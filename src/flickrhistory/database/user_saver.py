#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Save a flickr user to the database."""


import datetime

from .models import User
from .engine import Session


__all__ = ["UserSaver"]


class UserSaver:
    """Save a flickr user to the database."""

    def save(data):
        """Save a flickr user to the database."""
        # the API does not always return all fields

        # "id" is the only field garantueed to be in the data
        user_id, farm = data["id"].split("@N0")
        user_data = {}

        # "joindate" and "ownername" need special attentation
        try:
            data["join_date"] = datetime.datetime.fromtimestamp(
                int(data["join_date"]), tz=datetime.timezone.utc
            )
        except KeyError:
            pass
        try:
            data["name"] = data["ownername"]
        except KeyError:
            pass

        # all the other fields can be added as they are (if they exist)
        for field in [
            "first_name",
            "last_name",
            "name",
            "join_date",
            "city",
            "country",
            "hometown",
            "occupation",
            "description",
            "website",
            "facebook",
            "twitter",
            "tumblr",
            "instagram",
            "pinterest",
        ]:
            try:
                user_data[field] = data[field]
            except KeyError:
                pass

        with Session() as session, session.begin():
            user = User(**user_data)
            session.merge(user)
            return user
