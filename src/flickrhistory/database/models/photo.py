#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""ORM class to represent a flickr photo."""


__all__ = [
    "Photo",
]


import geoalchemy2
import sqlalchemy
import sqlalchemy.orm

from .base import Base


class Photo(Base):
    """ORM class to represent a flickr photo (posts)."""

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
        ),
    )
    page_url = sqlalchemy.Column(
        sqlalchemy.Text,
        sqlalchemy.Computed(
            "'https://www.flickr.com/photos/' || "
            + "user_id::TEXT || '@N0' || user_farm::TEXT || '/' || "
            + "id::TEXT || '/'"
        ),
    )

    geom = sqlalchemy.Column(geoalchemy2.Geometry("POINT", 4326))
    geo_accuracy = sqlalchemy.Column(sqlalchemy.SmallInteger)

    user_id = sqlalchemy.Column(sqlalchemy.BigInteger, nullable=False)
    user_farm = sqlalchemy.Column(sqlalchemy.SmallInteger, nullable=False)

    tags = sqlalchemy.orm.relationship(
        "Tag",
        secondary="tag_photo_associations",
        back_populates="photos",
    )

    license_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("licenses.id"),
        index=True,
    )
    license = sqlalchemy.orm.relationship("License", back_populates="photos")

    user = sqlalchemy.orm.relationship("User", back_populates="photos")

    __table_args__ = (
        sqlalchemy.ForeignKeyConstraint(
            ["user_id", "user_farm"], ["users.id", "users.farm"], "User"
        ),
    )

    @sqlalchemy.orm.validates("title", "description")
    def _drop_nul_from_strings(self, key, address):
        return address.replace("\x00", "")
