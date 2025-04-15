#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Download all data covering a time span from the flickr API."""


__all__ = ["PhotoDownloader"]


import datetime
import json

import requests
import urllib3

from .exceptions import ApiResponseError, DownloadBatchIsTooLargeError


MAX_PHOTOS_PER_BATCH = 3000
ONE_SECOND = datetime.timedelta(seconds=1)


class PhotoDownloader:
    """Download all data covering a time span from the flickr API."""

    API_ENDPOINT_URL = "https://api.flickr.com/services/rest/"

    def __init__(self, timespan, api_key_manager):
        """Intialize an PhotoDownloader."""
        self._timespan = timespan
        self._api_key_manager = api_key_manager

    @property
    def photos(self):
        """Iterate over downloaded photos."""
        query = {
            "method": "flickr.photos.search",
            "format": "json",
            "nojsoncallback": 1,
            "per_page": 500,
            "has_geo": 1,
            "extras": ", ".join(
                [
                    "description",
                    "date_upload",
                    "date_taken",
                    "geo",
                    "owner_name",
                    "tags",
                    "license",
                ]
            ),
            "min_upload_date": self._timespan.start.timestamp(),
            "max_upload_date": self._timespan.end.timestamp(),
            "sort": "date-posted-asc",
        }

        page = 1

        while True:
            query["page"] = page
            params = {}
            with self._api_key_manager.get_api_key() as api_key:
                params["api_key"] = api_key
                params.update(query)

                try:
                    with requests.get(self.API_ENDPOINT_URL, params=params) as response:
                        results = response.json()
                except (
                    ConnectionError,
                    json.decoder.JSONDecodeError,
                    requests.exceptions.RequestException,
                    urllib3.exceptions.HTTPError,
                ) as exception:
                    # API hicups, let’s consider this batch
                    # unsuccessful and start over
                    raise ApiResponseError() from exception

            try:
                try:
                    num_photos = int(results["photos"]["total"])
                except TypeError:
                    num_photos = 0

                if (
                    num_photos > MAX_PHOTOS_PER_BATCH
                    and self._timespan.duration > ONE_SECOND
                ):
                    raise DownloadBatchIsTooLargeError(
                        f"More than {MAX_PHOTOS_PER_BATCH} rows returned ({num_photos}), "
                        "please specify a shorter time span."
                    )

                for photo in results["photos"]["photo"]:
                    # the flickr API is matching date_posted very fuzzily,
                    # let’s not waste time with duplicates
                    if (
                        datetime.datetime.fromtimestamp(
                            int(photo["dateupload"]), tz=datetime.timezone.utc
                        )
                        > self._timespan.end
                    ):
                        continue

                    yield photo

            except KeyError:
                pass  # moving on to next page, if exists

            page += 1
            if page > int(results["photos"]["pages"]):
                break
