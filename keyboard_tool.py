import telebot
import json


file  = open("RU.json", encoding="utf-8")
bot_text  = json.load(file)

def get_menu_keyboard():
    buttons = bot_text["info"]["menu_buttons"]
    menu_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_keyboard.row(buttons)

    return menu_keyboard

def get_registration_keyboard(user_id):
    buttons = bot_text["menu"]["registration_buttons"]
    registration_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    registration_keyboard.row(buttons[0], buttons[1])
    registration_keyboard.row(buttons[2], buttons[3])

    return registration_keyboard

def create_inlineKeyboard(key, row=0):
    keyboard = telebot.types.InlineKeyboardMarkup()
    key_list = []
    count = 0
    for i in key:
        key_list.append(telebot.types.InlineKeyboardButton(
            text=i, callback_data=key.get(i)))
        count += 1

        if count >= row:
            keyboard.add(*[i for i in key_list])
            key_list = []
            count = 0
        if list(key.keys())[-1] == i:
            keyboard.add(*[i for i in key_list])
    return keyboard