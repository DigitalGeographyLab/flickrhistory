#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2019 Christoph Fink, University of Helsinki
#
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 3
#   of the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, see <http://www.gnu.org/licenses/>.


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
