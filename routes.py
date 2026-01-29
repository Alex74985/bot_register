import time
import configparser
import middleware
from middleware import check_admin, config
from app import main_base as base
from app import bot, fsm
import models
import keyboard_tool
from keyboard_tool import bot_text
from datetime import datetime, timedelta
import os


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
    if not base.test(models.User, user_id=message.chat.id):
        base.new(models.User, message.chat.id, message.from_user.username)
        bot.send_message(
            message.chat.id,
            bot_text["info"]["welcome_text"],
            reply_markup=keyboard_tool.get_menu_keyboard(),
        )
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы")


@bot.message_handler(commands=["nastya"])
@check_admin
def give_menu(message):
    keyboard = keyboard_tool.create_inlineKeyboard(
        bot_text["admin_panel"]["buttons"], 1
    )
    bot.send_message(
        message.chat.id,
        bot_text["admin_panel"]["start_text"],
        reply_markup=keyboard,
    )
    if base.test(models.State, user_id=message.chat.id):
        base.delete(models.State, user_id=message.chat.id)


@bot.callback_query_handler(lambda call: call.data == "get_regs")
@check_admin
def give_regs(call):
    buttons = bot_text["admin_panel"]["regs_optional_buttons"]
    bot.edit_message_text(
        bot_text["admin_panel"]["regs_optional_text"],
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard_tool.add_back(
            keyboard_tool.create_inlineKeyboard(buttons, 1)
        ),
    )
    fsm.set_state(call.message.chat.id, "admin watch regs")


@bot.callback_query_handler(lambda call: call.data == "on_date")
@check_admin
def _chose_date(call):
    datas = middleware.get_datas()
    buttons = {el: el for el in datas}
    bot.edit_message_text(
        bot_text["admin_panel"]["regs_optional_text"],
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard_tool.create_dateKeyboard(buttons),
    )
    fsm.set_state(call.message.chat.id, "admin pick reg date")


@bot.callback_query_handler(lambda call: call.data == "first")
@check_admin
def _first_reg(call):
    res = middleware.get_first_reg()
    bot.send_message(
        call.message.chat.id, str(res) + f"`{res.user_id}`", parse_mode="markdown"
    )


@bot.callback_query_handler(lambda call: call.data == "list")
@check_admin
def _all_reg(call):
    bot.send_message(
        call.message.chat.id,
        f"{os.linesep}---{os.linesep}".join(
            [str(el) + f"`{el.user_id}`" for el in middleware.get_all_regs()]
        ),
        parse_mode="markdown",
    )


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "admin pick reg date"
)
@check_admin
def _give_regs_on_date(call):
    date = datetime.strptime(call.data, "%d-%m-%y")
    regs = middleware.get_regs_on_date(date)
    if regs:
        bot.send_message(
            call.message.chat.id,
            f"{call.data}{os.linesep}{f'{os.linesep}---{os.linesep}'.join([str(el) + f'`{el.user_id}`' for el in regs])}",
            parse_mode="markdown",
        )
    else:
        bot.send_message(
            call.message.chat.id,
            f"{call.data}{os.linesep}{bot_text['admin_panel']['no_regs']}",
        )


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0]
    in ["admin watch regs", "admin pick option", "wait id"]
    and call.data == "_back"
)
def back_to_menu(call):
    keyboard = keyboard_tool.create_inlineKeyboard(
        bot_text["admin_panel"]["buttons"], 1
    )
    bot.edit_message_text(
        f"{bot_text['admin_panel']['start_text']}",
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard,
    )
    base.delete(models.State, user_id=call.message.chat.id)


@bot.callback_query_handler(lambda call: call.data == "change_shedule")
@check_admin
def give_choise(call):
    bot.edit_message_text(
        f"{bot_text['admin_panel']['choose_option']}",
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard_tool.add_back(
            keyboard_tool.create_inlineKeyboard(
                {
                    bot_text["admin_panel"]["add_ts_text"]: "_add",
                    bot_text["admin_panel"]["delete_ts_text"]: "_delete",
                }
            )
        ),
    )
    fsm.set_state(
        call.message.chat.id,
        "admin pick option",
    )


