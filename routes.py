import time
import configparser
import middleware
from app import main_base as base
import models
from app import bot, fsm
import keyboard_tool
from keyboard_tool import bot_text
from datetime import datetime, timedelta


middleware.start_registration_timer()


def check_user(func):
    def decorator(message):
        user = base.test(models.User, user_id=message["from"]["id"])
        if user:
            return func(message)
        else:
            bot.send_message(message.chat.id, "Необходимо зарегестрироваться (/start)")
            return False

    return decorator


@bot.message_handler(commands=["start"])
def start(message):
    if base.test(models.User, user_id=message.chat.id) is False:
        base.new(models.User, message.chat.id, message.from_user.username)
        bot.send_message(
            message.chat.id,
            bot_text["info"]["welcome_text"],
            reply_markup=keyboard_tool.get_menu_keyboard(),
        )
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы")


@bot.message_handler(
    func=lambda message: True and message.text == bot_text["info"]["menu_buttons"][1]
)
def my_registrations(message):
    middleware.my_registration_info(message.chat.id)
    fsm.set_state(message.chat.id, "my_draws", number=0)


@bot.callback_query_handler(func=lambda call: True and call.data == "next")
def next_reg(call):
    try:
        number = int(fsm.get_state(call.message.chat.id)[1]["number"]) + 1
        tmp = middleware.my_registration_info(call.message.chat.id, row=number)
        if tmp == "last":
            bot.answer_callback_query(
                callback_query_id=call.id,
                show_alert=True,
                text=bot_text["my_reg"]["last"],
            )
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        fsm.set_state(call.message.chat.id, "my_regs", number=number)
    except:
        base.delete(models.State, user_id=call.mesage.chat.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: True and call.data == "back")
