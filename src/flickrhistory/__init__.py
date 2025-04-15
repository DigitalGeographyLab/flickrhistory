#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Download a complete history of georeferenced flickr posts."""


__all__ = [
    "FlickrHistoryDownloader",
    "__version__",
]

try:
    from .flickrhistorydownloader import FlickrHistoryDownloader
except ImportError:
    pass

__version__ = "0.3.0"
