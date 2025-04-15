#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Update the database schema if necessary."""


__all__ = ["DatabaseSchemaUpdater"]


import sys

import sqlalchemy

from ..config import Config


# for now, schema updates are SQL only and work on PostgreSQL, only.
# GeoAlchemy2 doesn’t really support SQLite, anyway
SCHEMA_UPDATES = {
    # 0 -> 1
    1: """
        ALTER TABLE
            photos
        ADD COLUMN IF NOT EXISTS
            geo_accuracy SMALLINT;

        CREATE TABLE IF NOT EXISTS
            licenses (
                id INTEGER,
                name TEXT,
                url TEXT
            );

        ALTER TABLE
            photos
        ADD COLUMN IF NOT EXISTS
            license INTEGER REFERENCES licenses(id);
    """,
}


class DatabaseSchemaUpdater:
    """Update the database schema if necessary."""

    LATEST = "LATEST"  # ‘magic’, see def set_schema_version

    def __init__(self):
        """Update the database schema if necessary."""
        # Try to create database table for schema version
        with Config() as config:
            self.engine = sqlalchemy.create_engine(config["database_connection_string"])
        with self.engine.begin() as connection:
            connection.execute(
                sqlalchemy.text(
                    """
                        CREATE TABLE IF NOT EXISTS
                            schema_versions
                            (
                                update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                                version INTEGER PRIMARY KEY
                            );
                    """
                )
            )

    @property
    def installed_version(self):
        """Return current version."""
        with self.engine.connect() as connection:
            installed_version = connection.execute(
                sqlalchemy.text(
                    """
                        SELECT
                            COALESCE(
                                MAX(version),
                                0
                            ) AS version
                        FROM
                            schema_versions;
                    """
                )
            ).scalar_one_or_none()
        return installed_version

    def update_to_latest(self):
        """Update to the latest schema version."""
        installed_version = self.installed_version
        while installed_version < max(SCHEMA_UPDATES.keys()):
            print(
                "Updating database schema (db version {:d}->{:d})".format(
                    installed_version, installed_version + 1
                ),
                file=sys.stderr,
                flush=True,  # so that we don’t seem without work
            )
            with self.engine.connect() as connection:
                next_version = self.installed_version + 1
                connection.execute(sqlalchemy.text(SCHEMA_UPDATES[next_version]))
                self.set_schema_version(next_version)
            installed_version = self.installed_version

    def set_schema_version(self, version):
        """Set the schema version (without running update scripts)."""
        if version == self.LATEST:
            version = max(SCHEMA_UPDATES.keys())
        with self.engine.begin() as connection:
            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO
                        schema_versions (version)
                    VALUES (
                        :version
                    );
                """
                ),
                {"version": version},
            )
