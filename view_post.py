#!/usr/bin/env python3

from typing import *
from html import escape
from message_info import MessageInfo
from telegram import InlineKeyboardMarkup, InlineKeyboardButton # type: ignore
from enum import Enum
from message_kind import Kind
import control


"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Description: functions to present data in chat
The important ones are single_pin and pins_post
"""


def single_pin(msg_info: MessageInfo, index) -> str:
    lines: List[str] = []
    head_icon = "📌"

    # first line: preview
    preview_line = ""
    # these require disambiguation with icon
    visual_kind = msg_info.kind in [Kind.Photo, Kind.File]
    if len(msg_info.preview.wrapped) == 0 or visual_kind:
        # populate it with icon
        preview_line += f"{msg_info.icon} "
    preview_line += msg_info.preview.wrapped
    lines += [preview_line]

    # second line - header line: icon, sender and date and index
    time_str = msg_info.date.strftime("%Y-%m-%d")
    weekday = msg_info.date.strftime("%a")
    header_line =  f"{head_icon}"
    header_line += f' <a href="{msg_info.link}">'
    header_line += f"[{index}] {time_str}"
    header_line += "</a>"
    header_line += "<i>"
    header_line += f" - {escape(msg_info.sender.wrapped)}, {weekday}"
    header_line += "</i>"
    lines += [header_line]

    return "\n".join(lines)


EmptyPost: Tuple[str, InlineKeyboardMarkup] = (
    "No pins", InlineKeyboardMarkup([[]])
)


# how the buttons to edit pins should look
class ButtonsStatus(Enum):
    Collapsed = 1
    Expanded = 2

# used event handlers to generate view
def pins_post(pins, chat_id: int
             ,button_status: ButtonsStatus = ButtonsStatus.Collapsed
             ) -> Tuple[str, InlineKeyboardMarkup]:
    text = "\n\n".join(single_pin(pin, i + 1) for i, pin in enumerate(pins))

    # generate buttons for pin control
    button_all = InlineKeyboardButton(
        "❌ Unpin all", callback_data=control.UnpinAll)
    button_keep_last = InlineKeyboardButton(
        "Keep last 🔺", callback_data=control.KeepLast)
    button_expand = InlineKeyboardButton(
        "➕ Edit", callback_data=control.ButtonsExpand)
    button_collapse = InlineKeyboardButton(
        "➖ Close", callback_data=control.ButtonsCollapse)

    # special button case when only one pin:
    if len(pins) == 1:
        layout = [[button_all]]
        return (text, InlineKeyboardMarkup(layout))

    # when buttons are set to not shown
    if button_status == ButtonsStatus.Collapsed:
        layout = [[button_expand]]
        return (text, InlineKeyboardMarkup(layout))

    # generate all expanded buttons

    # first two rows: those buttons
    layout = [[button_collapse], [button_all, button_keep_last]]

    # other buttons: this style with special data
    def on_button(msg, index) -> str:
        return f"{index + 1} {msg.icon}"
    cb_data = control.unpin_message_data

    texts = (on_button(msg, index) for index, msg in enumerate(pins))
    cb_datas = (cb_data(msg, index) for index, msg in enumerate(pins))

    buttons = [InlineKeyboardButton(text, callback_data=data)
                for text, data in zip(texts, cb_datas)]

    # split buttons by lines
    on_one_line = best_split(len(buttons))
    rows = [buttons[i:i+on_one_line] for i in range(0, len(buttons), on_one_line)]

    layout += rows

    return (text, InlineKeyboardMarkup(layout))

# choose the best way to split buttons between lines
def best_split(amount: int) -> int:
    best_per_line = 5
    if amount < best_per_line:
        return amount
    #
    # select which has the most buttons on the last row
    candidates = list(range(best_per_line, 1, -1))
    def test_for(amount, candidate):
        if amount % candidate == 0:
            return (candidate, candidate)
        else:
            return (amount % candidate, candidate)
    tests = (test_for(amount, cand) for cand in candidates)
    option = max(tests)[1]
    return option
