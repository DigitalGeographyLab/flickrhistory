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


import sys
import threading

import blessed

from .basicflickrhistoryDownloader import BasicFlickrHistoryDownloader


class FancyFlickrHistoryDownloader(BasicFlickrHistoryDownloader):
    """
    Download (all) georeferenced flickr posts.

    With fancy console output.
    """

    def report_progress(self):
        """Report current progress."""
        print(
            (
                "Downloaded metadata for {photos: 6d} photos "
                + "and {profiles: 4d} user profiles "
                + "using {workers:d} workers, "
                + "{todo:d} time slots to cover"
            ).format(
                photos=sum([worker.count for worker in self._worker_threads]),
                profiles=self.user_profile_updater_thread.count,
                workers=(threading.active_count() - self.NUM_MANAGERS),
                todo=len(self._todo_deque)
            ),
            file=sys.stderr,
            end="\r"
        )

    def announce_shutdown(self):
        """Tell the user that we initiated shutdown."""
        print(
            "Cleaning up" + (" " * 69),  # 80 - len("Cleaning up")
            file=sys.stderr,
            end="\r"
        )

    def summarise_overall_progress(self):
        """
        Summarise what we have done.

        (Called right before exit)
        """
        print(
            (
                "Downloaded {photos:d} photos "
                + "and {profiles:d} user profiles"
            ).format(
                photos=sum([worker.count for worker in self._worker_threads]),
                profiles=self.user_profile_updater_thread.count
            ),
            file=sys.stderr
        )
