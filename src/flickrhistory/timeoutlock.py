#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""A timer-released threading.Lock-like lock."""


__all__ = ["TimeoutLock"]


import threading
import time


class TimeoutLock:
    """A timer-released threading.Lock-like lock."""

    def __init__(self, timeout=1.0):
        """Intialize a timer-released threading.Lock-like lock."""
        self._lock = threading.Lock()
        self._lock_time = 0
        self.timeout = timeout

    def __enter__(self):
        """Acquire the lock using a contextmanager."""
        self.acquire()

    def __exit__(self, *_):
        """Release the lock using a contextmanager."""
        self.release()

    def acquire(self, blocking=True, timeout=-1):
        """Acquire the lock, blocking or non-blocking."""
        if self._lock.acquire(blocking=False):
            return True

        if blocking:
            wait_time = (self._lock_time + self.timeout) - time.time()
            if timeout == -1 or timeout > wait_time:
                if wait_time > 0:
                    time.sleep(wait_time)
                self._lock.release()
                return self.acquire()

        return False

    def release(self):
        """Release the lock."""
        self._lock_time = time.time()