@bot.callback_query_handler(
    lambda call: call.data == "_back"
    and fsm.get_state(call.message.chat.id)[0] == "admin pick shedule day"
)
@check_admin
def back_to_choise(call):
    prev_args = fsm.get_state(call.message.chat.id)[1]
    fsm.set_state(
        call.message.chat.id,
        "admin pick option",
        **prev_args,
    )
    give_choise(call)


@bot.callback_query_handler(
    lambda call: call.data in ["_delete", "_add"]
    and fsm.get_state(call.message.chat.id)[0] == "admin pick option"
)
@check_admin
def give_shedule(call):
    datas = middleware.get_datas()
    buttons = {el: el for el in datas}
    bot.edit_message_text(
        f"{bot_text['admin_panel']['shedule_date_text']}",
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
    prev_args["date_pull"] = [el.strftime("%d-%m-%y") for el in datas]
    prev_args["option"] = call.data
    fsm.set_state(call.message.chat.id, "admin pick shedule day", **prev_args)


@bot.callback_query_handler(
    lambda call: call.data == "_back"
    and fsm.get_state(call.message.chat.id)[0] == "admin pick time"
)
@check_admin
def back_to_shedule(call):
    prev_args = fsm.get_state(call.message.chat.id)[1]
    prev_args["timeslots"] = []
    give_shedule(call)


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "admin pick time"
    and call.data in ["next_day", "prev_day"]
)
def adjacent_day_shedule(call):
    permanent = fsm.get_state(call.message.chat.id)[1]["permanent"]
    text = (
        bot_text["admin_panel"]["ts_to_delete"]
        if fsm.get_state(call.message.chat.id)[1]["option"] == "_delete"
        else bot_text["admin_panel"]["ts_to_append"]
    )
    prev_args = fsm.get_state(call.message.chat.id)[1]
    if permanent:
        if call.data == "next_day":
            date_f = (
                int(prev_args["weekday"]) + 1 if int(prev_args["weekday"]) < 6 else 0
            )
        else:
            date_f = (
                int(prev_args["weekday"]) - 1 if int(prev_args["weekday"]) > 0 else 6
            )
        ts = base.select_permanent(models.WeekdayTimeslot, date_f)
        timeslots = [el.time.strftime("%H:%M") for el in ts]
    else:
        date = fsm.get_state(call.message.chat.id)[1]["datetime"]
        date = date - timedelta(days=1)
        date_f = date.strftime("%d-%m-%y")
        timeslots = middleware.get_timeslots(date, 0)
        prev_args["datetime"] = date
    buttons = {key: key for key in timeslots}
    prev_args["timeslots"] = timeslots
    weekday = int(prev_args["weekday"])
    if call.data == "next_day":
        prev_args["weekday"] = weekday + 1 if weekday < 6 else 0
    else:
        prev_args["weekday"] = weekday - 1 if weekday > 0 else 6
    if buttons:
        bot.edit_message_text(
            f"{text}{os.linesep}{date_f}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.add_apply_decline(
                keyboard_tool.create_timeKeybard(buttons)
            ),
        )
    else:
        bot.edit_message_text(
            f"{bot_text['reg']['no_timeslots_text']} {date_f}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        datas = middleware.get_datas()
        buttons = {el: el for el in datas}
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.create_dateKeyboard(buttons),
        )
        prev_args = fsm.get_state(call.message.chat.id)[1]
        fsm.set_state(call.message.chat.id, "admin pick shedule day", **prev_args)
        return
    fsm.set_state(
        call.message.chat.id,
        "admin pick time",
        **prev_args,
    )


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "admin pick shedule day"
    and call.data in ["0", "1", "2", "3", "4", "5", "6"]
)
@check_admin
def give_permanent_timeslots(call):
    ts = base.select_permanent(models.WeekdayTimeslot, int(call.data))
    text = (
        bot_text["admin_panel"]["ts_to_delete"]
        if fsm.get_state(call.message.chat.id)[1]["option"] == "_delete"
        else bot_text["admin_panel"]["ts_to_append"]
    )
    timeslots = [el.time.strftime("%H:%M") for el in ts]
    buttons = {key: key for key in timeslots}
    if buttons:
        bot.edit_message_text(
            f"{text}{os.linesep}{call.data}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.add_apply_decline(
                keyboard_tool.create_timeKeybard(buttons)
            ),
        )
    else:
        bot.edit_message_text(
            f"{bot_text['reg']['no_timeslots_text']} {call.data}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        datas = middleware.get_datas()
        buttons = {el: el for el in datas}
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.create_dateKeyboard(buttons),
        )
        return
    prev_args = fsm.get_state(call.message.chat.id)[1]
    prev_args["timeslots"] = timeslots
    prev_args["weekday"] = int(call.data)
    prev_args["permanent"] = True
    fsm.set_state(
        call.message.chat.id,
        "admin pick time",
        **prev_args,
    )


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "admin pick shedule day"
    and call.data in fsm.get_state(call.message.chat.id)[1]["date_pull"]
)
@check_admin
def give_timeslots(call):
    date = datetime.strptime(call.data, "%d-%m-%y")
    timeslots = middleware.get_timeslots(date, 0)
    buttons = {el: el for el in timeslots}
    text = (
        bot_text["admin_panel"]["ts_to_delete"]
        if fsm.get_state(call.message.chat.id)[1]["option"] == "_delete"
        else bot_text["admin_panel"]["ts_to_append"]
    )
    if buttons:
        bot.edit_message_text(
            f"{text}{os.linesep}{call.data}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.add_apply_decline(
                keyboard_tool.create_timeKeybard(buttons)
            ),
        )
    else:
        bot.edit_message_text(
            f"{bot_text['reg']['no_timeslots_text']} {call.data}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        datas = middleware.get_datas()
        buttons = {el: el for el in datas}
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.create_dateKeyboard(buttons),
        )
        return
    prev_args = fsm.get_state(call.message.chat.id)[1]
    prev_args["datetime"] = date
    prev_args["timeslots"] = timeslots
    prev_args["weekday"] = date.weekday()
    prev_args["permanent"] = False
    fsm.set_state(
        call.message.chat.id,
        "admin pick time",
        **prev_args,
    )


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "admin pick time"
    and call.data in fsm.get_state(call.message.chat.id)[1]["timeslots"]
)
@check_admin
def write_chosen(call):
    prev_args = fsm.get_state(call.message.chat.id)[1]
    if call.data not in prev_args["timeslots"]:
        bot.send_message(call.message.chat.id, bot_text["reg"]["error"])
        return
    if "timeslots_to_change" in prev_args:
        prev_args["timeslots_to_change"].append(call.data)
    else:
        prev_args["timeslots_to_change"] = [call.data]
    fsm.set_state(
        call.message.chat.id,
        "admin pick time",
        **prev_args,
    )


