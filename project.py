import psycopg2
from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Project, Task, Enrollment
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Connect to Database and create database session

engine = create_engine('postgresql://grader:grader@localhost:5432/garageproject')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/projects')
def index():
    projects = session.query(Project).all()
    return render_template('projects.html', projects=projects)


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# LinkedIn Auth
@app.route('/auth/linkedin', methods=['POST'])
def linkedInAuth():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    data = json.loads(request.data)
    login_session['firstName'] = data['firstName']
    login_session['lastName'] = data['lastName']
    login_session['email'] = data['emailAddress']
    login_session['pictureUrl'] = data['pictureUrl']
    # This will be used if providers is expanded to mor ethan just linkedin
    login_session['authProvider'] = "linkedin"

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return 'I got you logged in bruh!'


# logout
@app.route('/disconnect')
def disconnect():
    if 'email' in login_session:
        del login_session['firstName']
        del login_session['lastName']
        del login_session['email']
        del login_session['pictureUrl']
        del login_session['authProvider']
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


# create Project if logged in
@app.route('/createProject', methods=['POST', 'GET'])
def createProject():
    if not isLoggedIn(login_session):
        return redirect('login')

    if request.method == 'POST':
        user_id = getUserID(login_session['email'])
        new_project = Project(name=request.form['name'],
                              description=request.form['description'],
                              link=request.form['link'],
                              creator_id=user_id)
        session.add(new_project)
        session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('createProject.html')


# create task for a project
@app.route('/projects/<int:projectId>/createTask', methods=['POST', 'GET'])
def createTask(projectId):
    if not isLoggedIn(login_session):
        return redirect('login')

    project = session.query(Project).filter_by(id=projectId).one()

    if request.method == 'POST':
        user_id = getUserID(login_session['email'])
        t_name = "Untitled"
        t_description = "No Information"
        if request.form['name']:
            t_name = request.form['name']
        if request.form['description']:
            t_description = request.form['description']

        new_task = Task(name=t_name,
                        description=t_description,
                        creator_id=user_id,
                        project_id=request.form['project_id'])
        session.add(new_task)
        session.commit()
        return redirect(url_for('viewProject',
                        projectId=request.form['project_id']))
    else:
        return render_template('createTask.html', p=project)


# view single project
@app.route('/projects/<int:projectId>')
def viewProject(projectId):
    user_id = 0
    if isLoggedIn(login_session):
        user_id = getUserID(login_session['email'])

    project = session.query(Project).filter_by(id=projectId).one()
    tasks = session.query(Task).filter_by(project_id=project.id).all()
    return render_template('project.html',
                           p=project,
                           user_id=user_id,
                           tasks=tasks)


# edit project if project creator
@app.route('/editProject/<int:projectId>', methods=['GET', 'POST'])
def editProject(projectId):

    if not isLoggedIn(login_session):
        return redirect('login')

    edited_project = session.query(Project).filter_by(id=projectId).one()
    user_id = getUserID(login_session['email'])

    if edited_project.creator_id != user_id:
        return redirect(url_for('viewProject', projectId=projectId))

    if request.method == 'POST':
        if request.form['name']:
            edited_project.name = request.form['name']
        if request.form['description']:
            edited_project.description = request.form['description']
        session.add(edited_project)
        session.commit()
        return redirect(url_for('viewProject', projectId=edited_project.id))

    else:
        return render_template('editProject.html', p=edited_project)


# Show confirm delete project page
@app.route('/confirmDeleteProject/<int:projectId>')
def confirmDeleteProject(projectId):

    if not isLoggedIn(login_session):
        return redirect('login')

    user_id = getUserID(login_session['email'])
    project = session.query(Project).filter_by(id=projectId).one()

    if project.creator_id != user_id:
        return redirect(url_for('viewProject', projectId=projectId))

    if user_id == project.creator_id:
        return render_template('deleteProject.html', p=project)
    else:
        return redirect(url_for('viewProject', projectId=project.id))


# delete project from database
@app.route('/deleteProject/<int:projectId>', methods=["POST"])
def deleteProject(projectId):

    if not isLoggedIn(login_session):
        return redirect('login')

    user_id = getUserID(login_session['email'])
    project = session.query(Project).filter_by(id=projectId).one()
    tasks = session.query(Task).filter_by(project_id=project.id).all()

    if user_id == project.creator_id:
        session.delete(project)
        for task in tasks:
            session.delete(task)
        session.commit()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('viewProject', projectId=projectId))


# edit task if user is task creator or project creator
@app.route('/projects/<int:projectId>/editTask/<int:taskId>',
           methods=['GET', 'POST'])
def editTask(projectId, taskId):

    if not isLoggedIn(login_session):
        return redirect('login')

    project = session.query(Project).filter_by(id=projectId).one()
    edited_task = session.query(Task).filter_by(id=taskId).one()
    user_id = getUserID(login_session['email'])
    task_creator = edited_task.creator_id
    project_creator = project.creator_id

    if (user_id != task_creator) or (user_id != project_creator):
        return redirect(url_for('viewProject', projectId=project.id))

    if request.method == 'POST':
        if request.form['name']:
            edited_task.name = request.form['name']
        if request.form['description']:
            edited_task.description = request.form['description']
        session.add(edited_task)
        session.commit()
        return redirect(url_for('viewProject', projectId=project.id))
    else:
        return render_template('editTask.html', t=edited_task, p=project)


# show confirm delete task page
@app.route('/confirmDeleteTask/<int:projectId>/<int:taskId>')
def confirmDeleteTask(projectId, taskId):

    if not isLoggedIn(login_session):
        return redirect('login')

    user_id = getUserID(login_session['email'])
    project = session.query(Project).filter_by(id=projectId).one()
    task = session.query(Task).filter_by(id=taskId).one()

    # if user trying to delete is the creator of the task or project
    if (user_id == project.creator_id) or (user_id == task.creator_id):
        return render_template('deleteTask.html', p=project, t=task)
    else:
        return redirect(url_for('viewProject', projectId=project.id))


# delete task from database
@app.route('/deleteTask/<int:projectId>/<int:taskId>', methods=["POST"])
def deleteTask(projectId, taskId):

    if not isLoggedIn(login_session):
        return redirect('login')

    user_id = getUserID(login_session['email'])
    project = session.query(Project).filter_by(id=projectId).one()
    task = session.query(Task).filter_by(id=taskId).one()

    # if user trying to delete is the creator of the task or project
    if (user_id == project.creator_id) or (user_id == task.creator_id):
        session.delete(task)
        session.commit()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('viewProject', projectId=project.id))


# JSON Endpoints
@app.route('/api/projects')
def getProjects():
    projects = session.query(Project).all()
    return jsonify(projects=[p.serialize for p in projects])


@app.route('/api/project-task/<int:projectId>')
def getProjectTasks(projectId):
    project = session.query(Project).filter_by(id=projectId).one()
    tasks = session.query(Task).filter_by(project_id=projectId).all()
    return jsonify(project=project.serialize,
                   tasks=[t.serialize for t in tasks])


# User Helper Functions
def createUser(login_session):
    # Bio and title are empty for now until profiles are added
    newUser = User(first_name=login_session['firstName'],
                   last_name=login_session['lastName'],
                   email=login_session['email'],
                   picture=login_session['pictureUrl'],
                   title='', bio='')
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        print "Found User"
        return user.id
    except:
        print "Did not find user"
        return None


def isLoggedIn(login_session):
    if 'email' not in login_session:
        return False
    else:
        return True


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run()
