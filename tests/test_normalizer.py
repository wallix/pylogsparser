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
from logsparser.normalizer import Normalizer, TagType, Tag, CallbackFunction, CSVPattern, get_generic_tagTypes
from lxml.etree import parse, DTD

class TestSample(unittest.TestCase):
    """Unit tests for logsparser.normalize. Validate sample log example"""
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
    
    def test_normalize_samples_012_symantec(self):
        self.normalize_samples('symantec.xml', 'symantec', 0.99)
    
    def test_normalize_samples_014_arkoonfast360(self):
        self.normalize_samples('arkoonFAST360.xml', 'arkoonFAST360', 0.99)

    def test_normalize_samples_013_msexchange2007MTL(self):
        self.normalize_samples('MSExchange2007MessageTracking.xml', 'MSExchange2007MessageTracking', 0.99)


class TestCSVPattern(unittest.TestCase):
    """Test CSVPattern behaviour"""
    normalizer_path = os.environ['NORMALIZERS_PATH']
   
    tt1 = TagType(name='Anything', ttype=str, regexp='.*')

    tt2 = TagType(name='SyslogDate', ttype=datetime,
                  regexp='[A-Z][a-z]{2} [ 0-9]\d \d{2}:\d{2}:\d{2}')
        
    tag_types = {}
    for tt in (tt1, tt2):
        tag_types[tt.name] = tt

    generic_tagTypes = get_generic_tagTypes(path = os.path.join(normalizer_path,
                                                 'common_tagTypes.xml'))

    cb_syslogdate = CallbackFunction("""
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
now = datetime.now()
currentyear = now.year
# Following line may throw a lot of ValueError
newdate = datetime(currentyear,
                   MONTHS.index(value[0:3]) + 1,
                   int(value[4:6]),
                   int(value[7:9]),
                   int(value[10:12]),
                   int(value[13:15]))
log["date"] = newdate
""", name = 'formatsyslogdate')

    def test_normalize_csv_pattern_001(self):
        t1 = Tag(name='date',
                tagtype = 'Anything',
                substitute = 'DATE')
        t2 = Tag(name='id',
                tagtype = 'Anything',
                substitute = 'ID')
        t3 = Tag(name='msg',
                tagtype = 'Anything',
                substitute = 'MSG')

        p_tags = {}
        for t in (t1, t2, t3):
            p_tags[t.name] = t

        p = CSVPattern('test', 'DATE,ID,MSG', tags = p_tags, tagTypes = self.tag_types, genericTagTypes = self.generic_tagTypes)
        ret = p.normalize('Jul 18 08:55:35,83,"start listening on 127.0.0.1, pam auth started"')
        self.assertEqual(ret['date'], 'Jul 18 08:55:35')
        self.assertEqual(ret['id'], '83')
        self.assertEqual(ret['msg'], 'start listening on 127.0.0.1, pam auth started')
        
    def test_normalize_csv_pattern_002(self):
        t1 = Tag(name='date',
                tagtype = 'SyslogDate',
                substitute = 'DATE')
        t2 = Tag(name='id',
                tagtype = 'Anything',
                substitute = 'ID')
        t3 = Tag(name='msg',
                tagtype = 'Anything',
                substitute = 'MSG')

        p_tags = {}
        for t in (t1, t2, t3):
            p_tags[t.name] = t
        
        p = CSVPattern('test', 'DATE,ID,MSG', tags = p_tags, tagTypes = self.tag_types, genericTagTypes = self.generic_tagTypes)

        ret = p.normalize('Jul 18 08:55:35,83,"start listening on 127.0.0.1, pam auth started"')
        self.assertEqual(ret['date'], 'Jul 18 08:55:35')
        self.assertEqual(ret['id'], '83')
        self.assertEqual(ret['msg'], 'start listening on 127.0.0.1, pam auth started')
            
        ret = p.normalize('2011 Jul 18 08:55:35,83,"start listening on 127.0.0.1, pam auth started"')
        self.assertEqual(ret, None)
        
    def test_normalize_csv_pattern_003(self):
        t1 = Tag(name='date',
               tagtype = 'SyslogDate',
               substitute = 'DATE',
               callbacks = ['formatsyslogdate'])
        t2 = Tag(name='id',
               tagtype = 'Anything',
               substitute = 'ID')
        t3 = Tag(name='msg',
               tagtype = 'Anything',
               substitute = 'MSG')

        p_tags = {}
        for t in (t1, t2, t3):
            p_tags[t.name] = t
        
        p = CSVPattern('test', 'DATE,ID,MSG', tags = p_tags,
                        tagTypes = self.tag_types, callBacks = {self.cb_syslogdate.name:self.cb_syslogdate},
                        genericTagTypes = self.generic_tagTypes)

        ret = p.normalize('Jul 18 08:55:35,83,"start listening on 127.0.0.1, pam auth started"')
        self.assertEqual(ret['date'], datetime(datetime.now().year, 7, 18, 8, 55, 35))
        self.assertEqual(ret['id'], '83')
        self.assertEqual(ret['msg'], 'start listening on 127.0.0.1, pam auth started')
    
    def test_normalize_csv_pattern_004(self):
        t1 = Tag(name='date',
                tagtype = 'Anything',
                substitute = 'DATE')
        t2 = Tag(name='id',
                tagtype = 'Anything',
                substitute = 'ID')
        t3 = Tag(name='msg',
                tagtype = 'Anything',
                substitute = 'MSG')

        p_tags = {}
        for t in (t1, t2, t3):
            p_tags[t.name] = t

        p = CSVPattern('test', ' DATE; ID ;MSG ', separator = ';', quotechar = '=', tags = p_tags, tagTypes = self.tag_types, genericTagTypes = self.generic_tagTypes)
        ret = p.normalize('Jul 18 08:55:35;83;=start listening on 127.0.0.1; pam auth started=')
        self.assertEqual(ret['date'], 'Jul 18 08:55:35')
        self.assertEqual(ret['id'], '83')
        self.assertEqual(ret['msg'], 'start listening on 127.0.0.1; pam auth started')
    
    def test_normalize_csv_pattern_005(self):
        t1 = Tag(name='date',
                tagtype = 'Anything',
                substitute = 'DATE')
        t2 = Tag(name='id',
                tagtype = 'Anything',
                substitute = 'ID')
        t3 = Tag(name='msg',
                tagtype = 'Anything',
                substitute = 'MSG')

        p_tags = {}
        for t in (t1, t2, t3):
            p_tags[t.name] = t

        p = CSVPattern('test', 'DATE ID MSG', separator = ' ', quotechar = '=', tags = p_tags, tagTypes = self.tag_types, genericTagTypes = self.generic_tagTypes)
        ret = p.normalize('=Jul 18 08:55:35= 83 =start listening on 127.0.0.1 pam auth started=')
        self.assertEqual(ret['date'], 'Jul 18 08:55:35')
        self.assertEqual(ret['id'], '83')
        self.assertEqual(ret['msg'], 'start listening on 127.0.0.1 pam auth started')
    
    def test_normalize_csv_pattern_006(self):
        t1 = Tag(name='date',
                tagtype = 'Anything',
                substitute = 'DATE')
        t2 = Tag(name='id',
                tagtype = 'Anything',
                substitute = 'ID')
        t3 = Tag(name='msg',
                tagtype = 'Anything',
                substitute = 'MSG')

        p_tags = {}
        for t in (t1, t2, t3):
            p_tags[t.name] = t

        p = CSVPattern('test', 'DATE ID MSG', separator = ' ', quotechar = '=', tags = p_tags, tagTypes = self.tag_types, genericTagTypes = self.generic_tagTypes)
        # Default behaviour of csv reader is doublequote for escape a quotechar.
        ret = p.normalize('=Jul 18 08:55:35= 83 =start listening on ==127.0.0.1 pam auth started=')
        self.assertEqual(ret['date'], 'Jul 18 08:55:35')
        self.assertEqual(ret['id'], '83')
        self.assertEqual(ret['msg'], 'start listening on =127.0.0.1 pam auth started')

    def test_normalize_samples_012_s3(self):
        self.normalize_samples('s3.xml', 's3', 0.99)

if __name__ == "__main__":
    unittest.main()
