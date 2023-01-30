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
        # the API does not always return all fields

        # "id" is the only field garantueed to be in the data
        # (because we add it ourselves in databaseobjects.py in case parsing fails)
        user_id, farm = data["id"].split("@N0")

        # "joindate" needs special attentation
        try:
            join_date = datetime.datetime.fromtimestamp(
                int(data["join_date"]),
                tz=datetime.timezone.utc
            )
        except KeyError:
            join_date = None

        user_data = {
            "id": user_id,
            "farm": farm,

            "join_date": join_date
        }

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
        # the API does not always return all fields
        # we need to figure out which ones we can use

        # and do quite a lot of clean-up because the flickr API
        # also returns fairly weird data, sometimes

        # another side effect is that we can initialise
        # with incomplete data (only id needed),
        # which helps with bad API responses

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
        except (
            ValueError,  # some non-hex character
            KeyError
        ):
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
                int(data["dateupload"]),
                tz=datetime.timezone.utc
            )
        except KeyError:
            pass

        # geometry
        try:
            longitude = float(data["longitude"])
            latitude = float(data["latitude"])
            assert longitude != 0 and latitude != 0
            photo_data["geom"] = "SRID=4326;POINT({longitude:f} {latitude:f})".format(
                longitude=longitude,
                latitude=latitude
            )
        except (
            AssertionError,  # lon/lat is at exactly 0°N/S, 0°W/E -> bogus
            KeyError,        # not contained in API dict
            TypeError        # weird data returned
        ):
            pass

        # finally, the user
        # (let’s just delegate that to the FlickrUser constructor)
        photo_data["user"] = FlickrUser.from_raw_api_data_flickrphotossearch(data)

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
