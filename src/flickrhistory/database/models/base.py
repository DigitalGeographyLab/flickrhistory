#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""A common sqlalchemy declarative_base() to share between models."""


__all__ = ["Base"]


import json
import re

import sqlalchemy.ext.declarative
import sqlalchemy.orm


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
        return f"<{self.__class__.__name__}({json.dumps(primary_keys)})>"

    @sqlalchemy.orm.declared_attr
    def __tablename__(cls):
        """Return a table name derived from the class name."""
        snake_case = camel_case_to_snake_case(cls.__name__)
        return f"{snake_case}s"

    def update(self, **kwargs):
        """Update the values of this ORM object from keyword arguments."""
        for key, value in kwargs.items():
            setattr(self, key, value)


Base = sqlalchemy.ext.declarative.declarative_base(cls=Base)
