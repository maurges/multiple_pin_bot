#!/usr/bin/env python3

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import handlers
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.ext import MessageHandler, Filters
from storage import Storage


def main(token : str) -> None:
    updater = Updater(token)
    dp = updater.dispatcher

    storage = Storage()

    # catch messages pinned
    pin_filter = Filters.status_update.pinned_message
    dp.add_handler(MessageHandler(pin_filter, handlers.pinned(storage)))
    # catch presses of "unpin" buttons
    dp.add_handler(CallbackQueryHandler(handlers.button_pressed(storage)))

    # mundane handlers
    dp.add_handler(CommandHandler("start", handlers.start))
    dp.add_handler(CommandHandler("help", handlers.help))

    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                       ,level=logging.INFO)
    logger = logging.getLogger(__name__)
    dp.add_error_handler(handlers.error(logger))


    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    with open("token.txt", "r") as tfile:
        token = tfile.read().strip()
    main(token)
