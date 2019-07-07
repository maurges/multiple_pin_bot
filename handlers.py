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
    update.message.reply_text("Start")

def help(bot, update):
    update.message.reply_text("Don't panic!")

@curry
def error(logger, bot, update, whatisthisparam):
    logger.warning(f"Update '{update}' caused error: {context.error}")


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
    no_editable = not storage.has_message_id(chat_id)
    if new_message or no_editable:
        # There recently was a user message, or there is no bot's pinned
        # message to edit. We need to send a new one
        sent_msg = bot.send_message(chat_id, text=text
                                   ,parse_mode="HTML"
                                   ,reply_markup=layout)
        sent_id = sent_msg.message_id
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
        msg_id = int(cb.data)
        storage.remove(chat_id, msg_id)
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
    # first two rows: those buttons
    layout = [[button_all], [button_keep_last]]

    # other buttons: this style with message_id as data
    def on_button(msg, index) -> str:
        return f"{index} {msg.icon}"
        #return f"{index} {msg.icon} {msg.sender}"

    texts = (on_button(msg, index + 1) for msg,index in zip(pins, range(len(pins))))
    cb_datas = (str(msg.m_id) for msg in pins)

    buttons = [InlineKeyboardButton(text, callback_data=data)
                for text, data in zip(texts, cb_datas)]
    # split buttons by lines
    on_one_line = 5
    rows = [buttons[i:i+on_one_line] for i in range(0, len(buttons), on_one_line)]

    layout += rows

    return (text, InlineKeyboardMarkup(layout))
