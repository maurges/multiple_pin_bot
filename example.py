#!/usr/bin/env python3
"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
Waits for command and creates an example pin post.
"""

import logging
import handlers
import traceback
from telegram.ext import CommandHandler # type: ignore
from telegram.ext import Updater, MessageHandler, Filters # type: ignore
from local_store import Storage as LocalStorage
from random import randint, choice
import test.handlers_test as test


def main(token: str) -> None:
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    def print_exception(func):
        def r(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                tb = traceback.format_exc()
                print(tb)
        return r

    @print_exception
    def run_example(msg_update, msg_context) -> None:
        print("Got example command")
        storage = LocalStorage()
        bot = test.Bot()
        context = test.Context(bot)
        messages = []

        # message with links
        for _ in range(randint(5, 7)):
            msg = test.gen_message()
            if choice([True, False]):
                # link message
                link = choice(["github.com", "https://kde.org/"])
                text = f"foo {link} bar"
                start = 4
                length = len(link)
                msg.entities = [test.Entity(start, length)]
                msg.text = text
            else:
                # regular message
                pass
            messages.append(msg)

        # set correct chat_id
        for msg in messages:
            msg.chat = msg_update.message.chat

        # do pinning
        for msg in messages:
            update = test.Update(msg, None)
            handlers.pinned(storage)(update, context)

        msg_context.bot.send_message(
              msg_update.message.chat_id
            , text=bot.edited[-1]["text"]
            , parse_mode="HTML"
            , reply_markup=bot.edited[-1]["markup"]
            )
        print(bot.edited[-1])

    dp.add_handler(CommandHandler("example", run_example))
    # Enable logging
    logging.basicConfig(
          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        , level=logging.INFO
        )
    logger = logging.getLogger(__name__)
    dp.add_error_handler(handlers.error(logger))

    print("Going to poll")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    with open("token.txt", "r") as tfile:
        token = tfile.read().strip()
    main(token)
