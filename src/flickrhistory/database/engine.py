#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""An SQLAlchemy engine and sessionmaker."""


__all__ = ["engine", "Session"]


import sqlalchemy
import sqlalchemy.orm

from ..config import Config


with Config() as config:
    engine = sqlalchemy.create_engine(config["database_connection_string"])


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
