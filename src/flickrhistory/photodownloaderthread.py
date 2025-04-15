#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Worker threads wrapping an APIDownloader."""


__all__ = ["PhotoDownloaderThread"]


import threading

from .database import PhotoSaver
from .exceptions import ApiResponseError, DownloadBatchIsTooLargeError
from .photodownloader import PhotoDownloader


class PhotoDownloaderThread(threading.Thread):
    """Wraps an PhotoDownloader to run in a separate thread."""

    def __init__(self, api_key_manager, todo_deque, done_queue):
        """
        Intialize an PhotoDownloaderThread.

        Args:
            api_key_manager: instance of an ApiKeyManager
            todo_deque: collections.deque that serves TimeSpans
                        that need to be downloaded
            done_queue: queue.Queue into which to put TimeSpans
                        that have been downloaded

        """
        super().__init__()

        self.count = 0

        self._api_key_manager = api_key_manager
        self._todo_deque = todo_deque
        self._done_queue = done_queue

        self.shutdown = threading.Event()

    def run(self):
        """Get TimeSpans off todo_deque and download photos."""
        while not self.shutdown.is_set():
            try:
                timespan = self._todo_deque.pop()
            except IndexError:
                break

            photo_downloader = PhotoDownloader(timespan, self._api_key_manager)

            try:
                for photo in photo_downloader.photos:
                    photo = PhotoSaver().save(photo)

                    self.count += 1

                    if self.shutdown.is_set():
                        # let’s only report back on how much we
                        # in fact downloaded, not what our quota was
                        timespan.end = photo.date_posted
                        break

            except ApiResponseError:
                # API returned some bogus/none-JSON data
                # let’s add this timespan to the other end
                # of the todo deque and start over
                # TODO: implement logging and log the
                # data (which is in the exception’s message)
                self._todo_deque.appendleft(timespan)
                continue

            except DownloadBatchIsTooLargeError:
                # too many photos in this time span,
                # let’s split it in half and re-inject
                # it to the todo deque
                for half_timespan in timespan / 2:
                    self._todo_deque.append(half_timespan)

                # get a new timespan from the deque :)
                continue

            # … report to parent thread how much we worked
            self._done_queue.put(timespan)
