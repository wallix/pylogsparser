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

import logsparser.extras as extras
import unittest

class TestExtras(unittest.TestCase):
    """Unit tests for the extras libraries."""
    
    def test_00_domains(self):
        """Tests domain extraction from various addresses."""
        # feel free to complete !
        self.assertEquals(extras.get_domain("10.10.4.7"), "10.10.4.7")
        self.assertEquals(extras.get_domain("www.google.com"), "google.com")
        self.assertEquals(extras.get_domain("lucan.cs.purdue.edu"), "purdue.edu")
        
if __name__ == "__main__":
    unittest.main()
