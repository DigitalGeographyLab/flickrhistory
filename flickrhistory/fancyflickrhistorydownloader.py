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

        + "{t.normal}"
    )

    STATUS = (
        "{t.normal} Downloaded metadata for "
        + "{t.bold}{t.magenta}{photos: 9d} 📷 photos "
        + "{t.normal}{t.magenta}{photo_rate: 11.1f}/s\n"

        + "{t.normal} and updated             "
        + "{t.bold}{t.red}{profiles: 9d} 👱 user profiles "
        + "{t.normal}{t.red}{profile_rate: 3.1f}/s\n"

        + "{t.normal} using                   "
        + "{t.bold}{t.green}{workers: 9d} 💪 workers\n"

        + "{t.normal}{t.bold} TODO:                {todo: 12d} 🚧 time slots"

        + "{t.normal}"
    )
    STATUS_LINES = len(STATUS.splitlines())

    SHUTDOWN_ANNOUNCEMENT = "{t.bold}Cleaning up. 🛑 {t.normal}"

    SUMMARY = (
        "{t.normal}Downloaded  {t.bold}{t.magenta}{photos: 9d} 📷 photos "
        + "{t.normal}{t.magenta}{photo_rate: 11.1f}/s\n"
        + "{t.normal}and updated {t.bold}{t.red}{profiles: 9d} 👱 user profiles "
        + "{t.normal}{t.red}{profile_rate: 3.1f}/s\n"

        + "{t.normal}"
    )

    def __init__(self):
        """Initialise FlickrHistoryDownloader."""
        super().__init__()

        self.terminal = blessed.Terminal()

        print(self.WELCOME.format(t=self.terminal))

        # scroll down terminal, in case we’re at the bottom
        print(self.STATUS_LINES * "\n", end="")

        self.pos_y, _ = self.terminal.get_location(timeout=5)
        self._photo_count = 0
        self._profile_count = 0

    def report_progress(self):
        """Report current progress."""
        photo_count, photo_rate, profile_count, profile_rate = self._statistics

        with self.terminal.location(0, (self.pos_y - self.STATUS_LINES)):
            print(
                self.STATUS.format(
                    t=self.terminal,
                    photos=photo_count,
                    photo_rate=photo_rate,
                    profiles=profile_count,
                    profile_rate=profile_rate,
                    workers=(threading.active_count() - self.NUM_MANAGERS),
                    todo=len(self._todo_deque)
                )
            )

    def announce_shutdown(self):
        """Tell the user that we initiated shutdown."""
        # clear the status output
        for i in range(self.STATUS_LINES):
            with self.terminal.location(0, (self.pos_y - (i + 1))):
                print(self.terminal.clear_eol)

        with self.terminal.location(0, (self.pos_y - self.STATUS_LINES)):
            print(self.SHUTDOWN_ANNOUNCEMENT.format(t=self.terminal))

    def summarise_overall_progress(self):
        """
        Summarise what we have done.

        (Called right before exit)
        """
        photo_count, photo_rate, profile_count, profile_rate = self._statistics
        with self.terminal.location(0, (self.pos_y - self.STATUS_LINES)):
            print(
                self.SUMMARY.format(
                    t=self.terminal,
                    photos=photo_count,
                    photo_rate=photo_rate,
                    profiles=profile_count,
                    profile_rate=profile_rate
                )
            )
