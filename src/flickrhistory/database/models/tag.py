#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""ORM class to represent a flickr tag."""


__all__ = ["Tag"]


import sqlalchemy
import sqlalchemy.orm

from .base import Base


class Tag(Base):
    """ORM class to represent a flickr tag."""

    tag = sqlalchemy.Column(sqlalchemy.Text, primary_key=True)
    photos = sqlalchemy.orm.relationship(
        "Photo",
        secondary="tag_photo_associations",
        back_populates="tags",
    )


class TagPhotoAssociation(Base):
    """A many-to-many relation table between tags and photos."""

    tag_tag = sqlalchemy.Column(
        sqlalchemy.Text,
        sqlalchemy.ForeignKey("tags.tag"),
        primary_key=True,
    )
    photo_id = sqlalchemy.Column(
        sqlalchemy.BigInteger,
        sqlalchemy.ForeignKey("photos.id"),
        primary_key=True,
    )
