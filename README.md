#Garage Project
Garage Project is a web application intended for the internal use of an organization, company,
 or team to create share ideas of passion projects that team members might wish to collaborate
 on to either learn new skills, keep enthusiasm burning for their profession, or get create 
 examples of new ideas their company or organization might wish to explore.

##Current features
As of now users can log in using LinkedIn OAuth2, create Projects and assign tasks to this project. 
The creator of the project or of the task may delete or update the task.

##To Dos
In the next updates, users will only be logged into the app if their LinkedIn profile declare that they are
a current employee of the company. Users will be able to enroll in projects and specific tasks and view their 
enrollments on their own user hub. Categorization is the next step afterwards.

##Installation
Before running make sure all the dependencies are installed globally on your machine. These include Python,
Flack, SQLite, SQLAlchemy. To be certain that all dependencies are installed check what the project imports by 
looking at the top of the -project.py file.

After all packages are installed you will need to setup the database schema. I your console run 
 ---python database_setup.py

Now you can run the webserver to launch the application. In your console run ---python project.py

You can now access your web application at ---localhost:5000
