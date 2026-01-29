import os
import configparser
from sqlalchemy import (
    Column,
    DateTime,
    String,
    LargeBinary,
    Integer,
    BigInteger,
    Boolean,
)
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session


config = configparser.ConfigParser()
config.read("settings.ini", encoding="utf-8-sig")

engine = create_engine(config["SQLAchemy"]["SQLALCHEMY_DATABASE_URI"], echo=False)
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
    zone = Column(String)
    duration = Column(Integer)
    datetime = Column(DateTime)
    informed = Column(Boolean)
    cost = Column(String)

    def __init__(self, user_id, zone, duration, datetime, cost):
        self.user_id = user_id
        self.zone = zone
        self.duration = duration
        self.datetime = datetime
        self.cost = cost
        self.informed = False

    def __repr__(self):
        return f"<Register(id={self.id}, user_id={self.user_id}, zone={self.zone}, duration={self.duration}, datetime={self.datetime})>"

    def __str__(self):
        return f"Время={self.datetime}{os.linesep}Зона={self.zone}{os.linesep}Длительность={self.duration}{os.linesep}Запись от  "


class WeekdayTimeslot(Base):
    __tablename__ = "weekday_timeslots"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    weekday = Column(Integer)
    time = Column(DateTime)
    free = Column(Boolean)

    def __init__(self, weekday, time, free=True):
        self.weekday = weekday
        self.time = time
        self.free = free

    def __repr__(self):
        return f"<(Timeslot id={self.id}, weekday={self.weekday}, time={self.time.time()})>"


class State(Base):
    __tablename__ = "user_state"
    user_id = Column(BigInteger, primary_key=True)
    state = Column(String)
    arg = Column(LargeBinary)

    def __init__(self, user_id, state, arg):
        self.user_id = user_id
        self.state = state
        self.arg = arg

    def __repr__(self):
        return f"<State(user_id={self.user_id}, state={self.state}, arg={self.arg})>"
