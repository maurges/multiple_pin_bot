#!/usr/bin/env/python3

from typing import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from local_store import Storage
from enum import Enum

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Description: main handlers for telegram
"""


# decorator: curry first positional argument of function
def curry(func):
    def curried1(arg):
        def rest(*args, **kwargs):
            return func(arg, *args, **kwargs)
        return rest
    return curried1


def start(bot, update):
    update.message.reply_text("Hi!")

def help(bot, update):
    help_msg = """
Just pin a message and it will be added to the pinned list.
You can then remove a message just by pressing a button.

If something doesn't work, make sure the bot is administrator and has the right to pin messages.
If something doesn't work still, see https://github.com/d86leader/multiple_pin_bot/issues for help or questions.

I'm a bot, see my github in the link above. If you want to use this bot in your group, please set up your own copy. I'm currently running on {platform}.
    """.format(platform="Cavium ThunderX 88XX")
    update.message.reply_text(help_msg)

@curry
def error(logger, bot, update, err):
    logger.warning(f"Update '{update}' caused error: {err}")


@curry
def pinned(storage : Storage, bot, update):
    if update.message.from_user.is_bot:
        return

    chat_id = update.message.chat_id
    msg_info = storage.MessageInfo(update.message.pinned_message)

    # add pinned message for this chat
    storage.add(chat_id, msg_info)
    text, layout = gen_post(storage, chat_id)

    new_message = storage.did_user_message(chat_id) 
    has_editable = storage.has_message_id(chat_id)
    if new_message or not has_editable:
        # There recently was a user message, or there is no bot's pinned
        # message to edit. We need to send a new one
        sent_msg = bot.send_message(chat_id, text=text
                                   ,parse_mode="HTML"
                                   ,reply_markup=layout)
        sent_id = sent_msg.message_id

        # delete old pin message
        if has_editable:
            old_msg = storage.get_message_id(chat_id)
            bot.delete_message(chat_id, old_msg)

        # remember the message for future edits
        storage.set_message_id(chat_id, sent_id)
        bot.pin_chat_message(chat_id, sent_id, disable_notification=True)
    else:
        msg_id = storage.get_message_id(chat_id)
        bot.edit_message_text(
            chat_id       = chat_id
            ,message_id   = msg_id
            ,text         = text
            ,parse_mode   = "HTML"
            ,reply_markup = layout
            )
        # also repin bot's message
        bot.pin_chat_message(chat_id, msg_id, disable_notification=True)

@curry
def button_pressed(storage : Storage, bot, update):
    cb = update.callback_query
    chat_id = cb.message.chat_id

    if cb.data == UnpinAll:
        storage.clear(chat_id)
        cb.answer("")
    elif cb.data == KeepLast:
        storage.clear_keep_last(chat_id)
        cb.answer("")
    else:
        msg_id, msg_index = map(int, cb.data.split(':'))
        storage.remove(chat_id, msg_id, msg_index)
        cb.answer("")

    text, layout = gen_post(storage, chat_id)
    msg_id = storage.get_message_id(chat_id)

    bot.edit_message_text(
        chat_id       = chat_id
        ,message_id   = msg_id
        ,text         = text
        ,parse_mode   = "HTML"
        ,reply_markup = layout
        )

@curry
def message(storage : Storage, bot, update):
    if update.message and update.message.chat_id:
        chat_id = update.message.chat_id
        storage.user_message_added(chat_id)


# button actions in callback data
UnpinAll = "$$ALL"
KeepLast = "$$LAST"

# used in two handlers above
def gen_post(storage : Storage, chat_id : int) -> Tuple[str, InlineKeyboardMarkup]:
    if not storage.has(chat_id):
        text = "No pins"
        layout = InlineKeyboardMarkup([[]])
        return (text, layout)

    pins = storage.get(chat_id)
    text = "\n\n".join(map(str, pins))

    # generate buttons for pin control
    button_all = InlineKeyboardButton("Unpin all"
                                     ,callback_data=UnpinAll)
    button_keep_last = InlineKeyboardButton("Keep last"
                                     ,callback_data=KeepLast)

    # special button case when only one pin:
    if len(pins) == 1:
        layout = [[button_all]]
        return (text, InlineKeyboardMarkup(layout))

    # first two rows: those buttons
    layout = [[button_all], [button_keep_last]]

    # other buttons: this style with message_id as data
    def on_button(msg, index) -> str:
        return f"{index + 1} {msg.icon}"
    def cb_data(msg, index) -> str:
        return f"{str(msg.m_id)}:{index}"

    it1 = zip(pins, range(len(pins)))
    it2 = zip(pins, range(len(pins)))
    texts = (on_button(msg, index) for msg, index in it1)
    cb_datas = (cb_data(msg, index) for msg, index in it2)

    buttons = [InlineKeyboardButton(text, callback_data=data)
                for text, data in zip(texts, cb_datas)]
    # split buttons by lines
    on_one_line = 5
    rows = [buttons[i:i+on_one_line] for i in range(0, len(buttons), on_one_line)]

    layout += rows

    return (text, InlineKeyboardMarkup(layout))
