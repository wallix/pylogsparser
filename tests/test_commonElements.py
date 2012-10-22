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
from datetime import datetime, timedelta
from logsparser.normalizer import get_generic_tagTypes
from logsparser.normalizer import get_generic_callBacks


def get_sensible_year(*args):
    """args is a list of ordered date elements, from month and day (both 
    mandatory) to eventual second. The function gives the most sensible 
    year for that set of values, so that the date is not set in the future."""
    year = int(datetime.now().year)
    d = datetime(year, *args)
    if d > datetime.now():
        return year - 1
    return year  


def generic_time_callback_test(instance, cb):
    """Testing time formatting callbacks. This is boilerplate code."""
    # so far only time related callbacks were written. If it changes, list
    # here non related functions to skip in this test.
    instance.assertTrue(cb in instance.cb.keys())
    DATES_TO_TEST = [ datetime.utcnow() + timedelta(-1),
                      datetime.utcnow() + timedelta(-180),
                      datetime.utcnow() + timedelta(1), # will always be considered as in the future unless you're testing on new year's eve...
                    ]
    # The pattern translation list. Order is important !
    translations = [ ("YYYY", "%Y"),
                     ("YY"  , "%y"),
                     ("DDD" , "%a"),        # localized day
                     ("DD"  , "%d"),        # day with eventual leading 0
                     ("dd"  , "%d"),        
                     ("MMM" , "%b"),        # localized month
                     ("MM"  , "%m"),        # month number with eventual leading 0
                     ("hh"  , "%H"),
                     ("mm"  , "%M"),
                     ("ss"  , "%S") ]
    pattern = cb
    for old, new in translations:
        pattern = pattern.replace(old, new)
    # special cases
    if pattern == "ISO8601":
        pattern = "%Y-%m-%dT%H:%M:%SZ"
    for d in DATES_TO_TEST:
        if pattern == "EPOCH":
            #value = d.strftime('%s') + ".%i" % (d.microsecond/1000)
            # Fix for windows strftime('%s'), and python timedelta total_seconds not exists in 2.6
            td = d - datetime(1970, 1, 1)
            total_seconds_since_epoch = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
            value = str(total_seconds_since_epoch) + ".%i" % (d.microsecond/1000)
            #
            expected_result = datetime.utcfromtimestamp(float(value))
        else:
            value = d.strftime(pattern)
            expected_result = datetime.strptime(value, pattern)
            # Deal with time formats that don't define a year explicitly
            if "%y" not in pattern.lower():
                expected_year = get_sensible_year(*expected_result.timetuple()[1:-3])
                expected_result = expected_result.replace(year = expected_year)
        log = {}
        instance.cb[cb](value, log)
        instance.assertTrue("date" in log.keys())
        instance.assertEqual(log['date'], expected_result)


class TestGenericLibrary(unittest.TestCase):
    """Unit testing for the generic libraries"""
    normalizer_path = os.environ['NORMALIZERS_PATH']
    tagTypes = get_generic_tagTypes(os.path.join(normalizer_path,
                                                 'common_tagTypes.xml'))
    cb = get_generic_callBacks(os.path.join(normalizer_path,
                                            'common_callBacks.xml'))       
        
    def test_000_availability(self):
        """Testing libraries' availability"""
        self.assertTrue( self.tagTypes != {} )
        self.assertTrue( self.cb != {} )
        
    def test_010_test_tagTypes(self):
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

    # I wish there was a way to create these tests on the fly ...
    def test_020_test_time_callback(self):
        """Testing callback MM/dd/YYYY hh:mm:ss"""
        generic_time_callback_test(self, "MM/dd/YYYY hh:mm:ss")

    def test_030_test_time_callback(self):
        """Testing callback dd/MMM/YYYY:hh:mm:ss"""
        generic_time_callback_test(self, "dd/MMM/YYYY:hh:mm:ss")
        
    def test_040_test_time_callback(self):
        """Testing callback MMM dd hh:mm:ss"""
        generic_time_callback_test(self, "MMM dd hh:mm:ss")

    def test_050_test_time_callback(self):
        """Testing callback DDD MMM dd hh:mm:ss YYYY"""
        generic_time_callback_test(self, "DDD MMM dd hh:mm:ss YYYY")
        
    def test_060_test_time_callback(self):
        """Testing callback YYYY-MM-DD hh:mm:ss"""
        generic_time_callback_test(self, "YYYY-MM-DD hh:mm:ss")
        
    def test_070_test_time_callback(self):
        """Testing callback MM/DD/YY, hh:mm:ss"""
        generic_time_callback_test(self, "MM/DD/YY, hh:mm:ss")

    def test_070_test_time_callback(self):
        """Testing callback YYMMDD hh:mm:ss"""
        generic_time_callback_test(self, "YYMMDD hh:mm:ss")

    def test_080_test_time_callback(self):
        """Testing callback ISO8601"""
        generic_time_callback_test(self, "ISO8601")

    def test_090_test_time_callback(self):
        """Testing callback EPOCH"""
        generic_time_callback_test(self, "EPOCH")

    def test_100_test_time_callback(self):
        """Testing callback dd-MMM-YYYY hh:mm:ss"""
        generic_time_callback_test(self, "dd-MMM-YYYY hh:mm:ss")

if __name__ == "__main__":
    unittest.main()
