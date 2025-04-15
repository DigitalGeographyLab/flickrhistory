#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Worker threads wrapping an APIDownloader."""


__all__ = ["CacheUpdaterThread"]


import queue
import threading

from .cache import Cache


class CacheUpdaterThread(threading.Thread):
    """Wraps an ApiDownloader to run in a separate thread."""

    def __init__(self, done_queue):
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
                    try:
                        cache["already downloaded"] += newly_downloaded
                    except KeyError:
                        cache["already downloaded"] = newly_downloaded
                    self.status = f"added {newly_downloaded}"
            except queue.Empty:
                if self.shutdown.is_set():
                    break
