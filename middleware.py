import os
import time
import models
import keyboard_tool
import random
import threading
from app import middleware_base, bot, post_base, end_base
from datetime import datetime
from datetime import timedelta
from models import session
from sqlalchemy import and_
from app import middleware_base


def check_user(user_id):
    user = middleware_base.get_one(models.User, user_id=str(user_id))
    if user != None:
        return user
    else:
        return False
    

def create_registration_progress(user_id):
    middleware_base.delete(models.RegisterProgress, user_id=str(user_id))
    middleware_base.new(models.RegisterProgress, str(user_id))
    middleware_base.delete(models.State, user_id=str(user_id))

    return registration_info(user_id)

def registration_info(user_id):
    tmp = check_registration(user_id)
    text = keyboard_tool.bot_text["registration"]
    return f"{text}"


def check_registration(user_id):
    return middleware_base.get_one(models.RegisterProgress, user_id=str(user_id))
    

def my_registration_info(user_id, row=0):
    text = keyboard_tool.bot_text["my_registration"]
    active = middleware_base.select_all(models.Register, user_id=str(user_id))
    expired = middleware_base.select_all(models.Register, user_id=str(user_id))
    all_registrations = active + expired
    if len(all_registrations) == 0:
        bot.send_message(user_id, text["no_registration"])
    

    try:
        registration_text = f"{text["your_registration"]}\n{text["start_time_text"]} {all_registrations[row].start_time}\n{text["zone"]} {all_registrations[row].zona}\n{text["duration_time_text"]} {all_registrations[row].duration}"
        keyboard = keyboard_tool.create_inlineKeyboard({text['back']: "back", text['next']: "next"}, 2)
        bot.send_message(user_id, registration_text, reply_markup=keyboard)
    except Exception as e:
        print(e)
        print(text)
        print(all_registrations)


def start_registration_timer():
    def timer():
        while 1:
            for r in post_base.select_all(models.Register, informed=False):
                post_time = datetime.now()
                if post_time >= datetime.strptime(r.start_time, '%Y-%m-%d %H:%M') + timedelta(minutes=30):
                    safed = False
                    text = keyboard_tool.bot_text["my_registration"]
                    bot.send_message(admin_id,  f"Запись через полчаса\n{text["start_time_text"]} {r.start_time}\n{text["zone"]} {r.zona}\n{text["duration_time_text"]} {r.duration}")
                    bot.send_message(r.user_id,  f"Напоминаю о записи через полчаса:\n{text["start_time_text"]} {r.start_time}\n{text["zone"]} {r.zona}\n{text["duration_time_text"]} {r.duration}")

                    post_base.update(models.Register, {"informed": True}, id=r.id)
            time.sleep(5)

    rT = threading.Thread(target=timer)
    rT.start()


def get_datas():
    datas = [datetime.now() + timedelta(days=i) for i in range(30)]

    datas_f = [el.strftime("%d-%m") for el in datas]

    return datas


def get_timeslots(data: datetime):
    start_time = datetime.now() + timedelta(hours=2)
    end_time = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)
    if data.strftime("%m-%d") != datetime.now().strftime("%m-d%"):
        start_time = start_time.replace(day=data.day, hour=10, minute=30, second=0, microsecond=0)
        end_time = end_time.replace(day=data.day)

    if start_time.minute < 30:
        rounded_time = start_time.replace(minute=30, second=0, microsecond=0)
    else:
        rounded_time = start_time.replace(hour=start_time.hour + 1, minute=0, second=0, microsecond=0)


    timeslots_count = (end_time - rounded_time) // timedelta(minutes=30)
    timeslots = [rounded_time]
    for _ in range(timeslots_count):
        timeslots.append(rounded_time + timedelta(minutes=30))
        rounded_time += timedelta(minutes=30)

    timeslots_f = [el.strftime("%H:%M") for el in timeslots]


    return timeslots

