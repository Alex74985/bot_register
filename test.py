from datetime import datetime, time, timedelta
from sqlalchemy import create_engine, Column, BigInteger, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


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


# Подключение к БД (замените на свои параметры)
DATABASE_URL = "postgresql+psycopg://alex:9999@localhost/bot_register"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def generate_timeslots():
    """Генерация временных слотов на неделю"""
    timeslots = []

    # Используем фиксированную дату для времени (например, 1970-01-01)
    base_date = datetime(1970, 1, 1)

    # Будние дни: понедельник-пятница (0-4), с 10:00 до 20:00
    for weekday in range(0, 5):  # 0=понедельник, 4=пятница
        current_time = datetime.combine(base_date.date(), time(10, 0))
        end_time = datetime.combine(base_date.date(), time(20, 30))  # включительно

        while current_time <= end_time:
            timeslots.append(
                WeekdayTimeslot(
                    weekday=weekday,
                    time=datetime(1970, 1, 1, current_time.hour, current_time.minute),
                )
            )
            current_time += timedelta(minutes=30)

    # Суббота (5): с 10:00 до 15:00
    weekday = 5  # суббота
    current_time = datetime.combine(base_date.date(), time(10, 0))
    end_time = datetime.combine(base_date.date(), time(15, 30))  # включительно

    while current_time <= end_time:
        timeslots.append(
            WeekdayTimeslot(
                weekday=weekday,
                time=datetime(1970, 1, 1, current_time.hour, current_time.minute),
            )
        )
        current_time += timedelta(minutes=30)

    # Воскресенье (6): с 17:00 до 20:00
    weekday = 6  # воскресенье
    current_time = datetime.combine(base_date.date(), time(17, 0))
    end_time = datetime.combine(base_date.date(), time(20, 30))  # включительно

    while current_time <= end_time:
        timeslots.append(
            WeekdayTimeslot(
                weekday=weekday,
                time=datetime(1970, 1, 1, current_time.hour, current_time.minute),
            )
        )
        current_time += timedelta(minutes=30)

    return timeslots


# Генерация и вставка данных
timeslots = generate_timeslots()
session.add_all(timeslots)
session.commit()
