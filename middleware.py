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
from telebot.types import Message, CallbackQuery
import os


config = configparser.ConfigParser()
config.read("settings.ini")


def check_user(user_id):
    user = middleware_base.get_one(models.User, user_id=str(user_id))
    if user != None:
        return user
    else:
        return False


def check_admin(func):
    def decorator(in_data: Message | CallbackQuery):
        if isinstance(in_data, Message):
            if int(in_data.chat.id) == int(config["Telegramm"]["ADMIN_ID"]):
                return func(in_data)
        elif isinstance(in_data, CallbackQuery):
            if int(in_data.message.chat.id) == int(config["Telegramm"]["ADMIN_ID"]):
                return func(in_data)
        else:
            return False

    return decorator


def get_first_reg():
    regs = middleware_base.select_regs_active(models.Register)
    return regs[0]


def get_all_regs():
    regs = middleware_base.select_regs_active(models.Register)
    return regs


def get_regs_on_date(date: datetime):
    regs = middleware_base.select_occupied(models.Register, date)

    return regs


def get_stat(user_id):
    active_regs = middleware_base.select_regs_active(
        models.Register, user_id=str(user_id)
    )
    expired_regs = middleware_base.select_regs_expired(
        models.Register, user_id=str(user_id)
    )
    summ = sum([int(el.split()[0]) for el in [r.cost for r in expired_regs]])
    user = middleware_base.get_one(models.User, user_id=user_id)
    return active_regs, expired_regs, summ, f"@{user.user_name}"


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


def drop_registration(user_id, row):
    active = middleware_base.select_regs_active(models.Register, user_id=str(user_id))
    expired = middleware_base.select_regs_expired(models.Register, user_id=str(user_id))
    all_registrations = expired + active
    middleware_base.delete(models.Register, id=all_registrations[row].id)


def my_registration_info(user_id, row=0):
    if row < 0:
        return "first", None
    text = keyboard_tool.bot_text["my_reg"]
    active = middleware_base.select_regs_active(models.Register, user_id=str(user_id))
    expired = middleware_base.select_regs_expired(models.Register, user_id=str(user_id))
    all_registrations = active
    if len(all_registrations) == 0:
        return text["no_reg"], None
    elif row == len(all_registrations):
        return "last", None
    try:
        registration_text = f"{text['your_reg']}{os.linesep}{text['start_time_text']} {datetime.strftime(all_registrations[row].datetime, '%d-%m %H:%M')}{os.linesep}{text['zone']} {all_registrations[row].zone}{os.linesep}{text['duration_time_text']} {all_registrations[row].duration}{os.linesep}{text['cost']} {all_registrations[row].cost}"
        keyboard = keyboard_tool.create_inlineKeyboard(
            {text["back"]: "back", text["next"]: "next", text["cancel"]: "cancel"}, 2
        )
        return registration_text, keyboard
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
                    user_name = post_base.get_one(
                        models.User, user_id=r.user_id
                    ).user_name
                    try:
                        bot.send_message(
                            config["Telegramm"]["ADMIN_ID"],
                            f"Запись через полчаса{os.linesep}{str(r) + f'`{r.user_id}`{os.linesep}@{user_name}'}",
                            parse_mode="markdown",
                        )
                    except ApiTelegramException:
                        pass
                    bot.send_message(
                        r.user_id,
                        f"Напоминаю о записи через полчаса:{os.linesep}{text['start_time_text']} {reg_time_f}{os.linesep}{text['zone']} {r.zone}{os.linesep}{text['duration_time_text']} {r.duration}{os.linesep}{text['cost']} {r.cost}",
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
    permanent = middleware_base.select_permanent(
        models.WeekdayTimeslot, data.weekday(), free=True
    )
    temporary_free = middleware_base.select_temporary(
        models.WeekdayTimeslot, data.date(), free=True
    )

    temporary_ban = middleware_base.select_temporary(
        models.WeekdayTimeslot, data.date(), free=False
    )

    all_to_today = sorted(permanent + temporary_free, key=lambda el: el.time.time())

    if data.date() < datetime.now().date():
        return []

    occupied = post_base.select_occupied(models.Register, data.date())

    def _filter_data(s):
        if s.time.time() not in [sh.time.time() for sh in temporary_ban]:
            return True
        return False

    shedule = filter(_filter_data, all_to_today)

    def _filter_today(s):
        if data.date() != datetime.now().date():
            return True
        if s.time.time() < (datetime.now() + timedelta(minutes=120)).time():
            return False
        return True

    shedule = filter(_filter_today, shedule)

    timeslots = []
    for timeslot in shedule:
        free = True
        for o in occupied:
            o_start = o.datetime.time()
            o_end = (o.datetime + timedelta(minutes=o.duration)).time()
            if max(o_start, timeslot.time.time()) <= min(
                o_end,
                (timeslot.time + timedelta(minutes=reg_duration)).time(),
            ):
                free = False
        if free:
            timeslots.append(timeslot.time)

    timeslots_f = [el.strftime("%H:%M") for el in timeslots]
    return timeslots_f
