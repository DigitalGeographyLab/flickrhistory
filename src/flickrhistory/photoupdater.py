#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Download all data covering a time span from the flickr API."""


__all__ = ["PhotoUpdater"]


import json

import requests
import urllib3

from .exceptions import ApiResponseError


class PhotoUpdater:
    """
    Download photo data from the flickr API.

    Photo data downloaded with flickrhistory<0.3.0 do not contain information on
    geo accuracy, license, tags. This re-fetches that information.
    """

    API_ENDPOINT_URL = "https://api.flickr.com/services/rest/"

    def __init__(self, api_key_manager):
        """Intialize an PhotoUpdater."""
        self._api_key_manager = api_key_manager

    def get_info_for_photo_id(self, photo_id):
        """Get profile data by photo_id."""
        query = {
            "method": "flickr.photos.getInfo",
            "format": "json",
            "nojsoncallback": True,
            "photo_id": photo_id,
        }

        params = {}
        with self._api_key_manager.get_api_key() as api_key:
            params["api_key"] = api_key
            params.update(query)

        try:
            with requests.get(self.API_ENDPOINT_URL, params=params) as response:
                results = response.json()
                assert "photo" in results

                data = {
                    "id": photo_id,
                    "tags": " ".join(
                        [tag["_content"] for tag in results["photo"]["tags"]["tag"]]
                    ),
                    "license": int(results["photo"]["license"]),
                    "accuracy": int(results["photo"]["location"]["accuracy"]),
                    "owner": results["photo"]["owner"]["nsid"],
                    "ownername": results["photo"]["owner"]["realname"],
                }

        except (
            ConnectionError,
            json.decoder.JSONDecodeError,
            requests.exceptions.RequestException,
            urllib3.exceptions.HTTPError,
        ) as exception:
            # API hicups, let’s consider this batch
            # unsuccessful and start over
            raise ApiResponseError() from exception

        except AssertionError:
            # if API hicups, return a stub data dict
            data = {"id": photo_id}

        return data
