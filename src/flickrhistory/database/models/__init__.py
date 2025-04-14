#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""ORM models for flickr entities."""


__all__ = [
    "FlickrPhoto",
    "FlickrUser",
    "License",
    "Photo",
    "User",
    "Tag",
]


import sqlalchemy

from ..engine import engine
from .base import Base
from .database_schema_updater import DatabaseSchemaUpdater
from .license import License
from .photo import FlickrPhoto, Photo
from .tag import Tag
from .user import FlickrUser, User


if sqlalchemy.inspect(engine).has_table(Photo.__table__):  # data exists
    DatabaseSchemaUpdater().update_to_latest()
else:
    Base.metadata.create_all(engine)
    DatabaseSchemaUpdater().set_schema_version(DatabaseSchemaUpdater.LATEST)
