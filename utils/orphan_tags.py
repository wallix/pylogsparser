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
from sys import exit as sysexit
from logsparser.lognormalizer import LogNormalizer as LN
from optparse import OptionParser

normalizer_path = os.environ['NORMALIZERS_PATH'] or '../normalizers/'

ln = LN(normalizer_path)

help = """
This utility aims to list tags frequencies per taxonomy.

It uses the environment variable $NORMALIZERS_PATH as the source of normalizers
to test.
By default, this script will use the sample logs shipped in the normalizers as
its input; it is possible to use another log file by using the parameter -i.

The script's output is a classification of tags per service type. It looks like
this:

Category *SERVICENAME* (N log(s)):

	* tag1 : 16.67%
		( program : 100.00%  )
	* tag2 : 16.67%
		( program : 100.00%  )
	...
	
N is the total amount of logs in the input set (sample logs included) that
match this category.
For each tag, the occurrence percentage is displayed; on the following line
the repartition of the logs with this tag, in this category, per program, is
displayed.
"""

parser = OptionParser(help)
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
                logs_per_categories[taxonomy]['tags'][t] = {'_total' : 0}
            prg = "Not set"
            if "program" in testlog:
                prg = testlog['program']
            if prg not in logs_per_categories[taxonomy]['tags'][t]:
                logs_per_categories[taxonomy]['tags'][t][prg] = 0
            logs_per_categories[taxonomy]['tags'][t]['_total'] += 1
            logs_per_categories[taxonomy]['tags'][t][prg] += 1

print "Parsing %i logs..." % (len(base_logs) + len(logs)),
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
                        cmp = lambda x,y: cmp(logs_per_categories[c]['tags'][x]['_total'],
                                              logs_per_categories[c]['tags'][y]['_total'])
                       ):
            print "\t* %s : %.2f%%" % (t, 100 * logs_per_categories[c]['tags'][t]['_total'] / total)
            print "\t\t(",
            for prg in [ u for u in logs_per_categories[c]['tags'][t] if u is not '_total' ]:
                print "%s : %.2f%% " % (prg, 100 * float(logs_per_categories[c]['tags'][t][prg]) / logs_per_categories[c]['tags'][t]['_total']),
            print ")"
    else:
        print "No logs for category %s !" % c
    print "\n-------------------\n"
        
