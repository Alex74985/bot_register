import os
import configparser
import time
import models
import keyboard_tool
import random
import threading
from app import middleware_base, bot, post_base
from datetime import datetime
from datetime import timedelta
from models import session
from sqlalchemy import and_
from app import middleware_base
from telebot.apihelper import ApiTelegramException


config = configparser.ConfigParser()
config.read("settings.ini")


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
    if row < 0:
        return "first"
    text = keyboard_tool.bot_text["my_reg"]
    active = middleware_base.select_regs_active(models.Register, user_id=str(user_id))
    expired = middleware_base.select_regs_expired(models.Register, user_id=str(user_id))
    all_registrations = expired + active
    if len(all_registrations) == 0:
        bot.send_message(user_id, text["no_reg"])
    elif row == len(all_registrations):
        return "last"
    try:
        registration_text = f"{text["your_reg"]}\n{text["start_time_text"]} {datetime.strftime(all_registrations[row].datetime, "%d-%m %H:%M")}\n{text["zone"]} {all_registrations[row].zone}\n{text["duration_time_text"]} {all_registrations[row].duration}\n{text["cost"]} {all_registrations[row].cost}"
        keyboard = keyboard_tool.create_inlineKeyboard(
            {text["back"]: "back", text["next"]: "next"}, 2
        )
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
                reg_time = r.datetime
                reg_time_f = datetime.strftime(reg_time, "%d-%m %H:%M")
                if post_time + timedelta(minutes=30) >= reg_time:
                    text = keyboard_tool.bot_text["my_reg"]
                    try:
                        bot.send_message(
                            config["Telegramm"]["ADMIN_ID"],
                            f"Запись через полчаса\n{text["start_time_text"]} {reg_time_f}\n{text["zone"]} {r.zone}\n{text["duration_time_text"]} {r.duration}\n{text["cost"]} {r.cost}",
                        )
                    except ApiTelegramException:
                        pass
                    bot.send_message(
                        r.user_id,
                        f"Напоминаю о записи через полчаса:\n{text["start_time_text"]} {reg_time_f}\n{text["zone"]} {r.zone}\n{text["duration_time_text"]} {r.duration}\n{text["cost"]} {r.cost}",
                    )

                    post_base.update(models.Register, {"informed": True}, id=r.id)
            time.sleep(5)

    rT = threading.Thread(target=timer)
    rT.start()


def get_datas():
    datas = [datetime.now() + timedelta(days=i) for i in range(30)]

    datas_f = [el.strftime("%d-%m") for el in datas]

    return datas


def get_timeslots(data: datetime, reg_duration: int):
    start_time = datetime.now() + timedelta(hours=2)
    end_time = datetime.now().replace(hour=20, minute=30, second=0, microsecond=0)
    if data != datetime.now().strftime("%d-%m-%y"):
        start_time = start_time.replace(
            day=datetime.strptime(data, "%d-%m-%y").day,
            hour=11,
            minute=0,
            second=0,
            microsecond=0,
        )
        end_time = end_time.replace(day=datetime.strptime(data, "%d-%m-%y").day)
    if start_time.minute == 0:
        rounded_time = start_time.replace(microsecond=0, second=0)
    elif start_time.minute < 30:
        rounded_time = start_time.replace(minute=30, second=0, microsecond=0)
    else:
        rounded_time = start_time.replace(
            hour=start_time.hour + 1, minute=0, second=0, microsecond=0
        )

    occupied_timeslots = post_base.select_occupied(
        models.Register, datetime.strptime(data, "%d-%m-%y").date()
    )
    timeslots_count = (end_time - rounded_time) // timedelta(minutes=30)
    timeslots = []
    for _ in range(timeslots_count):
        free = True
        for t in occupied_timeslots:
            t_start = t.datetime.time()
            t_end = (t.datetime + timedelta(minutes=t.duration)).time()
            if max(t_start, rounded_time.time()) <= min(
                t_end,
                (rounded_time + timedelta(minutes=reg_duration)).time(),
            ):
                free = False
        if free:
            timeslots.append(rounded_time)
        rounded_time += timedelta(minutes=30)

    timeslots_f = [el.strftime("%H:%M") for el in timeslots]
    print(timeslots_f)
    return timeslots_f
