#!/usr/bin/env python3

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3
Description: same as handlers test, but uses a running redis instance on
localhost
"""

import handlers
import unittest
from typing import *
from remote_store import Storage

from test.handlers_test import Bot, gen_same_chat_messages, Update, gen_message, gen_unpin_data


class TestHandlers(unittest.TestCase):

    def test_pin_sends_and_edits(self):
        storage = Storage(addr="localhost")
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
        storage = Storage(addr="localhost")
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
        storage = Storage(addr="localhost")
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
            self.assertEqual(len(storage.get(chat_id)), amount)

            button_handler(bot, unpin_update)
            self.assertEqual(len(storage.get(chat_id)), amount - 1)
            # test deleting non-existant
            button_handler(bot, unpin_update)
            self.assertEqual(len(storage.get(chat_id)), amount - 1)

            #second add of deleted to keep amount increasing
            pin_handler(bot, pin_update)
            self.assertEqual(len(storage.get(chat_id)), amount)

        unpin_all_cb = Update.CbQuery(msgs[0], handlers.UnpinAll)
        unpin_all_upd = Update(None, unpin_all_cb)
        button_handler(bot, unpin_all_upd)
        self.assertFalse(storage.has(chat_id))

    def test_keep_last(self):
        storage = Storage(addr="localhost")
        bot = Bot()
        pin_handler = handlers.pinned(storage)
        button_handler = handlers.button_pressed(storage)

        message_amount = 5
        msgs = gen_same_chat_messages(message_amount)
        upds = [Update(msg, None) for msg in msgs]
        chat_id = msgs[0].chat.id

        for update, amount in zip(upds, range(1, message_amount + 1)):
            pin_handler(bot, update)
            self.assertEqual(len(storage.get(chat_id)), amount)

        keep_last_cb = Update.CbQuery(msgs[0], handlers.KeepLast)
        keep_last_upd = Update(None, keep_last_cb)
        button_handler(bot, keep_last_upd)

        self.assertTrue(storage.has(chat_id))
        self.assertEqual(len(storage.get(chat_id)), 1)
