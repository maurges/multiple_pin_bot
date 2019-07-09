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

    if msg.entities != [] and has_links_in(msg.entities):
        return gather_links(msg.entities, msg.text)
    elif msg.caption_entities != [] and has_links_in(msg.caption_entities):
        return gather_links(msg.caption_entities, msg.caption)
    elif msg.text:
        return escape(msg.text[:max_length])
    elif msg.caption:
        return escape(msg.caption[:max_length])
    else:
        return ""

def is_link(entity):
    return entity.type == "url" or entity.type == "text_link"
def has_links_in(entities) -> bool:
    return any(map(is_link, entities))
def link_text(entity, all_text : str) -> str:
    start : int = entity.offset
    end : int = start + entity.length
    return all_text[start : end]
def make_link(href : str, body : str) -> str:
    return f'<a href="{escape(href)}">{escape(body)}</a>'

def gather_links(entities, text : str) -> str:
    lines : List[str] = []
    for ent in entities:
        if ent.url:
            # manual says this only works for "text_link", but i say if it has
            # url, that must be a correct url
            body = link_text(ent, text)
            lines.append(make_link(ent.url, body))
        elif is_link(ent):
            # it's a text_link or url, but doesn't have an own url. Extract one
            # from text body
            href = link_text(ent, text)
            lines.append(make_link(href, href))
        else:
            continue
    return "\n".join(lines)



def single_pin(msg_info) -> str:
    lines : List[str] = []

    # first line: preview
    if len(msg_info.preview) > 0:
        lines += [f"{msg_info.preview}"]

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
    on_one_line = best_split(len(buttons))
    rows = [buttons[i:i+on_one_line] for i in range(0, len(buttons), on_one_line)]

    layout += rows

    return (text, InlineKeyboardMarkup(layout))

# choose the best way to split buttons between lines
def best_split(amount : int) -> int:
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
