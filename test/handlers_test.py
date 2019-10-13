#!/usr/bin/env python3

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3
"""

import handlers
import unittest
import re
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

generated_number : int = 0
def gen_number() -> int:
    global generated_number
    generated_number += 1000
    return generated_number

def gen_message() -> Message:
    m_id = gen_number()
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
    data = str(msg.message_id) + ":0"
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
        self.deleted = []

    def send_message(self, chat_id, text, parse_mode, reply_markup):
        msg = gen_message()
        self.sent += [{'chat_id' : chat_id
                      ,'text'    : text
                      ,'markup'  : reply_markup
                      ,'m_id'    : msg.message_id
                      }]
        assert isinstance(text, str)
        return msg
    def unpin_chat_message(self, chat_id, m_id):
        self.pinned.remove({'chat_id' : chat_id
                           ,'m_id'    : m_id
                           })
    def pin_chat_message(self, chat_id, m_id, disable_notification):
        assert disable_notification == True
        self.pinned += [{'chat_id' : chat_id
                        ,'m_id'    : m_id
                        }]
    def edit_message_text(self, chat_id, message_id, text, parse_mode, reply_markup):
        # assert that editing existing message
        assert list(filter(lambda m: m["m_id"] == message_id, self.sent)) != []
        self.edited += [{'chat_id' : chat_id
                        ,'m_id'  : message_id
                        ,'text'    : text
                        ,'markup'  : reply_markup
                        }]
        assert isinstance(text, str)
    def delete_message(self, chat_id, message_id):
        # assert that editing existing message
        assert list(filter(lambda m: m["m_id"] == message_id, self.sent)) != []
        self.deleted += [{'chat_id' : chat_id
                         ,'m_id'  : message_id
                         }]

class Context:
    def __init__(self, bot : Bot) -> None:
        self.bot = bot

"""
Main testing classes
"""

class TestHandlers(unittest.TestCase):
    def get_storage(self):
        return Storage()

    def test_pin_sends_and_edits(self):
        storage = self.get_storage()
        bot = Bot()
        context = Context(bot)
        pin_handler = handlers.pinned(storage)

        message_amount = 5
        msgs = gen_same_chat_messages(message_amount)
        upds = [Update(msg, None) for msg in msgs]

        for update in upds:
            pin_handler(update, context)

        self.assertEqual(len(bot.pinned), message_amount)
        self.assertEqual(len(bot.sent), 1)
        self.assertEqual(len(bot.edited), message_amount - 1)

    def test_user_message_resends(self):
        storage = self.get_storage()
        bot = Bot()
        context = Context(bot)
        pin_handler = handlers.pinned(storage)
        message_handler = handlers.message(storage)

        message_amount = 5
        msgs = gen_same_chat_messages(message_amount)
        upds = [Update(msg, None) for msg in msgs]

        user_message = gen_message()
        user_message.chat.id = msgs[0].chat.id
        user_update = Update(user_message, None)

        for update in upds:
            pin_handler(update, context)
            message_handler(user_update, context)

        self.assertEqual(len(bot.pinned), message_amount)
        self.assertEqual(len(bot.sent), message_amount)
        self.assertEqual(len(bot.edited), 0)

    def test_handlers_store(self):
        storage = self.get_storage()
        bot = Bot()
        context = Context(bot)
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
            pin_handler(pin_update, context)
            self.assertEqual(len(storage.get(chat_id)), amount)

            button_handler(unpin_update, context)
            self.assertEqual(len(storage.get(chat_id)), amount - 1)
            # test deleting non-existant
            button_handler(unpin_update, context)
            self.assertEqual(len(storage.get(chat_id)), amount - 1)

            #second add of deleted to keep amount increasing
            pin_handler(pin_update, context)
            self.assertEqual(len(storage.get(chat_id)), amount)

        unpin_all_cb = Update.CbQuery(msgs[0], handlers.UnpinAll)
        unpin_all_upd = Update(None, unpin_all_cb)
        button_handler(unpin_all_upd, context)
        self.assertFalse(storage.has(chat_id))

    def test_keep_last(self):
        storage = self.get_storage()
        bot = Bot()
        context = Context(bot)
        pin_handler = handlers.pinned(storage)
        button_handler = handlers.button_pressed(storage)

        message_amount = 5
        msgs = gen_same_chat_messages(message_amount)
        upds = [Update(msg, None) for msg in msgs]
        chat_id = msgs[0].chat.id

        for update, amount in zip(upds, range(1, message_amount + 1)):
            pin_handler(update, context)
            self.assertEqual(len(storage.get(chat_id)), amount)

        keep_last_cb = Update.CbQuery(msgs[0], handlers.KeepLast)
        keep_last_upd = Update(None, keep_last_cb)
        button_handler(keep_last_upd, context)

        self.assertTrue(storage.has(chat_id))
        self.assertEqual(len(storage.get(chat_id)), 1)

    def test_deletes_on_nothing(self):
        storage = self.get_storage()
        bot = Bot()
        context = Context(bot)

        pin_handler = handlers.pinned(storage)
        button_handler = handlers.button_pressed(storage)

        message_amount = 5
        msgs = gen_same_chat_messages(message_amount)
        msg_upds = [Update(msg, None) for msg in msgs]

        unpins = [gen_unpin_data(msg) for msg in msgs]
        unpin_upds = [Update(None, unpin) for unpin in unpins]

        chat_id = msgs[0].chat.id
        for pin_update in msg_upds:
            pin_handler(pin_update, context)

        for unpin_update in unpin_upds:
            button_handler(unpin_update, context)

        self.assertEqual(len(bot.deleted), 1)
        self.assertNotEqual(len(bot.sent), 0)
        self.assertEqual(bot.sent[0]['m_id'], bot.deleted[0]['m_id'])
        self.assertEqual(bot.sent[0]['chat_id'], bot.deleted[0]['chat_id'])

        sent_first_batch = len(bot.sent)
        button_handler(unpin_upds[0], context)
        self.assertEqual(len(bot.deleted), 1)
        self.assertEqual(len(bot.sent), sent_first_batch)

    def test_resending_deletes_old(self):
        storage = self.get_storage()
        bot = Bot()
        context = Context(bot)
        pin_handler = handlers.pinned(storage)
        message_handler = handlers.message(storage)

        message_amount = 5
        msgs = gen_same_chat_messages(message_amount)
        upds = [Update(msg, None) for msg in msgs]

        user_message = gen_message()
        user_message.chat.id = msgs[0].chat.id
        user_update = Update(user_message, None)

        for update in upds:
            pin_handler(update, context)
            sent = bot.sent[-1]
            message_handler(user_update, context)
            pin_handler(update, context)
            deleted = bot.deleted[-1]

            self.assertEqual(sent['m_id'], deleted['m_id'])
            self.assertEqual(sent['chat_id'], deleted['chat_id'])

    def test_gathers_correct_links(self):
        storage = self.get_storage()
        bot = Bot()
        context = Context(bot)
        pin_handler = handlers.pinned(storage)

        msg = gen_message()
        class Entity:
            def __init__(self, start, length):
                self.offset = start
                self.length = length
                self.type = "url"
                self.url = None

        link1 = "github.com"
        link2 = "https://kde.org/"
        start1 = 0
        length1 = len(link1)
        start2 = len(link1) + 1
        length2 = len(link2)

        msg.entities = [Entity(start1, length1), Entity(start2, length2)]
        msg.text = "\n".join([link1, link2])

        update = Update(msg, None)
        pin_handler(update, context)

        sent = bot.sent[-1]["text"]
        link_re = re.compile('<a href="([^"]+)">')
        links = link_re.findall(sent)

        self.assertEqual(links[0], link1)
        self.assertEqual(links[1], link2)
