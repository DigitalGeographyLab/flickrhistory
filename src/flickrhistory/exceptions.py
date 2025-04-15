#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Custom exceptions."""


__all__ = ["ApiResponseError", "DownloadBatchIsTooLargeError"]


class ApiResponseError(BaseException):
    """Raised when API returns bogus data."""


class DownloadBatchIsTooLargeError(BaseException):
    """Raised when batch larger than usual flickr download limit."""