def prev_reg(call):
    try:
        number = int(fsm.get_state(call.message.chat.id)[1]["number"]) - 1
        tmp = middleware.my_registration_info(call.message.chat.id, row=number)
        if tmp == "first":
            bot.answer_callback_query(
                callback_query_id=call.id,
                show_alert=True,
                text=bot_text["my_reg"]["first"],
            )
            return

        bot.delete_message(call.message.chat.id, call.message.message_id)
        fsm.set_state(call.message.chat.id, "my_regs", number=number)
    except:
        base.delete(models.State, user_id=call.mesage.chat.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.message_handler(
    func=lambda message: message.text == bot_text["info"]["menu_buttons"][0]
)
def choose_zone(message):
    buttons = {el: el for el in bot_text["reg"]["zone_buttons"]}
    bot.send_message(
        message.chat.id,
        bot_text["reg"]["zone"],
        reply_markup=keyboard_tool.create_inlineKeyboard(
            buttons,
            4,
        ),
    )
    fsm.set_state(message.chat.id, "pick zone")


@bot.callback_query_handler(
    func=lambda call: fsm.get_state(call.message.chat.id)[0] == "pick zone"
)
def choose_duration(call):
    if call.data in ["ШВЗ", "Cпина", "Ноги"]:
        buttons = {
            "30 мин - 1000 ₽": "30 мин - 1000 ₽",
            "60 мин - 2000 ₽": "60 мин - 2000 ₽",
        }
    elif call.data == "Все тело":
        buttons = {
            "60 мин - 2000 ₽": "60 мин - 2000 ₽",
            "90 мин - 3000 ₽": "90 мин - 3000 ₽",
            "120 мин - 4000 ₽": "120 мин - 4000 ₽",
        }
    else:
        bot.send_message(call.message.chat.id, bot_text["reg"]["error"])
        return
    bot.edit_message_text(
        bot_text["reg"]["duration_time"],
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard_tool.create_inlineKeyboard(buttons),
    )
    fsm.set_state(
        call.message.chat.id,
        "pick duration",
        zone=call.data,
        duration_pull=[str(el) for el in buttons.values()],
    )


@bot.callback_query_handler(
    func=lambda call: fsm.get_state(call.message.chat.id)[0] == "pick duration"
)
def choose_date(call):
    if call.data not in fsm.get_state(call.message.chat.id)[1]["duration_pull"]:
        bot.send_message(call.message.chat.id, bot_text["reg"]["error"])
        return
    datas = middleware.get_datas()
    buttons = {el: el for el in datas}
    bot.edit_message_text(
        bot_text["reg"]["start_date"],
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard_tool.create_dateKeyboard(buttons),
    )
    prev_args = fsm.get_state(call.message.chat.id)[1]
    fsm.set_state(
        call.message.chat.id,
        "pick date",
        **prev_args,
        duration=call.data.split(" - ")[0],
        cost=call.data.split(" - ")[1],
        date_pull=[el.strftime("%d-%m-%y") for el in datas],
    )


@bot.callback_query_handler(
    func=lambda call: fsm.get_state(call.message.chat.id)[0] == "pick date"
)
def choose_time(call):
    if call.data not in fsm.get_state(call.message.chat.id)[1]["date_pull"]:
        return
    timeslots = middleware.get_timeslots(call.data)
    buttons = {el: el for el in timeslots}
    bot.edit_message_text(
        bot_text["reg"]["start_time"],
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard_tool.create_inlineKeyboard(buttons, 7),
    )
    prev_args = fsm.get_state(call.message.chat.id)[1]
    fsm.set_state(
        call.message.chat.id,
        "pick time",
        **prev_args,
        date=call.data,
        timeslots=timeslots,
    )


@bot.callback_query_handler(
    func=lambda call: fsm.get_state(call.message.chat.id)[0] == "pick time"
)
def confirm_registration(call):
    if call.data not in fsm.get_state(call.message.chat.id)[1]["timeslots"]:
        bot.send_message(call.message.chat.id, bot_text["reg"]["error"])
        return
    data = fsm.get_state(call.message.chat.id)[1]
    bot.edit_message_text(
        f"{bot_text["my_reg"]["your_reg"]}\n{bot_text["my_reg"]["start_time_text"]}{data["date"]} {call.data}\n{bot_text["my_reg"]["zone"]}{data["zone"]}\n{bot_text["my_reg"]["duration_time_text"]}{data["duration"]}\n{bot_text["my_reg"]["cost"]} {data["cost"]}",
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard_tool.create_inlineKeyboard(
            {
                bot_text["reg"]["submit_reg"]: "confirm",
                bot_text["reg"]["decline_reg"]: "decline",
            },
            2,
        ),
    )
    prev_args = fsm.get_state(call.message.chat.id)[1]
    user_time = datetime.strptime(call.data, "%H:%M")
    user_date = datetime.strptime(data["date"], "%d-%m-%y")
    user_datetime = user_time.replace(
        day=user_date.day, month=user_date.month, year=user_date.year
    )
    fsm.set_state(call.message.chat.id, "confirm", **prev_args, datetime=user_datetime)


@bot.callback_query_handler(
    func=lambda call: fsm.get_state(call.message.chat.id)[0] == "confirm"
    and call.data == "confirm"
)
def submit(call):
    data = fsm.get_state(call.message.chat.id)[1]
    base.new(
        models.Register,
        call.message.chat.id,
        data["zone"],
        data["duration"],
        data["datetime"],
        data["cost"],
    )
    base.delete(models.State, user_id=call.message.chat.id)

    bot.edit_message_reply_markup(
        call.message.chat.id, call.message.message_id, call.inline_message_id, None
    )

    bot.answer_callback_query(
        call.id, show_alert=True, text=bot_text["reg"]["submit_text"]
    )


@bot.callback_query_handler(
    func=lambda call: fsm.get_state(call.message.chat.id)[0] == "confirm"
    and call.data == "decline"
)
def decline(call):
    base.delete(models.State, user_id=call.message.chat.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(
        call.id, show_alert=True, text=bot_text["reg"]["decline_text"]
    )


print("routes")
bot.infinity_polling()