@bot.message_handler(
    func=lambda message: fsm.get_state(message.chat.id)[0] == "admin pick time"
    and message.text not in fsm.get_state(message.chat.id)[1]["timeslots"]
)
def write_entered(message):
    prev_args = fsm.get_state(message.chat.id)[1]
    if "timeslots_to_change" in prev_args:
        prev_args["timeslots_to_change"].append(message.text)
    else:
        prev_args["timeslots_to_change"] = [message.text]
    fsm.set_state(
        message.chat.id,
        "admin pick time",
        **prev_args,
    )


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "admin pick time"
    and call.data == "_submit"
)
@check_admin
def save_chosen(call):
    ts = fsm.get_state(call.message.chat.id)[1]["timeslots_to_change"]
    permanent = fsm.get_state(call.message.chat.id)[1]["permanent"]
    wd = fsm.get_state(call.message.chat.id)[1]["weekday"]
    if permanent:
        picked_date = datetime.strptime("1970-01-01", "%Y-%m-%d").date()
    else:
        picked_date = fsm.get_state(call.message.chat.id)[1]["datetime"].date()
    picked_option = fsm.get_state(call.message.chat.id)[1]["option"]
    for el in ts:
        dt = datetime.combine(picked_date, datetime.strptime(el, "%H:%M").time())
        print(dt)
        if picked_option == "_delete":
            if not permanent:
                if not base.test(models.WeekdayTimeslot, time=dt, weekday=wd):
                    base.new(models.WeekdayTimeslot, wd, dt, False)
                else:
                    base.update(
                        models.WeekdayTimeslot,
                        {"free": False},
                        weekday=wd,
                        time=dt,
                    )
            else:
                if base.test(models.WeekdayTimeslot, time=dt, weekday=wd):
                    print("Find")
                    base.delete(models.WeekdayTimeslot, time=dt, weekday=wd)
        if picked_option == "_add":
            if not permanent:
                if not base.test(models.WeekdayTimeslot, time=dt, weekday=wd):
                    base.new(models.WeekdayTimeslot, wd, dt, True)
                else:
                    base.update(
                        models.WeekdayTimeslot,
                        {"free": True},
                        weekday=wd,
                        time=dt,
                    )
            else:
                if not base.test(models.WeekdayTimeslot, time=dt, weekday=wd):
                    base.new(models.WeekdayTimeslot, wd, dt, True)
    callback_text = (
        bot_text["admin_panel"]["_delete_ts_test"]
        if picked_option == "_delete"
        else bot_text["admin_panel"]["_add_ts_test"]
    )
    bot.answer_callback_query(
        callback_query_id=call.id,
        show_alert=True,
        text=f"{callback_text} {picked_date}{os.linesep}{f'{os.linesep}'.join(ts)}",
    )
    bot.delete_message(call.message.chat.id, call.message.message_id)
    base.delete(models.State, user_id=call.message.chat.id)


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "admin pick time"
    and call.data == "_decline"
)
def cancel_choosen(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    base.delete(models.State, user_id=call.message.chat.id)


@bot.callback_query_handler(lambda call: call.data == "get_stat")
@check_admin
def ask_id(call):
    bot.send_message(
        call.message.chat.id,
        bot_text["admin_panel"]["enter_id_text"],
        reply_markup=keyboard_tool.create_inlineKeyboard({"Отмена": "admin cancel"}),
    )
    fsm.set_state(call.message.chat.id, "wait id")


@bot.message_handler(
    func=lambda message: True and fsm.get_state(message.chat.id)[0] == "wait id"
)
@check_admin
def give_stat(message):
    try:
        res = middleware.get_stat(int(message.text))
        if not res:
            bot.send_message(message.chat.id, "Не удалось собрать статистику")
        else:
            text = f"Активные записи:{os.linesep}{f'{os.linesep}---{os.linesep}'.join([str(el) + f'`{el.user_id}`' for el in res[0]])}\\nПрошедшие записи:{os.linesep}{f'{os.linesep}---{os.linesep}'.join([str(el) + f'`{el.user_id}`' for el in res[1]])}{os.linesep}---\\nВыплаченная сумма: {res[2]}\\nusername - {res[3]}"
            bot.send_message(message.chat.id, text, parse_mode="markdown")
    except:
        base.delete(models.State, user_id=message.chat.id)


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "wait id"
)
@check_admin
def cancel_waiting(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    base.delete(models.State, user_id=call.message.chat.id)


@bot.message_handler(
    func=lambda message: True and message.text == bot_text["info"]["menu_buttons"][1]
)
def my_registrations(message):
    text, keyboard = middleware.my_registration_info(message.chat.id)
    bot.send_message(message.chat.id, text, reply_markup=keyboard)
    fsm.set_state(message.chat.id, "my_regs", number=0)


@bot.callback_query_handler(func=lambda call: True and call.data == "cancel")
def cancel_this_reg(call):
    try:
        number = int(fsm.get_state(call.message.chat.id)[1]["number"])
        tmp, keyboard = middleware.my_registration_info(
            call.message.chat.id, row=number
        )
        keyboard = keyboard_tool.create_answerKeyboard()
        bot.send_message(
            call.message.chat.id,
            "Вы уверены что хотите удалить запись?",
            reply_markup=keyboard,
        )
    except:
        base.delete(models.State, user_id=call.message.chat.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(
    lambda call: call.data == "yes"
    and fsm.get_state(call.message.chat.id)[0] == "my_regs"
)
def delete_reg(call):
    reg_id = int(fsm.get_state(call.message.chat.id)[1]["number"])
    middleware.drop_registration(call.message.chat.id, reg_id)
    bot.answer_callback_query(
        callback_query_id=call.id,
        show_alert=True,
        text=bot_text["my_reg"]["deleted"],
    )
    bot.delete_message(call.message.chat.id, call.message.message_id)
    base.delete(models.State, user_id=call.message.chat.id)


@bot.callback_query_handler(
    lambda call: call.data == "no"
    and fsm.get_state(call.message.chat.id)[0] == "my_regs"
)
def back_to_regs(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: True and call.data == "next")
def next_reg(call):
    try:
        number = int(fsm.get_state(call.message.chat.id)[1]["number"]) + 1
        tmp, keyboard = middleware.my_registration_info(
            call.message.chat.id, row=number
        )
        if tmp == "last":
            bot.answer_callback_query(
                callback_query_id=call.id,
                show_alert=True,
                text=bot_text["my_reg"]["last"],
            )
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, tmp, reply_markup=keyboard)
        fsm.set_state(call.message.chat.id, "my_regs", number=number)
    except:
        base.delete(models.State, user_id=call.message.chat.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: True and call.data == "back")
def prev_reg(call):
    try:
        number = int(fsm.get_state(call.message.chat.id)[1]["number"]) - 1
        tmp, keyboard = middleware.my_registration_info(
            call.message.chat.id, row=number
        )
        if tmp == "first":
            bot.answer_callback_query(
                callback_query_id=call.id,
                show_alert=True,
                text=bot_text["my_reg"]["first"],
            )
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, tmp, reply_markup=keyboard)
        fsm.set_state(call.message.chat.id, "my_regs", number=number)
    except:
        base.delete(models.State, user_id=call.message.chat.id)
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
            3,
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
        reply_markup=keyboard_tool.add_back(
            keyboard_tool.create_inlineKeyboard(buttons, 1)
        ),
    )
    fsm.set_state(
        call.message.chat.id,
        "pick duration",
        zone=call.data,
        duration_pull=[str(el) for el in buttons.values()],
    )


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "pick duration"
    and call.data == "_back"
)
def back_to_zone(call):
    buttons = {el: el for el in bot_text["reg"]["zone_buttons"]}
    bot.edit_message_text(
        bot_text["reg"]["zone"],
        call.message.chat.id,
        call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard_tool.create_inlineKeyboard(
            buttons,
            3,
        ),
    )
    fsm.set_state(call.message.chat.id, "pick zone")


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
    prev_args["duration"] = int(call.data.split(" - ")[0].split()[0])
    prev_args["cost"] = call.data.split(" - ")[1]
    prev_args["date_pull"] = [el.strftime("%d-%m-%y") for el in datas]
    fsm.set_state(
        call.message.chat.id,
        "pick date",
        **prev_args,
    )


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "pick date"
    and call.data == "_back"
)
def back_to_duration(call):
    zone = fsm.get_state(call.message.chat.id)[1]["zone"]
    if zone in ["ШВЗ", "Cпина", "Ноги"]:
        buttons = {
            "30 мин - 1000 ₽": "30 мин - 1000 ₽",
            "60 мин - 2000 ₽": "60 мин - 2000 ₽",
        }
    elif zone == "Все тело":
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
        reply_markup=keyboard_tool.add_back(
            keyboard_tool.create_inlineKeyboard(buttons, 1)
        ),
    )
    prev_args = fsm.get_state(call.message.chat.id)[1]
    fsm.set_state(
        call.message.chat.id,
        "pick duration",
        **prev_args,
    )


