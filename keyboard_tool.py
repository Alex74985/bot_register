import telebot
import json
from datetime import datetime


file = open("RU.json", encoding="utf-8")
bot_text = json.load(file)

russian_months = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}


def get_menu_keyboard():
    buttons = bot_text["info"]["menu_buttons"]
    menu_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_keyboard.row(buttons[0], buttons[1])

    return menu_keyboard


def get_registration_keyboard(user_id):
    buttons = bot_text["menu"]["registration_buttons"]
    registration_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    registration_keyboard.row(buttons[0], buttons[1])
    registration_keyboard.row(buttons[2], buttons[3])

    return registration_keyboard


def create_inlineKeyboard(key: dict, row=3):
    if not isinstance(list(key.values())[0], dict):
        key = {key: {"callback_data": key} for key in key}
    keyboard = telebot.util.quick_markup(key, row)
    return keyboard


def add_back(keyboard: telebot.types.InlineKeyboardMarkup):
    keyboard.add(
        telebot.types.InlineKeyboardButton(
            text=bot_text["reg"]["back"], callback_data="_back"
        )
    )

    return keyboard


def create_timeKeybard(key):
    key = {key: {"callback_data": key} for key in key}
    keyboard = telebot.util.quick_markup(key, 4)
    keyboard.add(
        telebot.types.InlineKeyboardButton(
            text=bot_text["reg"]["prev_timeslots_text"], callback_data="prev_day"
        ),
        telebot.types.InlineKeyboardButton(
            text=bot_text["reg"]["next_timeslots_text"], callback_data="next_day"
        ),
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton(
            text=bot_text["reg"]["back"], callback_data="_back"
        )
    )
    return keyboard


def create_dateKeyboard(d, month=None):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=7)
    key_list = []
    today = datetime.now()
    if month == None:
        month = today.month
    if today.month != 1:
        prev_m = f"{russian_months[today.month - 1]} {today.year}"
    else:
        prev_m = f"{russian_months[12]} {today.year - 1}"
    if today.month != 12:
        next_m = f"{russian_months[today.month + 1]} {today.year}"
    else:
        next_m = f"{russian_months[1]} {today.year + 1}"

    keyboard.add(
        telebot.types.InlineKeyboardButton(text=prev_m, callback_data=prev_m),
        telebot.types.InlineKeyboardButton(text=next_m, callback_data=next_m),
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton(text="Пн", callback_data="None"),
        telebot.types.InlineKeyboardButton(text="Вт", callback_data="None"),
        telebot.types.InlineKeyboardButton(text="Ср", callback_data="None"),
        telebot.types.InlineKeyboardButton(text="Чт", callback_data="None"),
        telebot.types.InlineKeyboardButton(text="Пт", callback_data="None"),
        telebot.types.InlineKeyboardButton(text="Сб", callback_data="None"),
        telebot.types.InlineKeyboardButton(text="Вс", callback_data="None"),
    )

    for _ in range(today.weekday()):
        key_list.append(
            telebot.types.InlineKeyboardButton(text=" ", callback_data="None")
        )

    def filter_days(date: datetime):
        if date.month == month:
            return True
        return False

    for key in filter(filter_days, list(d.keys())):
        text = key.strftime("%d")
        callback = key.strftime("%d-%m-%y")
        key_list.append(
            telebot.types.InlineKeyboardButton(text=text, callback_data=callback)
        )

    while len(key_list) % 7 != 0:
        key_list.append(
            telebot.types.InlineKeyboardButton(text=" ", callback_data="None")
        )

    keyboard.add(*key_list)

    keyboard.add(
        telebot.types.InlineKeyboardButton(
            text=bot_text["reg"]["back"], callback_data="_back"
        )
    )

    return keyboard
