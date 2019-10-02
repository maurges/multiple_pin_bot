#!/usr/bin/env python3

from typing import *
from html import escape
from telegram import Message, InlineKeyboardMarkup, InlineKeyboardButton
from enum import Enum
from message_kind import Kind
import control

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Description: functions to present data in chat
The important ones are single_pin and pins_post
"""


# a wrapper class: the wrapped string is html-escaped
class Escaped:
    wrapped : str
    def __init__(self, s : str) -> None:
        self.wrapped = escape(s)
    @staticmethod
    def from_escaped(s : str) -> 'Escaped':
        self = Escaped("")
        self.wrapped = s
        return self
    def __str__(self):
        return self.wrapped


def gen_icon(kind : Kind) -> str:
    if kind == Kind.Text:
        return "📝"
    elif kind == Kind.Photo:
        return "🖼"
    elif kind == Kind.File:
        return "📎"
    elif kind == Kind.Sticker:
        return "😀"
    elif kind == Kind.Link:
        return "🔗"
    else:
        return "📍"

def gen_preview(msg : Message) -> Escaped:
    max_length = 280

    if msg.entities != [] and has_links_in(msg.entities):
        return gather_links(msg.entities, msg.text)
    elif msg.caption_entities != [] and has_links_in(msg.caption_entities):
        return gather_links(msg.caption_entities, msg.caption)
    elif msg.text:
        return Escaped(msg.text[:max_length])
    elif msg.caption:
        return Escaped(msg.caption[:max_length])
    elif msg.document:
        return gather_file(msg.document)
    elif msg.sticker:
        return Escaped(msg.sticker.emoji)
    else:
        return Escaped("")

def is_link(entity):
    return entity.type == "url" or entity.type == "text_link"
def has_links_in(entities) -> bool:
    return any(map(is_link, entities))
def link_text(entity, all_text : str) -> Escaped:
    start : int = entity.offset
    end : int = start + entity.length
    return Escaped(all_text[start : end])
def make_link(href : Escaped, body : Escaped) -> Escaped:
    return Escaped.from_escaped(f'<a href="{href}">{body}</a>')

def gather_links(entities, text : str) -> Escaped:
    lines : List[Escaped] = []
    for ent in entities:
        if ent.url:
            # manual says this only works for "text_link", but i say if it has
            # url, that must be a correct url
            body = link_text(ent, text)
            url = Escaped(ent.url)
            lines.append(make_link(url, body))
        elif is_link(ent):
            # it's a text_link or url, but doesn't have an own url. Extract one
            # from text body
            href = link_text(ent, text)
            lines.append(make_link(href, href))
        else:
            continue
    # unwrap lines, join them and wrap again
    lines_str = map(str, lines)
    return Escaped.from_escaped("\n".join(lines_str))

def gather_file(document) -> Escaped:
    name_str = f"<b>{document.file_name}</b>"
    return Escaped.from_escaped(name_str)


def single_pin(msg_info, index) -> str:
    lines : List[str] = []
    head_icon = "🏷"

    # first line: preview
    preview_line = ""
    if len(msg_info.preview.wrapped) == 0:
        # populate it with icon
        preview_line = f"{msg_info.icon}"
    else:
        preview_line += msg_info.preview.wrapped
        # add icon to disambiguate text from file or photo
        if msg_info.kind in [Kind.Photo, Kind.File]:
            preview_line += f" {msg_info.icon}"
    lines += [preview_line]

    # second line - header line: icon, sender and date and index
    time_str = msg_info.date.strftime("%A, %d %B %Y")
    header_line =  f"{head_icon}"
    header_line += "<i>"
    header_line += f" {escape(msg_info.sender.wrapped)},"
    header_line += "</i>"
    header_line += f' <a href="{msg_info.link}">'
    header_line += f"{time_str} [{index}]"
    header_line += "</a>"
    lines += [header_line]

    return "\n".join(lines)


EmptyPost : Tuple[str, InlineKeyboardMarkup] =(
    "No pins", InlineKeyboardMarkup([[]])
)


# how the buttons to edit pins should look
class ButtonsStatus(Enum):
    Collapsed = 1
    Expanded = 2

# used event handlers to generate view
def pins_post(pins, chat_id : int
             ,button_status : ButtonsStatus = ButtonsStatus.Collapsed
             ) -> Tuple[str, InlineKeyboardMarkup]:
    text = "\n\n".join(single_pin(pin, i + 1) for pin, i in zip(pins, range(len(pins))))

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
