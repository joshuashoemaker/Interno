import psycopg2
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Boolean, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    first_name = Column(String(80), nullable = False)
    last_name = Column(String(80), nullable = False)
    email = Column(String(200), nullable = False)
    picture = Column(String(250), nullable = True)
    title = Column(String(80), nullable = True)
    bio = Column(String(1000), nullable = True)

    @property
    def serialize(self):
        return{
            'first_name'    : self.first_name,
            'last_name'     : self.last_name,
            'email'         : self.email,
            'id'            : self.id,
            'picture'       : self.picture,
            'title'         : self.title,
            'bio'           : self.bio
        }


class Project(Base):
    __tablename__ = 'project'

    id = Column(Integer, primary_key = True)
    user = relationship(User)
    creator_id = Column(Integer, ForeignKey('user.id'))
    name = Column(String(80))
    description = Column(String(5000))
    link = Column(String(255))

    @property
    def serialize(self):
        return{
            'creator_id'    : self.creator_id,
            'name'          : self.name,
            'description'   : self.description,
            'link'          : self.link
        }

class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key = True)
    name = Column(String(80))
    description = Column(String(5000))
    project = relationship(Project)
    project_id = Column(Integer, ForeignKey('project.id'))
    user = relationship(User)
    creator_id = Column(Integer, ForeignKey('user.id'))

    @property
    def serialize(self):
        return{
            'name'          : self.name,
            'creator_id'    : self.creator_id,
            'project_id'    : self.creator_id,
            'description'   : self.description
        }

class Enrollment(Base):
    __tablename__ = 'enrollment'

    id = Column(Integer, primary_key = True)
    user = relationship(User)
    task = relationship(Task)
    user_id = Column(Integer, ForeignKey('user.id'))
    task_id = Column(Integer, ForeignKey('task.id'))

    @property
    def serialize(self):
        return{
            'id'            : self.id,
            'user_id'       : self.user_id,
            'task_id'       : self.task_id
        }



engine = create_engine('postgresql:///garageproject.db')
 

Base.metadata.create_all(engine)
