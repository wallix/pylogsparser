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


"""This module exposes the L{LogNormalizer} class that can be used for
higher-level management of the normalization flow.
Using this module is in no way mandatory in order to benefit from
the normalization system; the C{LogNormalizer} class provides basic facilities
for further integration in a wider project (web services, ...).
"""

import os
import uuid as _UUID_
import warnings
import StringIO

from normalizer import Normalizer
from lxml.etree import parse, DTD, fromstring as XMLfromstring

class LogNormalizer():
    """Basic normalization flow manager.
    Normalizers definitions are loaded from a path and checked against the DTD.
    If the definitions are syntactically correct, the normalizers are
    instantiated and populate the manager's cache.
    Normalization priormority is established as follows:
    
    * Maximum priority assigned to normalizers where the "appliedTo" tag is set
      to "raw". They MUST be mutually exclusive.
    * Medium priority assigned to normalizers where the "appliedTo" tag is set
      to "body".
    * Lowest priority assigned to any remaining normalizers.
    
    Some extra treatment is also done prior and after the log normalization:
    
    * Assignment of a unique ID, under the tag "uuid"
    * Conversion of date tags to UTC, if the "_timezone" was set prior to
      the normalization process."""
    
    def __init__(self, normalizers_paths, active_normalizers = {}):
        """
        Instantiates a flow manager. The default behavior is to activate every
        available normalizer.
        
        @param normalizers_paths: a list of absolute paths to the normalizer
        XML definitions to use or a just a single path as str.
        @param active_normalizers: a dictionary of active normalizers
        in the form {name: [True|False]}.
        """
        if not isinstance(normalizers_paths, list or tuple):
            normalizers_paths = [normalizers_paths,]
        self.normalizers_paths = normalizers_paths
        self.active_normalizers = active_normalizers
        self.dtd, self.ctt, self.ccb = None, None, None
        
        # Walk through paths for normalizer.dtd and common_tagTypes.xml
        # /!\ dtd file and common elements will be overrriden if present in
        # many directories.
        for norm_path in self.normalizers_paths:
            if not os.path.isdir(norm_path):
                raise ValueError, "Invalid normalizer directory : %s" % norm_path
            dtd = os.path.join(norm_path, 'normalizer.dtd')
            ctt = os.path.join(norm_path, 'common_tagTypes.xml')
            ccb = os.path.join(norm_path, 'common_callBacks.xml')
            if os.path.isfile(dtd):
                self.dtd = DTD(open(dtd))
            if os.path.isfile(ctt):
                self.ctt = ctt
            if os.path.isfile(ccb):
                self.ccb = ccb
        # Technically the common elements files should NOT be mandatory.
        # But many normalizers use them, so better safe than sorry.
        if not self.dtd or not self.ctt or not self.ccb:
            raise StandardError, "Missing DTD or common library files"
        self._cache = []
        self.reload()
        
    def reload(self):
        """Refreshes this instance's normalizers pool."""
        self.normalizers = { 'raw' : [], 'body' : [] }
        for path in self.iter_normalizer():
            norm = parse(open(path))
            if not self.dtd.validate(norm):
                warnings.warn('Skipping %s : invalid DTD' % path)
                print 'invalid normalizer ', path
            else:
                normalizer = Normalizer(norm, self.ctt, self.ccb)
                normalizer.uuid = self._compute_norm_uuid(normalizer)
                self.normalizers.setdefault(normalizer.appliedTo, [])
                self.normalizers[normalizer.appliedTo].append(normalizer)
        self.activate_normalizers()

    def _compute_norm_uuid(self, normalizer):
        return "%s-%s" % (normalizer.name, normalizer.version)

    def iter_normalizer(self):
        """ Iterates through normalizers and returns the normalizers' paths.
        
        @return: a generator of absolute paths.
        """
        for path in self.normalizers_paths:
            for root, dirs, files in os.walk(path):
                for name in files:
                    if not name.startswith('common_tagTypes') and \
                       not name.startswith('common_callBacks') and \
                           name.endswith('.xml'):
                        yield os.path.join(root, name)

    def __len__(self):
        """ Returns the amount of available normalizers.
        """
        return len([n for n in self.iter_normalizer()])

    def update_normalizer(self, raw_xml_contents, name = None, dir_path = None ):
        """used to add or update a normalizer.
        @param raw_xml_contents: XML description of normalizer as flat XML. It
        must comply to the DTD.
        @param name: if set, the XML description will be saved as name.xml.
        If left blank, name will be fetched from the XML description.
        @param dir_path: the path to the directory where to copy the given
        normalizer.
        """
        path = self.normalizers_paths[0]
        if dir_path:
            if dir_path in self.normalizers_paths:
                path = dir_path
        xmlconf = XMLfromstring(raw_xml_contents).getroottree()
        if not self.dtd.validate(xmlconf):
            raise ValueError, "This definition file does not follow the normalizers DTD :\n\n%s" % \
                               self.dtd.error_log.filter_from_errors()
        if not name:
            name = xmlconf.getroot().get('name')
        if not name.endswith('.xml'):
            name += '.xml'
        xmlconf.write(open(os.path.join(path, name), 'w'),
                      encoding = 'utf8',
                      method = 'xml',
                      pretty_print = True)
        self.reload()

    def get_normalizer_by_uuid(self, uuid):
        """Returns normalizer by uuid."""
        try:
            norm = [ u for u in sum(self.normalizers.values(), []) if u.uuid == uuid][0]
            return norm
        except:
            raise ValueError, "Normalizer uuid : %s not found" % uuid
        
    def get_normalizer_source(self, uuid):
        """Returns the raw XML source of normalizer uuid."""
        return self.get_normalizer_by_uuid(uuid).get_source()
    
    def get_normalizer_path(self, uuid):
        """Returns the filesystem path of a normalizer."""
        return self.get_normalizer_by_uuid(uuid).sys_path

    
    def activate_normalizers(self):
        """Activates normalizers according to what was set by calling
        set_active_normalizers. If no call to the latter function has been
        made so far, this method activates every normalizer."""
        if not self.active_normalizers:
            self.active_normalizers = dict([ (n.uuid, True) for n in \
                        sum([ v for v in self.normalizers.values()], []) ])
        # fool-proof the list
        self.set_active_normalizers(self.active_normalizers)
        # build an ordered cache to speed things up
        self._cache = []
        # First normalizers to apply are the "raw" ones.
        for norm in self.normalizers['raw']:
            # consider the normalizer to be inactive if not
            # explicitly in our list
            if self.active_normalizers.get(norm.uuid, False):
                self._cache.append(norm)
        # Then, apply the applicative normalization on "body":
        for norm in self.normalizers['body']:
            if self.active_normalizers.get(norm.uuid, False):
                self._cache.append(norm)
        # Then, apply everything else
        for norm in sum([ self.normalizers[u] for u in self.normalizers 
                                           if u not in ['raw', 'body']], []):
            if self.active_normalizers.get(norm.uuid, False):
                self._cache.append(norm)

    def get_active_normalizers(self):
        """Returns a dictionary of normalizers; keys are normalizers' uuid and
        values are True|False according to the normalizer's activation state."""
        return self.active_normalizers

    def set_active_normalizers(self, norms = {}):
        """Sets the active/inactive normalizers. Default behavior is to
        deactivate every normalizer.
        
        @param norms: a dictionary, similar to the one returned by
        get_active_normalizers."""
        default = dict([ (n.uuid, False) for n in \
                            sum([ v for v in self.normalizers.values()], []) ])
        default.update(norms)
        self.active_normalizers = default
        
    def lognormalize(self, data):
        """ This method is the entry point to normalize data (a log).

        data is passed through every activated normalizer
        and extra tagging occurs accordingly.
        
        data receives also an extra uuid tag.

        @param data: must be a dictionary with at least a key 'raw' or 'body'
                     with BaseString values (preferably Unicode).
        
        Here an example :
        >>> from logsparser import lognormalizer
        >>> from pprint import pprint
        >>> ln = lognormalizer.LogNormalizer('/usr/local/share/normalizers/')
        >>> mylog = {'raw' : 'Jul 18 15:35:01 zoo /USR/SBIN/CRON[14338]: (root) CMD (/srv/git/redmine-changesets.sh)'}
        >>> ln.lognormalize(mylog)
        >>> pprint mylog
        {'body': '(root) CMD (/srv/git/redmine-changesets.sh)',
        'date': datetime.datetime(2011, 7, 18, 15, 35, 1),
        'pid': '14338',
        'program': '/USR/SBIN/CRON',
        'raw': 'Jul 18 15:35:01 zoo /USR/SBIN/CRON[14338]: (root) CMD (/srv/git/redmine-changesets.sh)',
        'source': 'zoo',
        'uuid': 70851882840934161193887647073096992594L}
        """
        data = self.uuidify(data)
        data = self.normalize(data)

    
    # some more functions for clarity
    def uuidify(self, log):
        """Adds a unique UID to the normalized log."""
        log["uuid"] = _UUID_.uuid4().int
        return log
        
    def normalize(self, log):
        """plain normalization."""
        for norm in self._cache:
            log = norm.normalize(log)
        return log

    def _normalize(self, log):
        """Used for testing only, the normalizers' tags prerequisite are
        deactivated."""
        for norm in self._cache:
            log = norm.normalize(log, do_not_check_prereq = True)
        return log
        
