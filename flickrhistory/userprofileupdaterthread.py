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
from .userprofiledownloader import UserProfileDownloader


class UserProfileUpdaterThread(threading.Thread):
    """Finds incomplete user profiles and downloads missing data from the flickr API."""

    def __init__(
            self,
            api_key_manager
    ):
        """
        Intialize a UserProfileUpdateThread.

        Args:
            api_key_manager: instance of an ApiKeyManager

        """
        super().__init__()

        self.count = 0

        self._api_key_manager = api_key_manager

        self.shutdown = threading.Event()

        with Config() as config:
            self._engine = sqlalchemy.create_engine(
                config["database_connection_string"]
            )

    def run(self):
        """Get TimeSpans off todo_queue and download photos."""
        user_profile_downloader = UserProfileDownloader(self._api_key_manager)

        while not self.shutdown.is_set():

            # Find nsid of incomplete user profiles
            # We use first_name IS NULL, because after
            # updating a profile it will be "", so NULL is
            # a good way of finding “new” profiles
            with sqlalchemy.orm.Session(self._engine) as session:
                nsids_of_users_without_detailed_information = session.execute(
                    sqlalchemy.select(FlickrUser.nsid)
                    .filter_by(first_name=None)
                ).scalars()

            for nsid in nsids_of_users_without_detailed_information:
                with session.begin():
                    flickr_user = (
                        FlickrUser.from_raw_api_data_flickrprofilegetprofile(
                            user_profile_downloader.get_profile_for_nsid(nsid)
                        )
                    )
                    session.merge(flickr_user)

                self.count += 1

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
