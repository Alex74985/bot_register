import telebot
from base import DataBase
from fsm import FSM


bot_base = DataBase()
BOT_TOKEN = "8390969987:AAEE0A82IaxvJCay93FmFiKvlF061AWTyVU"

post_base = DataBase()
end_base = DataBase()
bot = telebot.TeleBot(BOT_TOKEN)
main_base = DataBase()
fsm_base = DataBase()
middleware_base = DataBase()
fsm = FSM(fsm_base)
