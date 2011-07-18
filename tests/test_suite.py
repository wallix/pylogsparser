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

""" The LogNormalizer need to be instanciated with the path to
normalizers XML definitions.

Tests expects to find normlizer path in NORMALIZERS_PATH environment variable.

$ NORMALIZERS_PATH=normalizers/ python tests/test_suite.py
"""

import unittest
import test_normalizer
import test_lognormalizer
import test_log_samples

tests = (test_normalizer,
         test_lognormalizer,
         test_log_samples)

load = unittest.defaultTestLoader.loadTestsFromModule
suite = unittest.TestSuite(map(load, tests)) 

unittest.TextTestRunner(verbosity=2).run(suite)