@bot.callback_query_handler(
    func=lambda call: fsm.get_state(call.message.chat.id)[0] == "pick date"
)
def choose_time(call):
    if call.data not in fsm.get_state(call.message.chat.id)[1]["date_pull"]:
        return
    reg_duration = fsm.get_state(call.message.chat.id)[1]["duration"]
    date = datetime.strptime(call.data, "%d-%m-%y")
    timeslots = middleware.get_timeslots(date, reg_duration)
    buttons = {el: el for el in timeslots}
    if buttons:
        bot.edit_message_text(
            f"{bot_text['reg']['start_time']}{os.linesep}{call.data}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.create_timeKeybard(buttons),
        )
    else:
        bot.edit_message_text(
            f"{bot_text['reg']['no_timeslots_text']} {call.data}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        datas = middleware.get_datas()
        buttons = {el: el for el in datas}
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.create_dateKeyboard(buttons),
        )
        prev_args = fsm.get_state(call.message.chat.id)[1]
        fsm.set_state(call.message.chat.id, "pick date", **prev_args)
        return
    prev_args = fsm.get_state(call.message.chat.id)[1]
    prev_args["datetime"] = datetime.strptime(call.data, "%d-%m-%y")
    prev_args["timeslots"] = timeslots
    fsm.set_state(
        call.message.chat.id,
        "pick time",
        **prev_args,
    )


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "pick time"
    and call.data == "_back"
)
def back_to_date(call):
    bot.edit_message_text(
        bot_text["reg"]["start_date"],
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    datas = middleware.get_datas()
    buttons = {el: el for el in datas}
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard_tool.create_dateKeyboard(buttons),
    )
    prev_args = fsm.get_state(call.message.chat.id)[1]
    fsm.set_state(call.message.chat.id, "pick date", **prev_args)


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "pick time"
    and call.data == "next_day"
)
def next_day_timeslots(call):
    reg_duration = fsm.get_state(call.message.chat.id)[1]["duration"]
    date = fsm.get_state(call.message.chat.id)[1]["datetime"]
    date = date + timedelta(days=1)
    date_f = date.strftime("%d-%m-%y")
    timeslots = middleware.get_timeslots(date, reg_duration)
    buttons = {el: el for el in timeslots}
    if buttons:
        bot.edit_message_text(
            f"{bot_text['reg']['start_time']}{os.linesep}{date_f}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.create_timeKeybard(buttons),
        )
    else:
        bot.edit_message_text(
            f"{bot_text['reg']['no_timeslots_text']} {date_f}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        datas = middleware.get_datas()
        buttons = {el: el for el in datas}
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.create_dateKeyboard(buttons),
        )
        prev_args = fsm.get_state(call.message.chat.id)[1]
        fsm.set_state(call.message.chat.id, "pick date", **prev_args)
        return
    prev_args = fsm.get_state(call.message.chat.id)[1]
    prev_args["datetime"] = date
    prev_args["timeslots"] = timeslots
    fsm.set_state(
        call.message.chat.id,
        "pick time",
        **prev_args,
    )


