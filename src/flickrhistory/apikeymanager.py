#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Manages API keys (and their rate limit)."""


__all__ = ["ApiKeyManager"]


import contextlib
import queue


from .timeoutlock import TimeoutLock


class ApiKey(TimeoutLock):
    """An API key that manages its own rate limit."""

    def __init__(self, api_key, rate_limit_per_second):
        """
        Initialise an API key.

        Args:
            api_key: API key (mixed)
            rate_limit_per_second: How often this API key
                can be used per second
        """
        super().__init__(timeout=(1.0 / rate_limit_per_second))
        self._api_key = api_key

    def __enter__(self):
        """Return the API key, after timeout if over rate limit."""
        self.acquire()
        return self._api_key


class ApiKeyManager:
    """Manages API keys (and their rate limit)."""

    def __init__(self, api_keys=None, rate_limit_per_second=1.0):
        """Intialize an API key manager."""
        self._api_keys = queue.Queue()
        self.rate_limit_per_second = rate_limit_per_second

        self._has_api_keys = False
        if api_keys is not None:
            for api_key in api_keys:
                self.add_api_key(api_key)

    def add_api_key(self, api_key):
        """Add an API key to the manager."""
        self._api_keys.put(ApiKey(api_key, self.rate_limit_per_second))
        self._has_api_keys = True

    @contextlib.contextmanager
    def get_api_key(self):
        """Retrieve the next available API key."""
        if not self._has_api_keys:
            raise RuntimeError("No API keys configured")

        api_key = self._api_keys.get()
        with api_key as key:
            try:
                yield key
            finally:
                self._api_keys.put(api_key)
