#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Save a flickr user to the database."""


import datetime

from .models import User
from .session import Session


__all__ = ["UserSaver"]


class UserSaver:
    """Save a flickr user to the database."""

    def save(self, data):
        """Save a flickr user to the database."""
        # We accept raw data from two different API endpoints
        # that return different data in different ontologies
        user_data = {}
        if "owner" in data:
            # -> from photos.search
            user_id, farm = data["owner"].split("@N0")

            user_data["name"] = data["ownername"]
        else:
            # from profile.getprofile
            user_id, farm = data["id"].split("@N0")

            data["join_date"] = datetime.datetime.fromtimestamp(
                int(data["join_date"]), tz=datetime.timezone.utc
            )

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
            user = session.get(User, (user_id, farm)) or User(id=user_id, farm=farm)
            user = session.merge(user)
            user.update(**user_data)

            session.flush()
            session.expunge(user)
        return user
