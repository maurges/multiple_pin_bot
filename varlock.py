#!/sur/bin/env python3

"""
Author: d86leader@mail.com, 2019
License: published under GNU GPL-3

Description: a parametrized lock object.
You can acquire a lock for a parameter, and if that parameter is not already
locked, you enter may enter a critical section.
My use-case is locking on different int values. So entering a critical section
with thr1.a = 228 and thr2.a = 322 will not lock, and the section would execute
concurrently, while entering with thr1.a = 228 and thr2.a = 228 would execute
the threads consequently.
"""

from threading import Lock
from typing import Dict, Any

class VarLock:
    _locks : Dict[Any, Lock]
    _ack_lock : Lock

    def __init__(self) -> None:
        self._locks = {}
        self._ack_lock = Lock()

    def acquire(self, var : Any, *args, **kwargs) -> bool:
        with self._ack_lock:
            if var not in self._locks:
                self._locks[var] = Lock()
        return self._locks[var].acquire(*args, **kwargs)

    def release(self, var : Any) -> None:
        with self._ack_lock:
            if var not in self._locks:
                raise RuntimeError("Attempting to release an unlocked lock")
        self._locks[var].release()

    # to be used in with statements
    def lock(self, var : Any) -> Lock:
        with self._ack_lock:
            if var not in self._locks:
                self._locks[var] = Lock()
        return self._locks[var]