@bot.callback_query_handler(
    lambda call: fsm.get_state(call.message.chat.id)[0] == "pick time"
    and call.data == "prev_day"
)
def prev_day_timeslots(call):
    reg_duration = fsm.get_state(call.message.chat.id)[1]["duration"]
    date = fsm.get_state(call.message.chat.id)[1]["datetime"]
    date = date - timedelta(days=1)
    date_f = date.strftime("%d-%m-%y")
    timeslots = middleware.get_timeslots(date, reg_duration)
    buttons = {el: el for el in timeslots}
    if buttons:
        bot.edit_message_text(
            f"{bot_text['reg']['start_time']}{os.linesep}{date_f}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.create_timeKeybard(buttons),
        )
    else:
        bot.edit_message_text(
            f"{bot_text['reg']['no_timeslots_text']} {date_f}",
            call.message.chat.id,
            message_id=call.message.message_id,
        )
        datas = middleware.get_datas()
        buttons = {el: el for el in datas}
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            call.inline_message_id,
            reply_markup=keyboard_tool.create_dateKeyboard(buttons),
        )
        prev_args = fsm.get_state(call.message.chat.id)[1]
        fsm.set_state(call.message.chat.id, "pick date", **prev_args)
        return
    prev_args = fsm.get_state(call.message.chat.id)[1]
    prev_args["datetime"] = date
    prev_args["timeslots"] = timeslots
    fsm.set_state(
        call.message.chat.id,
        "pick time",
        **prev_args,
    )


