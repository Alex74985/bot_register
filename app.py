import configparser
import telebot
from base import DataBase
from fsm import FSM


config = configparser.ConfigParser()
config.read("settings.ini")

bot_base = DataBase()
BOT_TOKEN = config["Telegramm"]["BOT_TOKEN"]

post_base = DataBase()
end_base = DataBase()
bot = telebot.TeleBot(BOT_TOKEN)
main_base = DataBase()
fsm_base = DataBase()
middleware_base = DataBase()
fsm = FSM(fsm_base)
