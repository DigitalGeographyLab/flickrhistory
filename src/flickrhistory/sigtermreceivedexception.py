#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""An exception to handle receiving SIGTERM signals."""


__all__ = ["SigTermReceivedException"]


import signal


class SigTermReceivedException(Exception):
    """Raised when SIGTERM signal received."""


def _received_sig_term(*args):
    raise SigTermReceivedException


signal.signal(signal.SIGTERM, _received_sig_term)
