#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  Copyright (C) 2018 Christoph Fink, University of Helsinki
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses/>.


"""An exception to handle receiving SIGTERM signals."""


__all__ = ["SigTermReceivedException"]


import signal


class SigTermReceivedException(Exception):
    """Raised when SIGTERM signal received."""


def _received_sig_term(*args):
    raise SigTermReceivedException


signal.signal(signal.SIGTERM, _received_sig_term)