@bot.callback_query_handler(
    func=lambda call: fsm.get_state(call.message.chat.id)[0] == "pick time"
    and call.data in fsm.get_state(call.message.chat.id)[1]["timeslots"]
)
def confirm_registration(call):
    if call.data not in fsm.get_state(call.message.chat.id)[1]["timeslots"]:
        bot.send_message(call.message.chat.id, bot_text["reg"]["error"])
        return
    data = fsm.get_state(call.message.chat.id)[1]
    bot.edit_message_text(
        f"{bot_text['my_reg']['your_reg']}{os.linesep}{bot_text['my_reg']['start_time_text']}{data['datetime'].date()} {call.data}{os.linesep}{bot_text['my_reg']['zone']}{data['zone']}{os.linesep}{bot_text['my_reg']['duration_time_text']}{data['duration']}{os.linesep}{bot_text['my_reg']['cost']} {data['cost']}",
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard_tool.add_back(
            keyboard_tool.create_inlineKeyboard(
                {
                    bot_text["reg"]["submit_reg"]: "confirm",
                    bot_text["reg"]["decline_reg"]: "decline",
                },
                2,
            )
        ),
    )
    prev_args = fsm.get_state(call.message.chat.id)[1]
    user_time = datetime.strptime(call.data, "%H:%M")
    user_datetime = data["datetime"].replace(
        hour=user_time.hour, minute=user_time.minute
    )
    prev_args["datetime"] = user_datetime
    fsm.set_state(call.message.chat.id, "confirm", **prev_args)


@bot.callback_query_handler(
    func=lambda call: fsm.get_state(call.message.chat.id)[0] == "confirm"
    and call.data == "_back"
)
def back_to_time(call):
    reg_duration = fsm.get_state(call.message.chat.id)[1]["duration"]
    date = fsm.get_state(call.message.chat.id)[1]["datetime"]
    date_f = date.strftime("%d-%m-%y")
    timeslots = middleware.get_timeslots(date, reg_duration)
    buttons = {el: el for el in timeslots}
    bot.edit_message_text(
        f"{bot_text['reg']['start_time']}{os.linesep}{date_f}",
        call.message.chat.id,
        message_id=call.message.message_id,
    )
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        call.inline_message_id,
        reply_markup=keyboard_tool.create_timeKeybard(buttons),
    )
    prev_args = fsm.get_state(call.message.chat.id)[1]
    fsm.set_state(call.message.chat.id, "pick time", **prev_args)


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

    bot.send_message(
        int(config["Telegramm"]["ADMIN_ID"]),
        f"{bot_text['admin_panel']['new_reg']}{os.linesep}{str(base.get_one(models.Register, datetime=data['datetime'], user_id=str(call.message.chat.id))) + f'`{call.message.chat.id}`'}",
        parse_mode="markdown",
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
