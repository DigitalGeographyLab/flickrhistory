#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Update the list of licenses."""


__all__ = ["LicenseDownloader"]


import json

import requests
import urllib3

from .database import License, Session
from .exceptions import ApiResponseError


class LicenseDownloader:
    """Update the list of licenses."""

    API_ENDPOINT_URL = "https://api.flickr.com/services/rest/"

    def __init__(self, api_key_manager):
        """Update the list of licenses."""
        self._api_key_manager = api_key_manager

    def update_licenses(self):
        """Update the list of licenses."""
        query = {
            "method": "flickr.photos.licenses.getInfo",
            "format": "json",
            "nojsoncallback": True,
        }

        with self._api_key_manager.get_api_key() as api_key:
            params = {"api_key": api_key}
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
                raise ApiResponseError() from exception

        with Session() as session, session.begin():
            for license in results["licenses"]["license"]:
                license_id = license["id"]
                license_name = license["name"]
                license_url = license["url"]
                license = session.get(License, license_id) or License(
                    id=license_id,
                    name=license_name,
                    url=license_url,
                )
                session.merge(license)
