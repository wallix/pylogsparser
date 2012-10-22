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
import tempfile
import shutil
from logsparser.lognormalizer import LogNormalizer
from lxml.etree import parse, fromstring as XMLfromstring

class Test(unittest.TestCase):
    """Unit tests for logsparser.lognormalizer"""
    normalizer_path = os.environ['NORMALIZERS_PATH']

    def test_000_invalid_paths(self):
        """Verify that we cannot instanciate LogNormalizer on invalid paths"""
        def bleh(paths):
            n = LogNormalizer(paths)
            return n
        self.assertRaises(ValueError, bleh, [self.normalizer_path, "/path/to/nowhere"])
        self.assertRaises(ValueError, bleh, ["/path/to/nowhere",])
        self.assertRaises(StandardError, bleh, ["/usr/bin/",])
    
    def test_001_all_normalizers_activated(self):
        """ Verify that we have all normalizer
        activated when we instanciate LogNormalizer with
        an activate dict empty.
        """
        ln = LogNormalizer(self.normalizer_path)
        self.assertTrue(len(ln))
        self.assertEqual(len([an[0] for an in ln.get_active_normalizers() if an[1]]), len(ln))
        self.assertEqual(len(ln._cache), len(ln))

    def test_002_deactivate_normalizer(self):
        """ Verify that normalizer deactivation is working.
        """
        ln = LogNormalizer(self.normalizer_path)
        active_n = ln.get_active_normalizers()
        to_deactivate = active_n.keys()[:2]
        for to_d in to_deactivate:
            del active_n[to_d]
        ln.set_active_normalizers(active_n)
        ln.reload()
        self.assertEqual(len([an[0] for an in ln.get_active_normalizers().items() if an[1]]), len(ln)-2)
        self.assertEqual(len(ln._cache), len(ln)-2)

    def test_003_activate_normalizer(self):
        """ Verify that normalizer activation is working.
        """
        ln = LogNormalizer(self.normalizer_path)
        active_n = ln.get_active_normalizers()
        to_deactivate = active_n.keys()[0]
        to_activate = to_deactivate
        del active_n[to_deactivate]
        ln.set_active_normalizers(active_n)
        ln.reload()
        # now deactivation should be done so reactivate
        active_n[to_activate] = True
        ln.set_active_normalizers(active_n)
        ln.reload()
        self.assertEqual(len([an[0] for an in ln.get_active_normalizers() if an[1]]), len(ln))
        self.assertEqual(len(ln._cache), len(ln))

    def test_004_normalizer_uuid(self):
        """ Verify that we get at least uuid tag
        """
        testlog = {'raw': 'a minimal log line'}
        ln = LogNormalizer(self.normalizer_path)
        ln.lognormalize(testlog)
        self.assertTrue('uuid' in testlog.keys())

    def test_005_normalizer_test_a_syslog_log(self):
        """ Verify that lognormalizer extracts
        syslog header as tags
        """
        testlog = {'raw': 'Jul 18 08:55:35 naruto app[3245]: body message'}
        ln = LogNormalizer(self.normalizer_path)
        ln.lognormalize(testlog)
        self.assertTrue('uuid' in testlog.keys())
        self.assertTrue('date' in testlog.keys())
        self.assertEqual(testlog['body'], 'body message')
        self.assertEqual(testlog['program'], 'app')
        self.assertEqual(testlog['pid'], '3245')

    def test_006_normalizer_test_a_syslog_log_with_syslog_deactivate(self):
        """ Verify that lognormalizer does not extract
        syslog header as tags when syslog normalizer is deactivated.
        """
        testlog = {'raw': 'Jul 18 08:55:35 naruto app[3245]: body message'}
        ln = LogNormalizer(self.normalizer_path)
        active_n = ln.get_active_normalizers()
        to_deactivate = [n for n in active_n.keys() if n.find('syslog') >= 0]
        for n in to_deactivate:
            del active_n[n]
        ln.set_active_normalizers(active_n)
        ln.reload()
        ln.lognormalize(testlog)
        self.assertTrue('uuid' in testlog.keys())
        self.assertFalse('date' in testlog.keys())
        self.assertFalse('program' in testlog.keys())

    def test_007_normalizer_getsource(self):
        """ Verify we can retreive XML source
        of a normalizer.
        """
        ln = LogNormalizer(self.normalizer_path)
        source = ln.get_normalizer_source('syslog-0.99')
        self.assertEquals(XMLfromstring(source).getroottree().getroot().get('name'), 'syslog')

    def test_008_normalizer_multiple_paths(self):
        """ Verify we can can deal with multiple normalizer paths.
        """
        fdir = tempfile.mkdtemp()
        sdir = tempfile.mkdtemp()
        for f in os.listdir(self.normalizer_path):
            path_f = os.path.join(self.normalizer_path, f)
            if os.path.isfile(path_f):
                shutil.copyfile(path_f, os.path.join(fdir, f))
        shutil.move(os.path.join(fdir, 'postfix.xml'), 
                    os.path.join(sdir, 'postfix.xml'))
        ln = LogNormalizer([fdir, sdir])
        source = ln.get_normalizer_source('postfix-0.99')
        self.assertEquals(XMLfromstring(source).getroottree().getroot().get('name'), 'postfix')
        self.assertTrue(ln.get_normalizer_path('postfix-0.99').__contains__(os.path.basename(sdir)))
        self.assertTrue(ln.get_normalizer_path('syslog-0.99').__contains__(os.path.basename(fdir)))
        xml_src = ln.get_normalizer_source('syslog-0.99')
        os.unlink(os.path.join(fdir, 'syslog.xml'))
        ln.reload()
        self.assertRaises(ValueError, ln.get_normalizer_path, 'syslog-0.99')
        ln.update_normalizer(xml_src, dir_path = sdir)
        self.assertTrue(ln.get_normalizer_path('syslog-0.99').__contains__(os.path.basename(sdir)))
        shutil.rmtree(fdir)
        shutil.rmtree(sdir)

    def test_009_normalizer_multiple_version(self):
        """ Verify we can can deal with a normalizer with more than one version.
        """
        fdir = tempfile.mkdtemp()
        shutil.copyfile(os.path.join(self.normalizer_path, 'postfix.xml'),
                        os.path.join(fdir, 'postfix.xml'))
        # Change normalizer version in fdir path
        xml = parse(os.path.join(fdir, 'postfix.xml'))
        xmln = xml.getroot()
        xmln.set('version', '1.0')
        xml.write(os.path.join(fdir, 'postfix.xml'))
        ln = LogNormalizer([self.normalizer_path, fdir])
        self.assertEquals(XMLfromstring(ln.get_normalizer_source('postfix-0.99')).getroottree().getroot().get('version'), '0.99')
        self.assertEquals(XMLfromstring(ln.get_normalizer_source('postfix-1.0')).getroottree().getroot().get('version'), '1.0')
        shutil.rmtree(fdir)

if __name__ == "__main__":
    unittest.main()
