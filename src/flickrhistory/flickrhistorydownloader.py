#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Download (all) georeferenced flickr posts."""


__all__ = ["FlickrHistoryDownloader"]


import blessed

from .basicflickrhistorydownloader import BasicFlickrHistoryDownloader
from .fancyflickrhistorydownloader import FancyFlickrHistoryDownloader


class FlickrHistoryDownloader:
    """Download (all) georeferenced flickr posts."""

    def __new__(cls, *args, **kwargs):
        """Create a new FlickrHistoryDownloader (dep. on terminal’s capabilities)."""
        if blessed.Terminal().does_styling:
            _cls = FancyFlickrHistoryDownloader
        else:
            _cls = BasicFlickrHistoryDownloader

        instance = _cls.__new__(_cls, *args, **kwargs)
        instance.__init__(*args, **kwargs)
        return instance
