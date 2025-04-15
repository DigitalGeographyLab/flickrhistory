#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Download a complete history of georeferenced flickr posts."""


from .flickrhistorydownloader import FlickrHistoryDownloader


def main():
    """Download a complete history of georeferenced flickr posts."""
    FlickrHistoryDownloader().download()


if __name__ == "__main__":
    main()
