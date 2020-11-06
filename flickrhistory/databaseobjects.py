#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2019 Christoph Fink, University of Helsinki
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

"""Base classes to represent flickr posts and users."""


__all__ = [
    "FlickrPhoto",
    "FlickrUser"
]


import datetime

import geoalchemy2
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.ext.hybrid
import sqlalchemy.orm

from .config import Config


Base = sqlalchemy.ext.declarative.declarative_base()
config = Config()


class FlickrUser(Base):
    """ORM class to represent a flickr user."""

    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.BigInteger)
    farm = sqlalchemy.Column(sqlalchemy.SmallInteger)
    nsid = sqlalchemy.Column(
        sqlalchemy.Text,
        sqlalchemy.Computed("id::TEXT || '@N0' || farm::TEXT")
    )

    name = sqlalchemy.Column(sqlalchemy.Text)
    first_name = sqlalchemy.Column(sqlalchemy.Text)
    last_name = sqlalchemy.Column(sqlalchemy.Text)
    real_name = sqlalchemy.Column(
        sqlalchemy.Text,
        sqlalchemy.Computed("first_name || ' ' || last_name")
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

    photos = sqlalchemy.orm.relationship("FlickrPhoto", back_populates="user")

    __table_args__ = (
        sqlalchemy.PrimaryKeyConstraint("id", "farm"),
    )

    @classmethod
    def from_raw_api_data_flickrphotossearch(cls, data):
        """Initialise a new FlickrUser with a flickr.photos.search data dict."""
        user_id, farm = data["owner"].split("@N0")
        user_data = {
            "id": user_id,
            "farm": farm,
            "name": data["ownername"]
        }
        return cls(**user_data)

    @classmethod
    def from_raw_api_data_flickrprofilegetprofile(cls, data):
        """Initialise a new FlickrUser with a flickr.profile.getProfile data dict."""
        user_id, farm = data["id"].split("@N0")
        join_date = datetime.datetime.fromtimestamp(
            int(data["join_date"]),
            tz=datetime.timezone.utc
        )

        user_data = {
            "id": user_id,
            "farm": farm,

            "join_date": join_date
        }

        # the API does not always return all fields
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
            "pinterest"
        ]:
            try:
                user_data[field] = data[field]
            except KeyError:
                pass

        return cls(**user_data)

    def __str__(self):
        """Return a str representation."""
        return "<FlickrUser({:s}@N0{:s})>".format(self.id, self.farm)

    def __repr(self):
        """Return a str representation."""
        return str(self)


class FlickrPhoto(Base):
    """ORM class to represent a flickr photo (posts)."""

    __tablename__ = "photos"

    id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True)

    server = sqlalchemy.Column(sqlalchemy.Integer)
    secret = sqlalchemy.Column(sqlalchemy.LargeBinary)

    title = sqlalchemy.Column(sqlalchemy.Text)
    description = sqlalchemy.Column(sqlalchemy.Text)

    date_taken = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))
    date_posted = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))

    photo_url = sqlalchemy.Column(
        sqlalchemy.Text,
        sqlalchemy.Computed(
            "'https://live.staticflickr.com/' || server::TEXT || '/' || "
            + "id::TEXT || '_' || encode(secret, 'hex') || '_z.jpg'"
        )
    )
    page_url = sqlalchemy.Column(
        sqlalchemy.Text,
        sqlalchemy.Computed(
            "'https://www.flickr.com/photos/' || "
            + "user_id::TEXT || '@N0' || user_farm::TEXT || '/' || "
            + "id::TEXT || '/'"
        )
    )

    geom = sqlalchemy.Column(geoalchemy2.Geometry("POINT", 4326))

    user_id = sqlalchemy.Column(sqlalchemy.BigInteger, nullable=False)
    user_farm = sqlalchemy.Column(sqlalchemy.SmallInteger, nullable=False)

    user = sqlalchemy.orm.relationship("FlickrUser", back_populates="photos")

    __table_args__ = (
        sqlalchemy.ForeignKeyConstraint(
            ["user_id", "user_farm"],
            ["users.id", "users.farm"],
            "FlickrUser"
        ),
    )

    @classmethod
    def from_raw_api_data_flickrphotossearch(cls, data):
        """Initialise a new FlickrPhoto with a flickr.photos.search data dict."""
        if data["datetakenunknown"] == "0":
            date_taken = None
        else:
            try:
                date_taken = datetime.datetime.fromisoformat(
                    data["datetaken"]
                ).astimezone(datetime.timezone.utc)
            except ValueError:
                # there is weirdly quite a lot of photos with
                # date_taken "0000-01-01 00:00:00"
                # Year 0 does not exist, there’s 1BCE, then 1CE, nothing in between
                date_taken = None

        date_posted = datetime.datetime.fromtimestamp(
            int(data["dateupload"]),
            tz=datetime.timezone.utc
        )

        try:
            longitude = float(data["longitude"])
            latitude = float(data["latitude"])
            assert longitude != 0 and latitude != 0
            geom = "SRID=4326;POINT({longitude:f} {latitude:f})".format(
                longitude=longitude,
                latitude=latitude
            )
        except (TypeError, AssertionError):
            geom = None

        photo_data = {
            "id": data["id"],

            "server": data["server"],
            "secret": bytes.fromhex(data["secret"]),

            "title": data["title"],
            "description": data["description"]["_content"],

            "date_taken": date_taken,
            "date_posted": date_posted,

            "geom": geom,

            "user": FlickrUser.from_raw_api_data_flickrphotossearch(data)
        }

        return cls(**photo_data)

    def __str__(self):
        """Return a str representation."""
        return "<FlickrPhoto({:s})>".format(self.id)

    def __repr(self):
        """Return a str representation."""
        return str(self)


# Create tables in case we know where
if "database_connection_string" in config:
    engine = sqlalchemy.create_engine(config["database_connection_string"])
    Base.metadata.create_all(engine)
