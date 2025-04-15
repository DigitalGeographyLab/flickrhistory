#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Thread to complete missing data on user profiles."""


__all__ = ["UserProfileUpdaterThread"]


import threading
import time

import sqlalchemy

from .config import Config
from .database import User, UserSaver
from .exceptions import ApiResponseError
from .userprofiledownloader import UserProfileDownloader


class UserProfileUpdaterThread(threading.Thread):
    """Finds incomplete user profiles and downloads missing data from the flickr API."""

    def __init__(self, api_key_manager, partition=None):
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
                part * 1.0 / number_of_partitions,
            )
        except (AssertionError, TypeError):
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
                nsids_of_users_without_detailed_information = session.query(
                    User.nsid
                ).filter_by(join_date=None)
            else:
                bounds = (
                    sqlalchemy.select(
                        sqlalchemy.sql.functions.percentile_disc(self._bounds[0])
                        .within_group(User.id)
                        .label("lower"),
                        sqlalchemy.sql.functions.percentile_disc(self._bounds[1])
                        .within_group(User.id)
                        .label("upper"),
                    )
                    .select_from(User)
                    .filter_by(join_date=None)
                    .cte()
                )
                nsids_of_users_without_detailed_information = (
                    session.query(User.nsid)
                    .filter_by(join_date=None)
                    .where(User.id.between(bounds.c.lower, bounds.c.upper))
                    .yield_per(1000)
                )

            for (nsid,) in nsids_of_users_without_detailed_information:
                yield nsid

    def run(self):
        """Get TimeSpans off todo_queue and download photos."""
        user_profile_downloader = UserProfileDownloader(self._api_key_manager)

        while not self.shutdown.is_set():
            for nsid in self.nsids_of_users_without_detailed_information:
                try:
                    UserSaver().save(user_profile_downloader.get_profile_for_nsid(nsid))
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
