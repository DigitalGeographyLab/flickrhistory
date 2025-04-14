#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Save a flickr photo to the database."""


import datetime

from .models import License, Photo, Tag
from .engine import Session
from .user_saver import UserSaver


__all__ = ["PhotoSaver"]


class PhotoSaver:
    """Save a flickr photo to the database."""

    def save(data):
        """Save a flickr photo to the database."""
        # the API does not always return all fields
        # we need to figure out which ones we can use

        # and do quite a lot of clean-up because the flickr API
        # also returns fairly weird data, sometimes

        # another side effect is that we can initialise
        # with incomplete data (only id needed),
        # which helps with bad API responses

        # store normalised data in dict
        photo_data = {}

        # "id" is the only field garantueed to be in the data
        # (because we add it ourselves in databaseobjects.py in case parsing fails)
        photo_data["id"] = data["id"]

        # server and secret are kinda straight-forward
        try:
            photo_data["server"] = data["server"]
        except KeyError:
            pass

        try:
            photo_data["secret"] = bytes.fromhex(data["secret"])
        except (ValueError, KeyError):  # some non-hex character
            pass

        try:
            photo_data["title"] = data["title"]
        except KeyError:
            pass

        try:
            photo_data["description"] = data["description"]["_content"]
        except KeyError:
            pass

        # the dates need special attention
        try:
            photo_data["date_taken"] = datetime.datetime.fromisoformat(
                data["datetaken"]
            ).astimezone(datetime.timezone.utc)
        except ValueError:
            # there is weirdly quite a lot of photos with
            # date_taken "0000-01-01 00:00:00"
            # Year 0 does not exist, there’s 1BCE, then 1CE, nothing in between
            photo_data["date_taken"] = None
        except KeyError:
            # field does not exist in the dict we got
            pass

        try:
            photo_data["date_posted"] = datetime.datetime.fromtimestamp(
                int(data["dateupload"]), tz=datetime.timezone.utc
            )
        except KeyError:
            pass

        # geometry
        try:
            longitude = float(data["longitude"])
            latitude = float(data["latitude"])
            assert longitude != 0 and latitude != 0
            photo_data["geom"] = "SRID=4326;POINT({longitude:f} {latitude:f})".format(
                longitude=longitude, latitude=latitude
            )
        except (
            AssertionError,  # lon/lat is at exactly 0°N/S, 0°W/E -> bogus
            KeyError,  # not contained in API dict
            TypeError,  # weird data returned
        ):
            pass

        photo_data["geographical_accuracy"] = int(data["accuracy"])

        license = int(data["license"])

        tags = data["tags"].split()

        with Session() as session, session.begin():

            photo = Photo(**photo_data)

            photo.tags = []
            for tag in tags:
                tag = session.get(Tag, tag) or Tag(tag=tag)
                if tag not in photo.tags:
                    photo.tags.append(tag)

            photo.license = session.get(License, license) or License(name=license)

            user = UserSaver().save(data)
            photo.user = user

            session.merge(photo)
            return photo
