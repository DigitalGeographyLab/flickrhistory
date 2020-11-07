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


"""
Download (all) georeferenced flickr posts.

Overloaded to provide fancy console output
"""


__all__ = ["FancyFlickrHistoryDownloader"]


import datetime
import threading

import blessed

from .basicflickrhistorydownloader import BasicFlickrHistoryDownloader
from . import __version__ as version


class FancyFlickrHistoryDownloader(BasicFlickrHistoryDownloader):
    """
    Download (all) georeferenced flickr posts.

    With fancy console output.
    """

    WELCOME = (
        "{t.bold}{t.blue} ### flickrhistory "
        + "{t.normal}{t.blue}"
        + version
        + "{t.bold} ###"
    )

    STATUS = (
        "{t.normal} Downloaded metadata for {t.bold}{t.magenta}{photos: 9d} 📷 photos "
        + "{t.normal}{t.magenta}{photo_rate: 11.1f}/s\n"
        + "{t.normal} and updated             {t.bold}{t.red}{profiles: 9d} 👱 user profiles "
        + "{t.normal}{t.red}{profile_rate: 3.1f}/s\n"
        + "{t.normal} using                   {t.bold}{t.green}{workers: 9d} 💪 workers\n"
        + "{t.normal}{t.bold} TODO:                {todo: 12d} 🚧 time slots"
    )
    STATUS_LINES = len(STATUS.splitlines())

    SHUTDOWN_ANNOUNCEMENT = "{t.bold}Cleaning up. 🛑"

    SUMMARY = (
        "{t.normal}Downloaded  {t.bold}{t.magenta}{photos: 9d} 📷 photos "
        + "{t.normal}{t.magenta}{photo_rate: 11.1f}/s\n"
        + "{t.normal}and updated {t.bold}{t.red}{profiles: 9d} 👱 user profiles "
        + "{t.normal}{t.red}{profile_rate: 3.1f}/s\n"
    )

    def __init__(self):
        """Initialise FlickrHistoryDownloader."""
        super().__init__()

        self.started = datetime.datetime.now()
        self.terminal = blessed.Terminal()

        print(self.WELCOME.format(t=self.terminal))

        # scroll down terminal, in case we’re at the bottom
        print(self.STATUS_LINES * "\n", end="")

        self.POS_Y, self.POS_X = self.terminal.get_location(timeout=5)
        self._photo_count = 0
        self._profile_count = 0

    def report_progress(self):
        """Report current progress."""
        self._update_statistics()

        with self.terminal.location(0, (self.POS_Y - self.STATUS_LINES)):
            print(
                self.STATUS.format(
                    t=self.terminal,
                    photos=self.photo_count,
                    photo_rate=self.photo_rate,
                    profiles=self.profile_count,
                    profile_rate=self.profile_rate,
                    workers=(threading.active_count() - self.NUM_MANAGERS),
                    todo=len(self._todo_deque)
                )
            )

    def announce_shutdown(self):
        """Tell the user that we initiated shutdown."""
        # clear the status output
        for i in range(self.STATUS_LINES):
            with self.terminal.location(0, (self.POS_Y - (i + 1))):
                print(self.terminal.clear_eol)

        with self.terminal.location(0, (self.POS_Y - self.STATUS_LINES)):
            print(self.SHUTDOWN_ANNOUNCEMENT.format(t=self.terminal))

    def summarise_overall_progress(self):
        """
        Summarise what we have done.

        (Called right before exit)
        """
        self._update_statistics()
        with self.terminal.location(0, (self.POS_Y - self.STATUS_LINES)):
            print(
                self.SUMMARY.format(
                    t=self.terminal,
                    photos=self.photo_count,
                    photo_rate=self.photo_rate,
                    profiles=self.profile_count,
                    profile_rate=self.profile_rate
                )
            )

    def _update_statistics(self):
        self.runtime = float((datetime.datetime.now() - self.started).total_seconds())

        self.photo_count = sum([worker.count for worker in self._worker_threads])
        self.photo_rate = self.photo_count / self.runtime

        self.profile_count = self.user_profile_updater_thread.count
        self.profile_rate = self.profile_count / self.runtime