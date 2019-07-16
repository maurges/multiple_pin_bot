#!/usr/bin/env python3

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3
"""

import unittest
import threading
from time import sleep
from varlock import VarLock


class TestVarLock(unittest.TestCase):

    def test_basic_usage(self):
        lock = VarLock()

        # acquiring
        lock.acquire(5)
        lock.release(5)
        # double acquiring
        lock.acquire(5)
        lock.release(5)

        # acq different at the same time
        lock.acquire(5)
        lock.acquire(6)
        lock.release(5)
        lock.release(6)

        # with
        with lock.lock(5):
            with lock.lock(6):
                with lock.lock(7):
                    pass

    def test_double_release(self):
        lock = VarLock()

        lock.acquire(5)
        lock.release(5)
        self.assertRaises(RuntimeError, lock.release, 5)

    def test_release_in_with(self):
        lock = VarLock()

        try:
            with lock.lock(5):
                lock.release(5)
        except RuntimeError as e:
            return
        self.fail("didn't raise an exception")

    def test_locks(self):
        lock = VarLock()

        lock.acquire(5)
        r = lock.acquire(5, timeout=0.2)
        self.assertFalse(r)

        lock.acquire(6)
        r = lock.acquire(6, timeout=0.2)
        self.assertFalse(r)

        lock.release(6)
        lock.release(5)

    def test_concurrent(self):
        lock = VarLock()

        param = 5
        wait_time = 1
        hold_time = 0.4

        def conc1(lock, assertTrue) -> None:
            r = lock.acquire(param, timeout = wait_time)
            assertTrue(r)
            sleep(hold_time)
            lock.release(param)

        def conc2(lock, assertTrue) -> None:
            sleep(hold_time / 4)
            r = lock.acquire(param, timeout = wait_time)
            assertTrue(r)
            lock.release(param)

        args = (lock, self.assertTrue)
        t1 = threading.Thread(target=conc1, args=args)
        t2 = threading.Thread(target=conc2, args=args)

        ts = [t1, t2]
        [t.start() for t in ts]
        [t.join() for t in ts]
