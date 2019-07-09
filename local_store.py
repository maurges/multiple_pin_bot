#!/usr/bin/env python3

from typing import *
from datetime import datetime
from enum import IntEnum
from view import gen_preview, has_links_in, Escaped

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Description: proxy class to a means of storage. For now i'm using python
dict, but this should be replaced with something persistant very soon
The Storage class stores different kinds of objects, but each is indexed with
chat id
"""


# structure with essential message data
# and methods for generating it from tg message
class MessageInfoType:
    class Kind(IntEnum):
        Default = 0
        Text  = 1
        Photo = 2
        File  = 3
        # current api doesn't support polls
        # Poll  = 4
        Sticker = 5
        Link  = 6

    m_id    : int
    kind    : Kind
    link    : str
    sender  : Escaped
    icon    : Escaped
    preview : Escaped
    date    : datetime

    def __init__(self, msg) -> None:
        self.m_id = msg.message_id

        self.kind = self.gen_kind(msg)
        self.link = self.gen_link(msg)
        self.icon = self.gen_icon(self.kind)
        self.preview = gen_preview(msg)
        self.date = msg.date

        # generate sender info
        sender = msg.from_user.first_name
        if msg.from_user.last_name:
            sender += " " + msg.from_user.last_name
        self.sender = Escaped(sender)


    @staticmethod
    def gen_kind(msg) -> Kind:
        if msg.photo and len(msg.photo) > 0:
            return MessageInfoType.Kind.Photo
        elif msg.document:
            return MessageInfoType.Kind.File
        elif msg.sticker:
            return MessageInfoType.Kind.Sticker
        elif has_links_in(msg.entities):
            return MessageInfoType.Kind.Link
        elif msg.text and len(msg.text) > 0:
            return MessageInfoType.Kind.Text
        else:
            return MessageInfoType.Kind.Default

    @staticmethod
    def gen_link(msg) -> str:
        chat_id = msg.chat_id
        # this api adapter uses strage int representation. Citation:
        # botapi prefixes:
        # + for pms
        # - for small group chats
        # -100 for channels and megagroups
        # we need to make a positive out of this
        if chat_id < 0:
            chat_id = -chat_id
            chat_s = str(chat_id)
            if chat_s[0:3] == "100":
                chat_s = chat_s[3:]
                chat_id = int(chat_s)
        return f"https://t.me/c/{chat_id}/{msg.message_id}"

    @staticmethod
    def gen_icon(kind : Kind) -> str:
        if kind == MessageInfoType.Kind.Text:
            return "📌"
        elif kind == MessageInfoType.Kind.Photo:
            return "🖼"
        elif kind == MessageInfoType.Kind.File:
            return "📎"
        elif kind == MessageInfoType.Kind.Sticker:
            return "😀"
        elif kind == MessageInfoType.Kind.Link:
            return "🔗"
        else:
            return "📌"


class Storage:
    MessageInfo = MessageInfoType

    # pinned messages
    _pin_data  : Dict[int, List[MessageInfoType]]
    # msg_id of the bot's message with pins
    _editables : Dict[int, int]
    # whether someone wrote something to chat after bot's pin
    # key exists if nobody wrote
    _no_chat_messages_added : Dict[int, Tuple]

    def __init__(self) -> None:
        self._pin_data  = {}
        self._editables = {}
        self._no_chat_messages_added = {}

    def has(self, chat_id : int) -> bool:
        return chat_id in self._pin_data and self._pin_data[chat_id] != []
    def get(self, chat_id : int) -> List[MessageInfoType]:
        return self._pin_data[chat_id]

    def add(self, chat_id : int, msg : MessageInfoType) -> None:
        if chat_id not in self._pin_data:
            self._pin_data[chat_id] = [msg]
        else:
            self._pin_data[chat_id].insert(0, msg)

    def clear(self, chat_id : int) -> None:
        if chat_id in self._pin_data:
            del self._pin_data[chat_id]

    def clear_keep_last(self, chat_id : int) -> None:
        if chat_id in self._pin_data:
            # latest messages are pushed to the back, so we just delete
            # everything but very last message
            self._pin_data[chat_id] = self._pin_data[chat_id][:1]

    def remove(self, chat_id : int, m_id : int, hint : int = 0) -> None:
        if chat_id not in self._pin_data:
            return

        pins = self._pin_data[chat_id]
        # calculate indicies to drop
        all_bad = [(abs(index - hint), index)
                      for msg, index in zip(pins, range(len(pins)))
                      if msg.m_id == m_id
                  ]
        if all_bad == []:
            return

        to_delete = min(all_bad)[1]
        del pins[to_delete]

    # get and set id of message that you need to edit
    def get_message_id(self, chat_id : int) -> int:
        return self._editables[chat_id]
    def set_message_id(self, chat_id : int, m_id : int) -> None:
        self._editables[chat_id] = m_id
        # automatically set that no user has messaged us
        self._no_chat_messages_added[chat_id] = ()
    def has_message_id(self, chat_id : int) -> bool:
        return chat_id in self._editables

    # status of last message
    def did_user_message(self, chat_id : int) -> bool:
        return chat_id not in self._no_chat_messages_added
    def user_message_added(self, chat_id : int) -> None:
        if chat_id in self._no_chat_messages_added:
            del self._no_chat_messages_added[chat_id]
