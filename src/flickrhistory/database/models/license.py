#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""ORM class to represent a flickr license."""


__all__ = ["License"]


import sqlalchemy
import sqlalchemy.orm

from .base import Base


class License(Base):
    """ORM class to represent a flickr license."""

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.Text)
    url = sqlalchemy.Column(sqlalchemy.Text)
    photos = sqlalchemy.orm.relationship("Photo")
