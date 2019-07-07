#!/usr/bin/env python3

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3
"""

import handlers
import unittest
from typing import *
from random import randint
from telegram import Message
from datetime import datetime, timedelta
from local_store import Storage
from copy import copy


"""
Classes and functions for generating test data
"""

def rand_time(delta : int) -> datetime:
    seconds = randint(0, delta)
    return datetime.utcnow() - timedelta(seconds=seconds)

class HasId:
    def __init__(self, id : int) -> None:
        self.id = id
class HasIdName:
    def __init__(self, id : int, name : str) -> None:
        self.id = id
        self.first_name = name
        self.last_name = None
        self.is_bot = False

def gen_message() -> Message:
    m_id = randint(0, 1<<31)
    chat = HasId(randint(0, 1<<63))
    user = HasIdName(randint(0, 1<<63), "mcnamington")
    time = rand_time(10)
    return Message(m_id, user, time, chat, text="textitty")

def inc_msg_id(msg : Message, amount : int) -> Message:
    r = copy(msg)
    r.message_id += amount
    return r

def gen_same_chat_messages(amount : int) -> List[Message]:
    base_msg = gen_message()
    msgs = [inc_msg_id(base_msg, i) for i in range(amount)]
    return msgs

def gen_unpin_data(msg : Message) -> 'Update.CbQuery':
    data = str(msg.message_id)
    return Update.CbQuery(msg, data)


class Update:
    class CbQuery:
        def __init__(self, message : Message, data : str) -> None:
            self.message = message
            self.data = data
        def answer(self, s : str) -> None:
            pass

    def __init__(self, msg : Optional[Message]
                     , cb : Optional[CbQuery]) -> None:
        self.message = msg
        if msg:
            self.message.pinned_message = copy(msg)
        self.callback_query = cb

class Bot:
    def __init__(self):
        self.sent = []
        self.pinned = []
        self.edited = []

    def send_message(self, chat_id, text, reply_markup):
        self.sent += [{'chat_id' : chat_id
                      ,'text'    : text
                      ,'markup'  : reply_markup
                      }]
        return gen_message()
    def pin_chat_message(self, chat_id, m_id, disable_notification):
        self.pinned += [{'chat_id' : chat_id
                        ,'m_id'    : m_id
                        }]
    def edit_message_text(self, chat_id, message_id, text, reply_markup):
        self.edited += [{'chat_id' : chat_id
                        ,'msg_id'  : message_id
                        ,'text'    : text
                        ,'markup'  : reply_markup
                        }]


"""
Main testing classes
"""

class TestHandlers(unittest.TestCase):

    def test_pin_sends_and_edits(self):
        storage = Storage()
        bot = Bot()
        pin_handler = handlers.pinned(storage)

        message_amount = 5
        msgs = gen_same_chat_messages(message_amount)
        upds = [Update(msg, None) for msg in msgs]

        for update in upds:
            pin_handler(bot, update)

        self.assertEqual(len(bot.pinned), message_amount)
        self.assertEqual(len(bot.sent), 1)
        self.assertEqual(len(bot.edited), message_amount - 1)

    def test_user_message_resends(self):
        storage = Storage()
        bot = Bot()
        pin_handler = handlers.pinned(storage)
        message_handler = handlers.message(storage)

        message_amount = 5
        msgs = gen_same_chat_messages(message_amount)
        upds = [Update(msg, None) for msg in msgs]

        user_message = gen_message()
        user_message.chat.id = msgs[0].chat.id
        user_update = Update(user_message, None)

        for update in upds:
            pin_handler(bot, update)
            message_handler(bot, user_update)

        self.assertEqual(len(bot.pinned), message_amount)
        self.assertEqual(len(bot.sent), message_amount)
        self.assertEqual(len(bot.edited), 0)

    def test_handlers_store(self):
        storage = Storage()
        bot = Bot()
        pin_handler = handlers.pinned(storage)
        button_handler = handlers.button_pressed(storage)

        message_amount = 5
        msgs = gen_same_chat_messages(message_amount)
        msg_upds = [Update(msg, None) for msg in msgs]

        unpins = [gen_unpin_data(msg) for msg in msgs]
        unpin_upds = [Update(None, unpin) for unpin in unpins]

        chat_id = msgs[0].chat.id
        it = zip(msg_upds, unpin_upds, range(1, message_amount + 1))

        for pin_update, unpin_update, amount in it:
            pin_handler(bot, pin_update)
            self.assertEqual(len(storage._pin_data[chat_id]), amount)

            button_handler(bot, unpin_update)
            self.assertEqual(len(storage._pin_data[chat_id]), amount - 1)
            # test deleting non-existant
            button_handler(bot, unpin_update)
            self.assertEqual(len(storage._pin_data[chat_id]), amount - 1)

            #second add of deleted to keep amount increasing
            pin_handler(bot, pin_update)
            self.assertEqual(len(storage._pin_data[chat_id]), amount)

        unpin_all_cb = Update.CbQuery(msgs[0], handlers.UnpinAll)
        unpin_all_upd = Update(None, unpin_all_cb)
        button_handler(bot, unpin_all_upd)
        self.assertFalse(chat_id in storage._pin_data)

    def test_keep_last(self):
        storage = Storage()
        bot = Bot()
        pin_handler = handlers.pinned(storage)
        button_handler = handlers.button_pressed(storage)

        message_amount = 5
        msgs = gen_same_chat_messages(message_amount)
        upds = [Update(msg, None) for msg in msgs]
        chat_id = msgs[0].chat.id

        for update, amount in zip(upds, range(1, message_amount + 1)):
            pin_handler(bot, update)
            self.assertEqual(len(storage._pin_data[chat_id]), amount)

        keep_last_cb = Update.CbQuery(msgs[0], handlers.KeepLast)
        keep_last_upd = Update(None, keep_last_cb)
        button_handler(bot, keep_last_upd)

        self.assertTrue(chat_id in storage._pin_data)
        self.assertEqual(len(storage._pin_data[chat_id]), 1)
