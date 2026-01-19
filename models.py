import os

from sqlalchemy import Column, Integer, String, LargeBinary, PickleType, BigInteger, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session


LINK = 'postgresql+psycopg2://postgres:12345@localhost/flask_db'

engine = create_engine(LINK, echo=False)
session = scoped_session(sessionmaker(bind=engine, autoflush=False))

Base = declarative_base()

class User(Base):
    __tablename__ = "bot_user"
    user_id = Column(BigInteger, primary_key=True)
    user_name = Column(String)

    def __init__(self, user_id, user_name):
        self.user_id = user_id
        self.user_name = user_name

    def __repr__(self):
        return f"User: {self.user_id}, user_name={self.user_name}"
    
class RegisterProgress(Base):
    __tablename__ = "register_progress"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(String)
    zona = Column(String)
    duration = Column(String)
    start_time = Column(String)

    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return f"<Register(id={self.id}, user_id={self.user_id}, zona={self.zona}, duration={self.duration}, start_time={self.start_time})>"
    

class Register(Base):
    __tablename__ = "register"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(String)
    zona = Column(String)
    duration = Column(String)
    start_time = Column(String)
    informed = Column(Boolean)

    def __init__(self, user_id, zona, duration, start_time):
        self.user_id = user_id
        self.zona = zona
        self.duration = duration
        self.start_time = start_time

    def __repr__(self):
        return f"<Register(id={self.id}, user_id={self.user_id}, zona={self.zona}, duration={self.duration}, start_time={self.start_time})>"


class State(Base):
    __tablename__ = 'user_state'
    user_id = Column(BigInteger, primary_key=True)
    state = Column(String)
    arg = Column(LargeBinary)

    def __init__(self, user_id, state, arg):
        self.user_id = user_id
        self.state = state
        self.arg = arg

    def __repr__(self):
        return f"<State(user_id={self.user_id}, state={self.state}, arg={self.arg})>"
