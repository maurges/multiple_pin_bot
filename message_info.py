#!/usr/bin/env python3

from typing import *
from datetime import datetime
from html import escape
from message_kind import Kind
from telegram import Message, MessageEntity # type: ignore
import message_kind
import json

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Desctiption: structure with essential message data
and methods for generating it from tg message.
Also this structure is json-serializable through special methods.
"""


MaxLength = 280

# a wrapper class: the wrapped string is html-escaped
class Escaped:
    wrapped: str
    def __init__(self, s: str) -> None:
        self.wrapped = escape(s)
    @staticmethod
    def from_escaped(s: str) -> 'Escaped':
        self = Escaped("")
        self.wrapped = s
        return self
    def __str__(self):
        return self.wrapped


def gen_icon(kind: Kind) -> str:
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

def gen_preview(msg: Message) -> Escaped:
    if msg.entities != [] and has_links_in(msg.entities):
        return gather_links(msg.entities, msg.text)
    elif msg.caption_entities != [] and has_links_in(msg.caption_entities):
        return gather_links(msg.caption_entities, msg.caption)
    elif msg.text:
        return Escaped(msg.text[:MaxLength] + "...")
    elif msg.caption:
        return Escaped(msg.caption[:MaxLength] + "...")
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
def link_text(entity, all_text: str) -> Escaped:
    start: int = entity.offset
    end: int = start + entity.length
    return Escaped(all_text[start : end])
def make_link(href: Escaped, body: Escaped) -> Escaped:
    return Escaped.from_escaped(f'<a href="{href}">{body}</a>')

class MessagePart(NamedTuple):
    """Used to get links from messages and join all together"""
    text_repr: Escaped
    repr_length: int
    start: int

def gather_links(entities, text: str) -> Escaped:
    # start and end of entity
    ent_parts: List[MessagePart] = []
    # assertion: no entities overlap

    for ent in entities:
        if ent.url:
            # manual says this only works for "text_link", but i say if it has
            # url, that must be a correct url
            body = link_text(ent, text)
            url = Escaped(ent.url)
            part = MessagePart( text_repr = make_link(url, body)
                              , repr_length = len(body.wrapped)
                              , start = ent.offset
                              )
            ent_parts.append(part)
        elif is_link(ent):
            # it's a text_link or url, but doesn't have an own url. Extract one
            # from text body
            href = link_text(ent, text)
            part = MessagePart( text_repr = make_link(href, href)
                              , repr_length = len(href.wrapped)
                              , start = ent.offset
                              )
            ent_parts.append(part)
        else:
            continue
    ent_parts.sort(key = lambda x: x.start)

    result = ""
    cur_start = 0
    too_long = False
    for ent in ent_parts:
        if not too_long:
            cur_text = text[cur_start : ent.start]
            result += cur_text
            if len(result) > MaxLength:
                result = result[:MaxLength].strip() + "...\n"
                too_long = True
            result += ent.text_repr.wrapped
            if len(result) > MaxLength:
                # if became too long after adding link, we shouldn't cut
                result = result.strip()
                too_long = True
            cur_start = ent.start + ent.repr_length
        else:
            result += "\n" + ent.text_repr.wrapped
    if len(result) <= MaxLength:
        # append last text
        cur_text = text[cur_start:]
        result += Escaped(cur_text).wrapped
        if len(result) + len(cur_text) > MaxLength:
            result = result[:MaxLength].strip() + "..."

    return Escaped.from_escaped(result)

def gather_file(document) -> Escaped:
    name_str = f"<b>{document.file_name}</b>"
    return Escaped.from_escaped(name_str)

class MessageInfo:
    m_id:    int
    kind:    Kind
    link:    str
    sender:  Escaped
    icon:    str
    preview: Escaped
    date:    datetime

    def __init__(self, msg) -> None:
        if msg is None:
            return

        self.m_id = msg.message_id
        self.kind = self.gen_kind(msg)
        self.link = self.gen_link(msg)
        self.icon = gen_icon(self.kind)
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
            return Kind.Photo
        elif msg.document:
            return Kind.File
        elif msg.sticker:
            return Kind.Sticker
        elif has_links_in(msg.entities):
            return Kind.Link
        elif msg.text and len(msg.text) > 0:
            return Kind.Text
        else:
            return Kind.Default

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
    def loads(text: Union[str, bytes]) -> 'MessageInfo':
        dict = json.loads(text)
        self = MessageInfo(None)

        self.m_id = dict['m_id']
        self.kind    = Kind(dict['kind'])
        self.link    = dict['link']
        self.sender  = Escaped.from_escaped(dict['sender'])
        self.icon    = dict['icon']
        self.preview = Escaped.from_escaped(dict['preview'])
        self.date    = datetime.utcfromtimestamp(dict['date'])

        return self

