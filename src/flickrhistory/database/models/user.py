#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""ORM class to represent a flickr user."""


__all__ = ["User"]


import datetime

import sqlalchemy
import sqlalchemy.orm

from .base import Base


class User(Base):
    """ORM class to represent a flickr user."""

    id = sqlalchemy.Column(sqlalchemy.BigInteger)
    farm = sqlalchemy.Column(sqlalchemy.SmallInteger)
    nsid = sqlalchemy.Column(
        sqlalchemy.Text, sqlalchemy.Computed("id::TEXT || '@N0' || farm::TEXT")
    )

    name = sqlalchemy.Column(sqlalchemy.Text)
    first_name = sqlalchemy.Column(sqlalchemy.Text)
    last_name = sqlalchemy.Column(sqlalchemy.Text)
    real_name = sqlalchemy.Column(
        sqlalchemy.Text, sqlalchemy.Computed("first_name || ' ' || last_name")
    )

    city = sqlalchemy.Column(sqlalchemy.Text)
    country = sqlalchemy.Column(sqlalchemy.Text)
    hometown = sqlalchemy.Column(sqlalchemy.Text)

    occupation = sqlalchemy.Column(sqlalchemy.Text)
    description = sqlalchemy.Column(sqlalchemy.Text)

    join_date = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))

    website = sqlalchemy.Column(sqlalchemy.Text)
    facebook = sqlalchemy.Column(sqlalchemy.Text)
    twitter = sqlalchemy.Column(sqlalchemy.Text)
    tumblr = sqlalchemy.Column(sqlalchemy.Text)
    instagram = sqlalchemy.Column(sqlalchemy.Text)
    pinterest = sqlalchemy.Column(sqlalchemy.Text)

    photos = sqlalchemy.orm.relationship("Photo", back_populates="user")

    __table_args__ = (sqlalchemy.PrimaryKeyConstraint("id", "farm"),)

    @classmethod
    def from_raw_api_data_flickrphotossearch(cls, data):
        """Initialise a new User with a flickr.photos.search data dict."""
        user_id, farm = data["owner"].split("@N0")
        user_data = {"id": user_id, "farm": farm, "name": data["ownername"]}
        return cls(**user_data)

    @classmethod
    def from_raw_api_data_flickrprofilegetprofile(cls, data):
        """Initialise a new User with a flickr.profile.getProfile data dict."""
        # the API does not always return all fields

        # "id" is the only field garantueed to be in the data
        # (because we add it ourselves in databaseobjects.py in case parsing fails)
        user_id, farm = data["id"].split("@N0")

        # "joindate" needs special attentation
        try:
            join_date = datetime.datetime.fromtimestamp(
                int(data["join_date"]), tz=datetime.timezone.utc
            )
        except KeyError:
            join_date = None

        user_data = {"id": user_id, "farm": farm, "join_date": join_date}

        # all the other fields can be added as they are (if they exist)
        for field in [
            "first_name",
            "last_name",
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

        return cls(**user_data)
