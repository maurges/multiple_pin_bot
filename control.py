#!/usr/bin/env python3

from typing import *
from telegram import Message

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Description: generate and parse data in buttons
"""

# button actions in callback data
UnpinAll = "$$ALL"
KeepLast = "$$LAST"
ButtonsExpand = "$$EXPAND"
ButtonsCollapse = "$$COLLAPSE"

def unpin_message_data(msg : Message, index : int) -> str:
    return f"{str(msg.m_id)}:{index}"

# for data packed with function above: retrieve id and index
def parse_unpin_data(data : str) -> Tuple[int, int]:
    id, index = map(int, data.split(':'))
    return (id, index)
