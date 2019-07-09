#!/usr/bin/env python3

from typing import *
from html import escape
from telegram import Message, InlineKeyboardMarkup, InlineKeyboardButton
from enum import Enum
import control

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Description: functions to present data in chat
"""


def gen_preview(msg : Message) -> str:
    max_length = 280

    if msg.text:
        return msg.text[:max_length]
    elif msg.caption:
        return msg.caption[:max_length]
    else:
        return ""


def single_pin(msg_info) -> str:
    lines : List[str] = []

    # first line: preview
    if len(msg_info.preview) > 0:
        lines += [f"{escape(msg_info.preview)}"]

    # second line: icon, sender and date
    time_str = msg_info.date.strftime("%A, %d %B %Y")
    lines += [f"{msg_info.icon} <i>{escape(msg_info.sender)}, {time_str}</i>"]

    # third line: link to post
    lines += [f'<a href="{msg_info.link}">Go to message</a>']

    return "\n".join(lines)


def empty_post() -> Tuple[str, InlineKeyboardMarkup]:
    text = "No pins"
    layout = InlineKeyboardMarkup([[]])
    return (text, layout)


# how the buttons to edit pins should look
class ButtonsStatus(Enum):
    Collapsed = 1
    Expanded = 2

# used in two handlers above
def pins_post(pins, chat_id : int
             ,button_status : ButtonsStatus = ButtonsStatus.Collapsed
             ) -> Tuple[str, InlineKeyboardMarkup]:
    text = "\n\n".join(map(single_pin, pins))

    # generate buttons for pin control
    button_all = InlineKeyboardButton(
        "❌ Unpin all", callback_data=control.UnpinAll)
    button_keep_last = InlineKeyboardButton(
        "🔺 Keep last", callback_data=control.KeepLast)
    button_expand = InlineKeyboardButton(
        "Edit ➕", callback_data=control.ButtonsExpand)
    button_collapse = InlineKeyboardButton(
        "Close ➖", callback_data=control.ButtonsCollapse)

    # special button case when only one pin:
    if len(pins) == 1:
        layout = [[button_all]]
        return (text, InlineKeyboardMarkup(layout))

    # when buttons are set to not shown
    if button_status == ButtonsStatus.Collapsed:
        layout = [[button_keep_last, button_expand]]
        return (text, InlineKeyboardMarkup(layout))

    # generate all expanded buttons

    # first two rows: those buttons
    layout = [[button_all, button_collapse]]

    # other buttons: this style with special data
    def on_button(msg, index) -> str:
        return f"{index + 1} {msg.icon}"
    cb_data = control.unpin_message_data

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
