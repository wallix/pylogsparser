# -*- python -*-
# -*- coding: utf-8 -*-

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

"""Utility to visualize tags per taxonomy."""

import time
import os
from logsparser.lognormalizer import LogNormalizer as LN
from optparse import OptionParser

normalizer_path = os.environ['NORMALIZERS_PATH'] or '../normalizers/'

ln = LN(normalizer_path)

parser = OptionParser()
parser.add_option("-i", 
                  "--input", 
                  dest="input", 
                  action="store", 
                  help="the path to an optional log source file")
(options, args) = parser.parse_args()

logs = []
if options.input:
    try:
        logs = open(options.input, 'r').readlines()
    except IOError, e:
        print "Could not open %s, skipping" % options.input
if not logs:
    print "Using default logs only."
    
categories = dict([ (u.taxonomy, 0) 
                    for u in sum(ln.normalizers.values(), [])
                    if u.taxonomy ]).keys()
categories.sort()
categories.append("N/A")
base_logs = [ e.raw_line for e in sum([ p.examples 
                                    for p in sum([ u.patterns.values() 
                                    for u in sum(ln.normalizers.values(), [])
                                    if u.appliedTo in ["raw", "body"] ], [])
                                  ], []) 
            ]

logs_per_categories = {}

def compute(logs_set):
    global logs_per_categories
    for l in logs_set:
        testlog = {'raw' : l,
                   'body': l}
        ln.lognormalize(testlog)
        taxonomy = testlog.get('taxonomy', "N/A")
        if taxonomy not in logs_per_categories:
            logs_per_categories[taxonomy] = {'logs' : 0,
                                             'tags' : {}
                                            }
        logs_per_categories[taxonomy]['logs'] += 1
        for t in testlog:
            if t not in logs_per_categories[taxonomy]['tags']:
                logs_per_categories[taxonomy]['tags'][t] = 0
            logs_per_categories[taxonomy]['tags'][t] += 1

print "Parsing logs...",
start = time.time()
compute(base_logs)
compute(logs)
print "Done in %.2f seconds." % (time.time() - start)
print "\n-------------------\n"

for c in categories:
    if c in logs_per_categories:
        total = float(logs_per_categories[c]['logs'])
        print "Category %s (%i log(s)):\n" % (c, total)
        for t in sorted(logs_per_categories[c]['tags'].keys(), 
                        cmp = lambda x,y: cmp(logs_per_categories[c]['tags'][x],
                                              logs_per_categories[c]['tags'][y])
                       ):
            print "\t* %s : %.2f%%" % (t, 100 * logs_per_categories[c]['tags'][t] / total)
    else:
        print "No logs for category %s !" % c
    print "\n-------------------\n"
        
