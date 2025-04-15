#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""ORM models for flickr entities."""


__all__ = [
    "License",
    "Photo",
    "User",
    "Tag",
]


from .license import License
from .photo import Photo
from .tag import Tag
from .user import User
