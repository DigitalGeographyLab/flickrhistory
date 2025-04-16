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
        CREATE TABLE licenses (
            id integer NOT NULL,
            name text,
            url text
        );

        CREATE SEQUENCE licenses_id_seq
            AS integer
            START WITH 1
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;

        ALTER SEQUENCE licenses_id_seq OWNED BY licenses.id;

        ALTER TABLE ONLY photos ADD COLUMN geo_accuracy SMALLINT, ADD COLUMN license_id INTEGER;

        CREATE TABLE tag_photo_associations (
            tag_tag text NOT NULL,
            photo_id bigint NOT NULL
        );

        CREATE TABLE tags (
            tag text NOT NULL
        );

        ALTER TABLE ONLY licenses ALTER COLUMN id SET DEFAULT nextval('licenses_id_seq'::regclass);

        ALTER TABLE ONLY licenses
            ADD CONSTRAINT licenses_pkey PRIMARY KEY (id);

        ALTER TABLE ONLY tag_photo_associations
            ADD CONSTRAINT tag_photo_associations_pkey PRIMARY KEY (tag_tag, photo_id);

        ALTER TABLE ONLY tags
            ADD CONSTRAINT tags_pkey PRIMARY KEY (tag);

        CREATE INDEX ix_photos_license_id ON photos USING btree (license_id);

        ALTER TABLE ONLY photos RENAME CONSTRAINT "FlickrUser" TO "User";

        ALTER TABLE ONLY photos ADD CONSTRAINT photos_license_id_fkey FOREIGN KEY (license_id) REFERENCES licenses(id);

        ALTER TABLE ONLY tag_photo_associations
            ADD CONSTRAINT tag_photo_associations_photo_id_fkey FOREIGN KEY (photo_id) REFERENCES photos(id);

        ALTER TABLE ONLY tag_photo_associations
            ADD CONSTRAINT tag_photo_associations_tag_tag_fkey FOREIGN KEY (tag_tag) REFERENCES tags(tag);
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
            with self.engine.begin() as connection:
                next_version = self.installed_version + 1
                connection.execute(sqlalchemy.text(SCHEMA_UPDATES[next_version]))
                connection.commit()
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
