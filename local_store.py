#!/usr/bin/env python3

from typing import *
from message_info import MessageInfo

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Description: proxy class to a means of storage. For now i'm using python
dict, but this should be replaced with something persistant very soon
The Storage class stores different kinds of objects, but each is indexed with
chat id
"""


class Storage:
    # pinned messages
    _pin_data  : Dict[int, List[MessageInfo]]
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
    def get(self, chat_id : int) -> List[MessageInfo]:
        return self._pin_data[chat_id]

    def add(self, chat_id : int, msg : MessageInfo) -> None:
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
                      for index, msg in enumerate(pins)
                      if msg.m_id == m_id
                  ]
        if all_bad == []:
            return

        to_delete = min(all_bad)[1]
        del pins[to_delete]

    def replace_same_id(self, chat_id : int, edited : MessageInfo) -> None:
        if chat_id not in self._pin_data:
            return
        messages = self._pin_data[chat_id]
        for message, i in zip(messages, range(len(messages))):
            if message.m_id == edited.m_id:
                messages[i] = edited

    # get and set id of message that you need to edit
    def get_message_id(self, chat_id : int) -> int:
        return self._editables[chat_id]
    def set_message_id(self, chat_id : int, m_id : int) -> None:
        self._editables[chat_id] = m_id
        # automatically set that no user has messaged us
        self._no_chat_messages_added[chat_id] = ()
    def has_message_id(self, chat_id : int) -> bool:
        return chat_id in self._editables
    def remove_message_id(self, chat_id : int) -> None:
        del self._editables[chat_id]

    # status of last message
    def did_user_message(self, chat_id : int) -> bool:
        return chat_id not in self._no_chat_messages_added
    def user_message_added(self, chat_id : int) -> None:
        if chat_id in self._no_chat_messages_added:
            del self._no_chat_messages_added[chat_id]
