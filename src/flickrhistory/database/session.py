#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""An SQLAlchemy sessionmaker."""


__all__ = ["Session"]


import multiprocessing

import sqlalchemy
import sqlalchemy.orm

from ..config import Config
from .databaseschemaupdater import DatabaseSchemaUpdater
from .models import Photo
from .models.base import Base


POOL_SIZE = multiprocessing.cpu_count() * 10


class Session:
    """An sqlachemy.Session."""

    _sessionmaker = None

    def __new__(cls, *args, **kwargs):
        """Return an sqlachemy.Session."""
        if cls._sessionmaker is None:
            with Config() as config:
                engine = sqlalchemy.create_engine(
                    config["database_connection_string"],
                    pool_size=POOL_SIZE,
                    max_overflow=POOL_SIZE,
                )

            with engine.begin() as connection:
                connection.execute(
                    sqlalchemy.text(
                        """
                        CREATE EXTENSION IF NOT EXISTS
                            postgis;
                        """
                    )
                )

            if sqlalchemy.inspect(engine).has_table(Photo.__table__.name):  # data exist
                DatabaseSchemaUpdater().update_to_latest()
            else:
                Base.metadata.create_all(engine)
                DatabaseSchemaUpdater().set_schema_version(DatabaseSchemaUpdater.LATEST)

            cls._sessionmaker = sqlalchemy.orm.sessionmaker(engine, autoflush=False)
        return cls._sessionmaker()
