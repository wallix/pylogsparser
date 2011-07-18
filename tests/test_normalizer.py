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
from logsparser.normalizer import Normalizer
from lxml.etree import parse, DTD

class Test(unittest.TestCase):
    """Unit tests for logsparser.normalize"""
    normalizer_path = os.environ['NORMALIZERS_PATH']

    def normalize_samples(self, norm, name, version):
        """Test logparser.normalize validate for syslog normalizer."""
        # open parser
        n = parse(open(os.path.join(self.normalizer_path, norm)))
        # validate DTD
        dtd = DTD(open(os.path.join(self.normalizer_path,
                                    'normalizer.dtd')))
        self.assertTrue(dtd.validate(n))
        # Create normalizer from xml definition
        normalizer = Normalizer(n, os.path.join(self.normalizer_path, 'common_tagTypes.xml'))
        self.assertEquals(normalizer.name, name)
        self.assertEquals(normalizer.version, version)
        self.assertTrue(normalizer.validate())

    def test_normalize_samples_001_syslog(self):
        self.normalize_samples('syslog.xml', 'syslog', 0.99)

    def test_normalize_samples_002_apache(self):
        self.normalize_samples('apache.xml', 'apache', 0.99)
    
    def test_normalize_samples_003_dhcpd(self):
        self.normalize_samples('dhcpd.xml', 'DHCPd', 0.99)
    
    def test_normalize_samples_004_lea(self):
        self.normalize_samples('LEA.xml', 'LEA', 0.99)
    
    def test_normalize_samples_005_netfilter(self):
        self.normalize_samples('netfilter.xml', 'netfilter', 0.99)
    
    def test_normalize_samples_006_pam(self):
        self.normalize_samples('pam.xml', 'PAM', 0.99)
    
    def test_normalize_samples_007_postfix(self):
        self.normalize_samples('postfix.xml', 'postfix', 0.99)
    
    def test_normalize_samples_008_squid(self):
        self.normalize_samples('squid.xml', 'squid', 0.99)
    
    def test_normalize_samples_009_sshd(self):
        self.normalize_samples('sshd.xml', 'sshd', 0.99)
    
    def test_normalize_samples_010_named(self):
        self.normalize_samples('named.xml', 'named', 0.99)
    
    def test_normalize_samples_011_named2(self):
        self.normalize_samples('named-2.xml', 'named-2', 0.99)

if __name__ == "__main__":
    unittest.main()

