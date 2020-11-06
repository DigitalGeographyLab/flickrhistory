#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2020 Christoph Fink, University of Helsinki
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


"""Worker threads wrapping an APIDownloader."""


__all__ = ["CacheUpdaterThread"]


import queue
import threading

from .cache import Cache


class CacheUpdaterThread(threading.Thread):
    """Wraps an ApiDownloader to run in a separate thread."""

    def __init__(
            self,
            done_queue
    ):
        """
        Intialize a CacheUpdaterThread.

        Args:
            done_queue: queue.Queue with updated TimeSpans
        """
        super().__init__()
        self._done_queue = done_queue
        self.shutdown = threading.Event()
        self.status = "init"

    def run(self):
        """Get TimeSpans off done_queue and update cache."""
        while True:
            try:
                newly_downloaded = self._done_queue.get(timeout=0.1)
                with Cache() as cache:
                    cache["already downloaded"] += newly_downloaded
                    self.status = "added {}".format(newly_downloaded)
            except queue.Empty:
                if self.shutdown.is_set():
                    break
