#!/usr/bin/env python3
from enum import IntEnum

# a small enum for signalling message kinds
class Kind(IntEnum):
    Default = 0
    Text  = 1
    Photo = 2
    File  = 3
    # current api doesn't support polls
    # Poll  = 4
    Sticker = 5
    Link  = 6


