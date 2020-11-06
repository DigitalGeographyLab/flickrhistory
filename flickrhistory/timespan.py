#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright (C) 2020 Christoph Fink, University of Helsinki
#
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 3
#   of the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, see <http://www.gnu.org/licenses/>.


"""A period in time starting at a datetime and ending at another datetime."""


__all__ = [
    "TimeSpan"
]


import datetime

import yaml


class TimeSpan(yaml.YAMLObject):
    """A period in time starting at a datetime and ending at another datetime."""

    def __init__(
            self,
            start,
            end
    ):
        """Initialise a new TimeSpan object."""
        self.start = start
        self.end = end

    def __str__(self):
        """Return a string representation of this TimeSpan."""
        return (
            "<{:s}"
            + "({:%Y-%m-%dT%H:%M:%S.000Z}-{:%Y-%m-%dT%H:%M:%S.000Z})>"
        ).format(
            self.__class__.__name__,
            self.start,
            self.end
        )

    def __repr__(self):
        """Represent this TimeSpan in readable form."""
        return self.__str__()

    @property
    def start(self):
        """Return the start time of this time span."""
        return self._start

    @start.setter
    def start(self, start):
        if not isinstance(start, datetime.datetime):
            raise TypeError("Expected datetime.datetime")
        self._start = start

    @property
    def end(self):
        """Return the end time of this time span."""
        return self._end

    @end.setter
    def end(self, end):
        if not isinstance(end, datetime.datetime):
            raise TypeError("Expected datetime.datetime")
        self._end = end

    @property
    def duration(self):
        """Compute the time between TimeSpan.start and TimeSpan.end."""
        return self._end - self.start

    def __lt__(self, other):
        """Test if this TimeSpan starts earlier than another one."""
        return self.start < other.start

    def __gt__(self, other):
        """Test if this TimeSpan ends later than another one."""
        return self.end > other.end

    def __eq__(self, other):
        """Test if this TimeSpan and another one are equal."""
        return (
            self.start == other.start
            and self.end == other.end
        )

    def __add__(self, other):
        """Add another TimeSpan to this one."""
        if not isinstance(other, list):
            other = [other]

        # “recursively” merge all time spans in list
        not_yet_merged = sorted(other + [self])
        merged = [not_yet_merged.pop(0)]

        while not_yet_merged:
            # pop last member of merged time spans
            # and first one of still to be merged time spans
            last = merged.pop()
            new = not_yet_merged.pop(0)

            # check for overlap of the two,
            # then add one or two items to the merged list
            if last.end >= new.start:
                merged.append(
                    TimeSpan(
                        min(last.start, new.start),
                        max(last.end, new.end)
                    )
                )
            else:
                merged += [last, new]

        return merged

    def __radd__(self, other):
        """Add this TimeSpan to another one."""
        if other == 0:  # default case for calling `sum()`
            return self
        return self.__add__(other)

    def __truediv__(self, other):
        """Divide (split!) this TimeSpan into [other: int] pieces."""
        if not isinstance(other, int):
            raise TypeError("TimeSpan can only be divided into [int] pieces.")

        if self.duration == datetime.timedelta(0):
            return [self]

        pieces = []
        duration = self.duration / other
        for i in range(other - 1):
            pieces.append(
                TimeSpan(
                    self.start + i * duration,
                    self.start + (i + 1) * duration
                )
            )
        pieces.append(
            TimeSpan(
                self.start + (other - 1) * duration,
                self.end
            )
        )

        return pieces

    yaml_tag = "!TimeSpan"
    yaml_loader = yaml.SafeLoader
    yaml_dumper = yaml.SafeDumper

    @classmethod
    def from_yaml(cls, loader, node):
        """Convert a YAML !TimeSpan block to a TimeSpan object."""
        data = loader.construct_mapping(node)
        return TimeSpan(data["start"], data["end"])

    @classmethod
    def to_yaml(cls, dumper, data):
        """Map a TimeSpan object to its YAML representation."""
        return dumper.represent_mapping(
            "!TimeSpan",
            (
                ("start", data.start),
                ("end", data.end)
            )
        )
