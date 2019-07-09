#!/usr/bin/env/python3

from typing import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from local_store import Storage
from enum import Enum
from control import parse_unpin_data
from control import UnpinAll, KeepLast, ButtonsExpand, ButtonsCollapse
from view import ButtonsStatus
import view

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
    if pin_from_self(storage, update):
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
    cb.answer("")
    chat_id = cb.message.chat_id

    # race check: do nothing if message already destroyed
    # FIXME it would be quite nice to have a mutex here btw
    # but if the race happens, it's no biggie: failing with error is the same
    # as doing nothing
    if not storage.has_message_id(chat_id):
        return
    msg_id = storage.get_message_id(chat_id)

    # default status of response buttons. May be changed in handling below
    response_buttons = ButtonsStatus.Collapsed
    if cb.data == UnpinAll:
        storage.clear(chat_id)
    elif cb.data == KeepLast:
        storage.clear_keep_last(chat_id)
    elif cb.data == ButtonsExpand:
        response_buttons = ButtonsStatus.Expanded
    elif cb.data == ButtonsCollapse:
        response_buttons = ButtonsStatus.Collapsed
    else:
        to_unpin_id, msg_index = parse_unpin_data(cb.data)
        storage.remove(chat_id, to_unpin_id, msg_index)
        response_buttons = ButtonsStatus.Expanded

    text, layout = gen_post(storage, chat_id, response_buttons)
    if (text, layout) == view.EmptyPost:
        bot.unpin_chat_message(chat_id, msg_id)
        bot.delete_message(chat_id, msg_id)
        storage.remove_message_id(chat_id)
        return

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


def gen_post(storage, chat_id : int
            ,button_status : ButtonsStatus = ButtonsStatus.Collapsed
            ) -> Tuple[str, InlineKeyboardMarkup]:
    if not storage.has(chat_id):
        return view.EmptyPost
    else:
        pins = storage.get(chat_id)
        return view.pins_post(pins, chat_id, button_status)


def pin_from_self(storage, update) -> bool:
    msg = update.message.pinned_message
    chat_id = msg.chat_id

    if not storage.has_message_id(chat_id):
        return False
    old_msg_id = storage.get_message_id(chat_id)
    if old_msg_id == msg.message_id:
        return True

    return False
