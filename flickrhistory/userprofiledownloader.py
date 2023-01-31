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


"""Download all data covering a time span from the flickr API."""


__all__ = ["UserProfileDownloader"]


import json

import requests
import urllib3

from .exceptions import ApiResponseError


class UserProfileDownloader:
    """Download user profile data from the flickr API."""

    API_ENDPOINT_URL = "https://api.flickr.com/services/rest/"

    def __init__(self, api_key_manager):
        """Intialize an PhotoDownloader."""
        self._api_key_manager = api_key_manager

    def get_profile_for_id_and_farm(self, user_id, farm):
        """Retrieve profile data by user_id and farm identifier."""
        return self.get_profile_for_nsid("@N0".join([user_id, farm]))

    def get_profile_for_nsid(self, nsid):
        """Get profile data by nsid."""
        query = {
            "method": "flickr.profile.getProfile",
            "format": "json",
            "nojsoncallback": 1,
            "user_id": nsid
        }

        params = {}
        with self._api_key_manager.get_api_key() as api_key:
            params["api_key"] = api_key
            params.update(query)

        try:
            with requests.get(
                    self.API_ENDPOINT_URL,
                    params=params
            ) as response:
                results = response.json()
                assert "profile" in results

        except (
            ConnectionError,
            json.decoder.JSONDecodeError,
            requests.exceptions.RequestException,
            urllib3.exceptions.HTTPError,
        ) as exception:
            # API hicups, let’s consider this batch
            # unsuccessful and start over
            raise ApiResponseError(response.text) from exception

        except AssertionError:
            # TODO: implement logging and report the response text + headers
            # if API hicups, return a stub data dict
            results = {
                "profile": {
                    "id": nsid
                }
            }

        return results["profile"]
