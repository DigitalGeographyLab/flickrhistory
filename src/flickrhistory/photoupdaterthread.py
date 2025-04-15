#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Thread to complete missing data on photos."""


__all__ = ["PhotoUpdaterThread"]


import threading
import time

import sqlalchemy

from .config import Config
from .database import Photo, PhotoSaver, Session
from .exceptions import ApiResponseError
from .photoupdater import PhotoUpdater


class PhotoUpdaterThread(threading.Thread):
    """Finds incomplete photos and downloads missing data from the flickr API."""

    def __init__(self, api_key_manager, partition=None):
        """
        Intialize a PhotoUpdaterThread.

        Args:
            api_key_manager: instance of an ApiKeyManager
            partition (tuple of int): download the n-th of m parts of incomplete photos

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
    def ids_of_photos_without_detailed_information(self):
        """Find ids of incomplete photo profiles."""
        # Find id of incomplete photo records
        # We use geo_accuracy IS NULL
        with Session() as session:
            if self._bounds is None:
                ids_of_photos_without_detailed_information = session.query(
                    Photo.id
                ).filter_by(geo_accuracy=None)
            else:
                bounds = (
                    sqlalchemy.select(
                        sqlalchemy.sql.functions.percentile_disc(self._bounds[0])
                        .within_group(Photo.id)
                        .label("lower"),
                        sqlalchemy.sql.functions.percentile_disc(self._bounds[1])
                        .within_group(Photo.id)
                        .label("upper"),
                    )
                    .select_from(Photo)
                    .filter_by(geo_accuracy=None)
                    .cte()
                )
                ids_of_photos_without_detailed_information = (
                    session.query(Photo.id)
                    .filter_by(geo_accuracy=None)
                    .where(Photo.id.between(bounds.c.lower, bounds.c.upper))
                    .yield_per(1000)
                )

            for (id,) in ids_of_photos_without_detailed_information:
                yield id

    def run(self):
        """Get TimeSpans off todo_queue and download photos."""
        photo_updater = PhotoUpdater(self._api_key_manager)

        while not self.shutdown.is_set():
            for photo_id in self.ids_of_photos_without_detailed_information:
                try:
                    PhotoSaver().save(photo_updater.get_info_for_photo_id(photo_id))
                    self.count += 1

                except ApiResponseError:
                    # API returned some bogus/none-JSON data,
                    # let’s try again later
                    continue

                if self.shutdown.is_set():
                    break

            # once no incomplete photo profiles remain,
            # wait for ten minutes before trying again;
            # wake up every 1/10 sec to check whether we
            # should shut down
            for _ in range(10 * 60 * 10):
                if self.shutdown.is_set():
                    break
                time.sleep(0.1)
