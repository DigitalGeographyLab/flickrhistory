#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""A common sqlalchemy declarative_base() to share between models."""


__all__ = ["Base"]


import json
import re

import sqlalchemy.ext.declarative
import sqlalchemy.orm

from ...config import Config


CAMEL_CASE_TO_SNAKE_CASE_RE = re.compile(
    "((?<=[a-z0-9])[A-Z]|(?!^)(?<!_)[A-Z](?=[a-z]))"
)


def camel_case_to_snake_case(camel_case):
    """Convert a `camelCase` string to `snake_case`."""
    snake_case = CAMEL_CASE_TO_SNAKE_CASE_RE.sub(r"_\1", camel_case).lower()
    return snake_case


class Base:
    """Template for sqlalchemy declarative_base() to add shared functionality."""

    def __str__(self):
        """Return a str representation."""
        primary_keys = {}
        for pk in self.__mapper__.primary_key:
            try:
                primary_keys[pk.name] = getattr(self, pk.name)
            except AttributeError:  # (not yet set)
                pass
        return "{}({})".format(self.__class__.__name__, json.dumps(primary_keys))

    @staticmethod
    def pseudonymise_identifiers():
        """Pseudonymise identifiers?."""
        pseudonymise_identifiers = True
        try:
            with Config() as config:
                if config["pseudonymise"] is False:
                    pseudonymise_identifiers = False
        except KeyError:
            pass
        return pseudonymise_identifiers

    @sqlalchemy.orm.declared_attr
    def __tablename__(cls):
        """Return a table name derived from the class name."""
        snake_case = camel_case_to_snake_case(cls.__name__)
        return "{:s}s".format(snake_case)


Base = sqlalchemy.ext.declarative.declarative_base(cls=Base)
