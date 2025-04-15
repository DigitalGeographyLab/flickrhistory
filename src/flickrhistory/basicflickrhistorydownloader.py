#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Download (all) georeferenced flickr posts."""


__all__ = ["BasicFlickrHistoryDownloader"]


import collections
import datetime
import queue
import math
import multiprocessing
import sys
import threading
import time

from .apikeymanager import ApiKeyManager
from .cache import Cache
from .cacheupdaterthread import CacheUpdaterThread
from .config import Config
from .licensedownloader import LicenseDownloader
from .photodownloaderthread import PhotoDownloaderThread
from .photoupdaterthread import PhotoUpdaterThread
from .sigtermreceivedexception import SigTermReceivedException
from .timespan import TimeSpan
from .userprofileupdaterthread import UserProfileUpdaterThread


class BasicFlickrHistoryDownloader:
    """Download (all) georeferenced flickr posts."""

    NUM_WORKERS = multiprocessing.cpu_count()
    NUM_MANAGERS = 2  # main thread + cache_updater

    # if output into pipe (e.g. logger, systemd), then
    # print status every 10 minutes, else every 1/5 sec
    # also normal linefeed instead of carriage return for piped output
    STATUS_UPDATE_SEC = 0.2 if sys.stderr.isatty() else 600
    STATUS_UPDATE_LINE_END = "\r" if sys.stderr.isatty() else "\n"

    def __init__(self):
        """Intialise a FlickrHistory object."""
        self.started = datetime.datetime.now()

        self._todo_deque = collections.deque()
        self._done_queue = queue.Queue()

        self._worker_threads = []
        self._cache_updater_thread = CacheUpdaterThread(self._done_queue)

        with Config() as config:
            self._api_key_manager = ApiKeyManager(config["flickr_api_keys"])

    def download(self):
        """Download all georeferenced flickr posts."""
        LicenseDownloader(self._api_key_manager).update_licenses()

        for gap in self.gaps_in_download_history:
            self._todo_deque.append(gap)

        try:
            # start downloaders
            for _ in range(self.NUM_WORKERS):
                worker = PhotoDownloaderThread(
                    self._api_key_manager, self._todo_deque, self._done_queue
                )
                worker.start()
                self._worker_threads.append(worker)

            # start user profile updaters
            for i in range(self.NUM_WORKERS):
                worker = UserProfileUpdaterThread(
                    self._api_key_manager, (i + 1, self.NUM_WORKERS)
                )
                worker.start()
                self._worker_threads.append(worker)

            # start photo record updaters
            for i in range(self.NUM_WORKERS):
                worker = PhotoUpdaterThread(
                    self._api_key_manager, (i + 1, self.NUM_WORKERS)
                )
                worker.start()
                self._worker_threads.append(worker)

            # start cache updater
            self._cache_updater_thread = CacheUpdaterThread(self._done_queue)
            self._cache_updater_thread.start()

            while threading.active_count() > self.NUM_MANAGERS:
                self.report_progress()
                time.sleep(self.STATUS_UPDATE_SEC)

        except (KeyboardInterrupt, SigTermReceivedException):
            self.announce_shutdown()
            for worker in self._worker_threads:
                worker.shutdown.set()

        finally:
            self.summarise_overall_progress()
            for worker in self._worker_threads:
                worker.join()
            self._cache_updater_thread.shutdown.set()
            self._cache_updater_thread.join()

    def report_progress(self):
        """Report current progress."""
        photo_count, _, profile_count, _ = self._statistics
        print(
            (
                f"Downloaded metadata for {photo_count: 6d} photos "
                f"and {profile_count: 4d} user profiles "
                f"using {(threading.active_count() - self.NUM_MANAGERS)} workers, "
                f"{len(self._todo_deque)} time slots to cover"
            ),
            file=sys.stderr,
            end=self.STATUS_UPDATE_LINE_END,
            flush=True,
        )

    def announce_shutdown(self):
        """Tell the user that we initiated shutdown."""
        print(
            "Cleaning up" + (" " * 69),  # 80 - len("Cleaning up")
            file=sys.stderr,
            end=self.STATUS_UPDATE_LINE_END,
            flush=True,
        )

    def summarise_overall_progress(self):
        """
        Summarise what we have done.

        (Called right before exit)
        """
        photo_count, _, profile_count, _ = self._statistics
        print(
            f"Downloaded {photo_count} photos and {profile_count} user profiles",
            file=sys.stderr,
        )

    @property
    def gaps_in_download_history(self):
        """Find gaps in download history."""
        already_downloaded = self.already_downloaded_timespans
        one_day = datetime.timedelta(days=1)  # for comparison

        for i in range(len(already_downloaded) - 1):
            gap = TimeSpan(already_downloaded[i].end, already_downloaded[i + 1].start)
            if gap.duration > one_day:
                divider = math.ceil(gap.duration / one_day)
                for part_of_gap in gap / divider:
                    yield part_of_gap
            else:
                yield gap

    @property
    def already_downloaded_timespans(self):
        """Figure out for which time spans we already have data."""
        with Cache() as cache:
            try:
                timespans = cache["already downloaded"]
            except KeyError:
                timespans = []

        # delete existing 0-length time spans
        timespans = [
            timespan
            for timespan in timespans
            if timespan.duration > datetime.timedelta(0)
        ]

        # add 0-length time spans for
        # - “beginning of all time”
        #  - now()
        #
        # beginning of time cannot be simply epoch 0, because the flickr API
        # matches dates slightly fuzzily, i.e. we would get ALL (or many) photos
        # that have a corrupted or missing upload date (don’t ask me, how flickr
        # managed to mess up the upload date)
        # on top of that, some small timestamps seems to be simply 0 +- timezone offset
        # which invalidates pretty much the entire first day after epoch 0
        # this is why we use epoch 0 + 1 day
        zero = datetime.datetime.fromtimestamp(
            0, tz=datetime.timezone.utc
        ) + datetime.timedelta(days=1)
        now = datetime.datetime.now(datetime.timezone.utc)
        timespans += [TimeSpan(zero, zero), TimeSpan(now, now)]

        return sum(timespans)  # sum resolves overlaps

    @property
    def _statistics(self):
        runtime = float((datetime.datetime.now() - self.started).total_seconds())

        photo_count = sum(
            [
                worker.count
                for worker in self._worker_threads
                if isinstance(worker, PhotoDownloaderThread)
            ]
        )
        photo_rate = photo_count / runtime

        profile_count = sum(
            [
                worker.count
                for worker in self._worker_threads
                if isinstance(worker, UserProfileUpdaterThread)
            ]
        )
        profile_rate = profile_count / runtime

        return (photo_count, photo_rate, profile_count, profile_rate)
