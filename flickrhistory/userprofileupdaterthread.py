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


"""Thread to complete missing data on user profiles."""


__all__ = ["UserProfileUpdaterThread"]


import threading
import time

import sqlalchemy

from .config import Config
from .databaseobjects import FlickrUser
from .exceptions import ApiResponseError
from .userprofiledownloader import UserProfileDownloader


class UserProfileUpdaterThread(threading.Thread):
    """Finds incomplete user profiles and downloads missing data from the flickr API."""

    MAX_RETRIES = 5  # once all users have been updated, retry this times (with 10 min breaks)

    def __init__(
            self,
            api_key_manager,
            partition=None
    ):
        """
        Intialize a UserProfileUpdateThread.

        Args:
            api_key_manager: instance of an ApiKeyManager
            partition (tuple of int): download the n-th of m parts of incomplete users

        """
        super().__init__()

        self.count = 0

        self._api_key_manager = api_key_manager
        try:
            part, number_of_partitions = partition
            assert part > 0
            assert part <= number_of_partitions
            self._bounds = (
                (part - 1) * 1.0 / number_of_partitions,
                part * 1.0 / number_of_partitions
            )
        except (
            AssertionError,
            TypeError
        ):
            self._bounds = None

        self.shutdown = threading.Event()

        with Config() as config:
            self._engine = sqlalchemy.create_engine(
                config["database_connection_string"]
            )

    @property
    def nsids_of_users_without_detailed_information(self):
        """Find nsid of incomplete user profiles."""
        # Find nsid of incomplete user profiles
        # We use join_date IS NULL, because after
        # updating a profile it will be "", so NULL is
        # a good way of finding “new” profiles
        with sqlalchemy.orm.Session(self._engine) as session:
            if self._bounds is None:
                nsids_of_users_without_detailed_information = (
                    session.query(FlickrUser.nsid).filter_by(join_date=None)
                )
            else:
                bounds = (
                    sqlalchemy.select(
                        sqlalchemy.sql.functions.percentile_disc(self._bounds[0])
                        .within_group(FlickrUser.id)
                        .label("lower"),
                        sqlalchemy.sql.functions.percentile_disc(self._bounds[1])
                        .within_group(FlickrUser.id)
                        .label("upper")
                    )
                    .select_from(FlickrUser)
                    .filter_by(join_date=None)
                    .cte()
                )
                nsids_of_users_without_detailed_information = (
                    session.query(FlickrUser.nsid)
                    .filter_by(join_date=None)
                    .where(FlickrUser.id.between(bounds.c.lower, bounds.c.upper))
                )

            for nsid, in nsids_of_users_without_detailed_information:
                yield nsid

    def run(self):
        """Get TimeSpans off todo_queue and download photos."""
        user_profile_downloader = UserProfileDownloader(self._api_key_manager)

        retries = 0

        while not (
                self.shutdown.is_set()
                or retries >= self.MAX_RETRIES
        ):
            for nsid in self.nsids_of_users_without_detailed_information:
                try:
                    with sqlalchemy.orm.Session(
                            self._engine
                    ) as session, session.begin():
                        flickr_user = (
                            FlickrUser.from_raw_api_data_flickrprofilegetprofile(
                                user_profile_downloader.get_profile_for_nsid(nsid)
                            )
                        )
                        session.merge(flickr_user)

                    self.count += 1

                except ApiResponseError:
                    # API returned some bogus/none-JSON data,
                    # let’s try again later
                    continue

                if self.shutdown.is_set():
                    break

            # once no incomplete user profiles remain,
            # wait for ten minutes before trying again;
            # wake up every 1/10 sec to check whether we
            # should shut down
            for _ in range(10 * 60 * 10):
                if self.shutdown.is_set():
                    break
                time.sleep(0.1)
            retries += 1
