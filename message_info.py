#!/usr/bin/env python3

from typing import *
from datetime import datetime
from view import gen_preview, has_links_in, Escaped
from message_kind import Kind
import message_kind
import json

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Desctiption: structure with essential message data
and methods for generating it from tg message.
Also this structure is json-serializable through special methods.
"""

class MessageInfo:
    Kind = message_kind.Kind
    m_id    : int
    kind    : Kind
    link    : str
    sender  : Escaped
    icon    : str
    preview : Escaped
    date    : datetime

    def __init__(self, msg) -> None:
        if msg is None:
            return

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
            return MessageInfo.Kind.Photo
        elif msg.document:
            return MessageInfo.Kind.File
        elif msg.sticker:
            return MessageInfo.Kind.Sticker
        elif has_links_in(msg.entities):
            return MessageInfo.Kind.Link
        elif msg.text and len(msg.text) > 0:
            return MessageInfo.Kind.Text
        else:
            return MessageInfo.Kind.Default

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
        if kind == MessageInfo.Kind.Text:
            return "📌"
        elif kind == MessageInfo.Kind.Photo:
            return "🖼"
        elif kind == MessageInfo.Kind.File:
            return "📎"
        elif kind == MessageInfo.Kind.Sticker:
            return "😀"
        elif kind == MessageInfo.Kind.Link:
            return "🔗"
        else:
            return "📌"

    # JSON methods

    def dumps(self) -> str:
        self_dict = {
             'm_id'    : self.m_id
            ,'kind'    : int(self.kind)
            ,'link'    : self.link
            ,'sender'  : self.sender.wrapped
            ,'icon'    : self.icon
            ,'preview' : self.preview.wrapped
            ,'date'    : int(self.date.timestamp())
            }
        return json.dumps(self_dict)

    @staticmethod
    def loads(text : Union[str, bytes]) -> 'MessageInfo':
        dict = json.loads(text)
        self = MessageInfo(None)

        self.m_id = dict['m_id']
        self.kind    = MessageInfo.Kind(dict['kind'])
        self.link    = dict['link']
        self.sender  = Escaped.from_escaped(dict['sender'])
        self.icon    = dict['icon']
        self.preview = Escaped.from_escaped(dict['preview'])
        self.date    = datetime.utcfromtimestamp(dict['date'])

        return self

