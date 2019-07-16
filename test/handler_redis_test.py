#!/usr/bin/env python3

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3
Description: same as handlers test, but uses a running redis instance on
localhost
"""

import handlers
import unittest
from typing import *
from remote_store import Storage

from test.handlers_test import TestHandlers as LocalTestHandlers


class TestHandlers(LocalTestHandlers):
    def get_storage(self):
        return Storage(addr="localhost")
