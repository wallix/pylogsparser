# -*- coding: utf-8 -*-

# -*- python -*-

# pylogsparser - Logs parsers python library
#
# Copyright (C) 2012 Wallix Inc.
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

"""Windows and MS-related utility functions."""

from datetime import datetime

def winUTC2UnixTimestamp(winTimestamp):
	"""Converts a windows UTC timestamp (increments of 100 nanoseconds since Jan 1, 1601)
	into a Unix EPOCH timestamp.
	
	@param winTimestamp : the windows timestamp"""
	
	a = int(winTimestamp)
	unixts = (a / 10000000) - 11644473600
	return datetime.fromtimestamp(unixts).isoformat()
