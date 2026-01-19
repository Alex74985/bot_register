import time
import middleware
from app import main_base as base
import models
from app import bot, fsm
import keyboard_tool
from keyboard_tool import bot_text

def check_user(func):
    def decorator(message):
        user = base.test(models.User, id=message["from"]['id'])
        if user:
            return func(message)
        else:
            bot.send_message(message.chat.id, "Необходимо зарегестрироваться (/start)")
            return False
    return decorator


@bot.message_handler(commands=['start'])
def start(message):
    if base.test(models.User, id=message.chat.id) is False:
        base.new(models.User, message.chat.id)
        bot.send_message(message.chat.id, bot_text["info"]["welcome_text"], reply_markup=keyboard_tool.get_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы")


@bot.message_handler(func=lambda message: True and message.text == bot_text["info"]["menu_buttons"][1])
def my_registrations(message):
    middleware.my_registration_info(message.chat.id)
    fsm.set_state(message.chat.id, 'my_draws', number=0)


@bot.message_handler(func=lambda message: message.text == bot_text["info"]["menu_buttons"][0])
def choose_zone(message):
    bot.send_message(message.chat.id, bot_text["reg"]["zone"], reply_markup=keyboard_tool.create_inlineKeyboard(bot_text["reg"]["zone_buttons"], 4))
    fsm.set_state(message.chat.id, "pick zone")

@bot.message_handler(func=lambda message: fsm.get_state(message.chat.id)[0] == "pick zone")
def choose_duration(message):
    if message.data in ["ШВЗ", "Cпина", "Ноги"]:
        buttons = ["30мин 1000₽", "60 мин 2000₽"]
    elif message.data == "Все тело":
        buttons =  ["60 мин 2000₽", "90 мин 3000₽", "120 мин 4000₽"]
    else:
        bot.send_message(message.chat.id, bot_text["reg"]["error"])
        return
    bot.send_message(message.chat.id, bot_text["reg"]["duration"], reply_markup=keyboard_tool.create_inlineKeyboard(buttons, len(buttons)))
    fsm.set_state(message.chat.id, "pick duration", duration_pull=buttons)

@bot.message_handler(func=lambda message: fsm.get_state(message.chat.id)[0] == "pick duration")
def choose_date(message):
    if message.data not in fsm.get_state(message.chat.id):
        bot.send_message(message.chat.id, bot_text["reg"]["error"])
        return
    datas = 
    bot.send_message(message.chat.id, bot_text["reg"]["start_date"], reply_markup=keyboard_tool.create_inlineKeyboard())
