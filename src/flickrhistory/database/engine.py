#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""An SQLAlchemy engine and sessionmaker."""


__all__ = ["engine", "Session"]


import multiprocessing

import sqlalchemy
import sqlalchemy.orm

from ..config import Config


POOL_SIZE = multiprocessing.cpu_count() * 10


with Config() as config:
    engine = sqlalchemy.create_engine(
        config["database_connection_string"],
        pool_size=POOL_SIZE,
        max_overflow=POOL_SIZE,
    )


if engine.dialect.name == "postgresql":
    with engine.connect() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                CREATE EXTENSION IF NOT EXISTS
                    postgis;
                """
            )
        )


Session = sqlalchemy.orm.sessionmaker(engine, autoflush=False)
