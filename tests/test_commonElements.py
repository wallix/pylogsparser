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

import os
import unittest
from datetime import datetime
from logsparser.normalizer import get_generic_tagTypes
from logsparser.normalizer import get_generic_callBacks


class TestGenericLibrary(unittest.TestCase):
    """Unit testing for the generic libraries"""
    normalizer_path = os.environ['NORMALIZERS_PATH']
    tagTypes = get_generic_tagTypes(os.path.join(normalizer_path,
                                                 'common_tagTypes.xml'))
    cb = get_generic_callBacks(os.path.join(normalizer_path,
                                            'common_callBacks.xml'))
                                                
    def get_sensible_year(*args):
        """args is a list of ordered date elements, from month and day (both 
        mandatory) to eventual second. The function gives the most sensible 
        year for that set of values, so that the date is not set in the future."""
        year = datetime.now().year
        d = datetime(year, *args)
        if d > datetime.now():
            return year - 1
        return year         
        
    def test_00_availability(self):
        """Testing libraries' availability"""
        self.assertTrue( self.tagTypes != {} )
        self.assertTrue( self.cb != {} )
        
    def test_10_test_tagTypes(self):
        """Testing tagTypes' accuracy"""
        self.assertTrue(self.tagTypes['EpochTime'].compiled_regexp.match('12934824.134'))
        self.assertTrue(self.tagTypes['EpochTime'].compiled_regexp.match('12934824'))
        self.assertTrue(self.tagTypes['syslogDate'].compiled_regexp.match('Jan 23 10:23:45'))
        self.assertTrue(self.tagTypes['syslogDate'].compiled_regexp.match('Oct  6 23:05:10'))
        self.assertTrue(self.tagTypes['URL'].compiled_regexp.match('http://www.wallix.org'))
        self.assertTrue(self.tagTypes['URL'].compiled_regexp.match('https://mysecuresite.com/?myparam=myvalue&myotherparam=myothervalue'))
        self.assertTrue(self.tagTypes['Email'].compiled_regexp.match('mhu@wallix.com'))
        self.assertTrue(self.tagTypes['Email'].compiled_regexp.match('matthieu.huin@wallix.com'))
        self.assertTrue(self.tagTypes['Email'].compiled_regexp.match('John-Fitzgerald.Willis@super-duper.institution.withlotsof.subdomains.org'))
        self.assertTrue(self.tagTypes['IP'].compiled_regexp.match('192.168.1.1'))
        self.assertTrue(self.tagTypes['IP'].compiled_regexp.match('255.255.255.0'))
        # shouldn't match ...
        self.assertTrue(self.tagTypes['IP'].compiled_regexp.match('999.888.777.666'))
        self.assertTrue(self.tagTypes['MACAddress'].compiled_regexp.match('0e:88:6a:4b:00:ff'))
        self.assertTrue(self.tagTypes['ZuluTime'].compiled_regexp.match('2012-12-21'))
        self.assertTrue(self.tagTypes['ZuluTime'].compiled_regexp.match('2012-12-21T12:34:56.99'))
        
if __name__ == "__main__":
    unittest.main()
