# -*- coding: utf-8 -*-

# -*- python -*-

# pylogsparser - Logs parsers python library
#
# Copyright (C) 2011 Wallix Inc.
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

""""""

import pytz

def to_naive_utc(date, from_tz):
    """
    @param date: a naive datetime instance
    @param from_tz: timezone information about the naive datetime
    @return: naive datetime set to UTC
    """
    date = date.replace(tzinfo=None)
    try:
        timezone = pytz.timezone(from_tz)
    except pytz.UnknownTimeZoneError:
        timezone = pytz.utc
    loc_date = timezone.localize(date)
    return loc_date.astimezone(pytz.utc).replace(tzinfo=None)
