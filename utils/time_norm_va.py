# -*- python -*-
#
# time_norm_va.py
#
# Copyright (C) 2012 JF Taltavull - jftalta@gmail.com
#
# This program is part of pylogsparser, a logs parser python library, copyright (c) 2011 Wallix Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by the
# Free Software Foundation
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
#
# Description
# ===========
# This program aims to measure the validation time of each normalizer shipped with pylogsparser package.
# - the measure is done by applying the "normalizer.validate" method on each xml coded normalizer, assuming each
#   normalizer embeds at least one example.
# - the environment variable NORMALIZERS_PATH must be defined.
# - default iterations number per normalizer is 5000 (see "iterations" variable)
# - results are printed on standard output, sorted on time, ascending order (faster normalizer first).
# - times are in micro-seconds
#

import os
import sys
import re
import timeit
from logsparser.normalizer import Normalizer
from logsparser.lognormalizer import LogNormalizer
from lxml.etree import parse, DTD

"""Measuring normalizers validation time"""

VERSION = 0.99
iterations = 5000
excl = (                      # Exclusion list, skip these files
        "common_callBacks.xml",
        "common_tagTypes.xml",
        "normalizer.dtd",
        "normalizer.template"
       )
path = os.environ['NORMALIZERS_PATH']
norm = None                   # normalizer object
ln = LogNormalizer(path)
tested_logs = None

class res:

    def __init__(self, it):
        self.nn = 0       # number of normalizers
        self.ts = 0.0     # times sum
        self.it = it      # number of iterations per normalizer
        self.rl = []      # results list (a list of dictionaries)

    def add_res(self, n, v, a, s):
        self.rl.append({"name" : n, "version" : v, "author" : a, "time" : s});
        self.nn += 1
        self.ts += s

    def key_time(self, r):  # function used by sort method
        return r["time"]	# sort on time field, ascending order

    def print_result(self):
        i = 0
        self.rl.sort(key=self.key_time)
        for r in self.rl:
            i += 1
            print "%i - " % i, "%s" % r["name"], "t=%imis" % ((r["time"] / self.it) * 1000000),\
                  "(v%s" % r["version"], "%s)" % r["author"]
        print "Number of iterations per normalizer=%i" % self.it
        print "Average time per iteration=%imis" % (self.ts / (self.nn * self.it) * 1000000)


def validate_norm(fn, nn, version, it):
    global norm 
    global result

    # open XML parser
    n = parse(open(os.path.join(path, fn)))
    # validate DTD
    dtd = DTD(open(os.path.join(path, 'normalizer.dtd')))
    assert dtd.validate(n) == True
    # Create normalizer from xml definition
    norm = Normalizer(n, os.path.join(path, 'common_tagTypes.xml'),
                      os.path.join(path, 'common_callBacks.xml'))
    # Time normalizer validation
    try:
        assert norm.name.lower() == nn.lower()
        if norm.name != nn:
            print "Warning, %s has name attribute set to %s" % (fn, norm.name)
    except AssertionError:
        print "\n[%s]" % norm.name, "and [%s]" % nn, "don't match"
        return
    try:
        assert norm.version == version
    except AssertionError:
        print "\n[%s]" % norm.version, "and [%s]" % version, "don't match"
        return
    samples_amount = len([u for u in [v.examples for v in norm.patterns.values()]])
    if samples_amount <= 0:
        print "No samples to validate in %s" % fn
        return
    t = timeit.Timer("assert norm.validate() == True", "from __main__ import norm")
    s = t.timeit(it)
    # Normalize result against number of validated samples
    s = s / float(samples_amount)
    # Add result
    result.add_res(norm.name, norm.version, norm.authors, s)

def bench_full(it, logset = []):
    """@param logset : a list of logs to use for the speed test. Default
    behavior is to use log samples from patterns of normalizers that are applied
    to "raw" or "body" tags."""
    global ln
    global tested_logs
    results = []
    if not logset:
        norm_samples = ln.normalizers['raw'] + ln.normalizers['body']
        logset = [u.raw_line 
                  for u in sum([p.examples 
                                for p in sum([norm.patterns.values() 
                                              for norm in norm_samples], 
                                             []) ], 
                               [])
                 ]
    # first, classify logs per programs (or taxonomy ?)
    sorted_logset = {}
    print "Sorting logs ...",
    for logline in logset:
        d = {'raw' : logline,
             'body': logline }
        ln.normalize(d)
        if 'program' not in d:
            d['program'] = "Unknown program"
        sorted_logset[d['program']] = sorted_logset.get(d['program'], []) + [{'raw' : logline,
                                                                              'body': logline },]
    print " Done."
    # then, test logs per program:
    for program in sorted(sorted_logset.keys()):
        print "Testing %s logs ..." % program
        tested_logs = sorted_logset[program]
        t = timeit.Timer("""for l in tested_logs: ln.normalize(l)""",
                         """from __main__ import tested_logs, ln""")
        s = t.timeit(it) / float(len(tested_logs))
        results.append({'program' : program,
                        'time'    : s})
    # finally, show results
    print "Printing results:"
    i = 0
    avg_time = 0
    for line in sorted(results, key=lambda x: x['time']):
        i += 1
        print "%s. %s logs treated in %i mis on average (%i sample logs used)" % (i, 
                                                                                  line['program'], 
                                                                                  (line['time'] / it) * 1000000,
                                                                                  len(sorted_logset[line['program']]))
        avg_time += line['time'] / it
    print "\nAverage parsing time : %i mis" % ((avg_time / i) * 1000000)
                

if __name__ == "__main__":

    result = res(iterations)      # results object

    # Iterate on normalizers and validate
    print "Measuring normalizers validation time: "
    for fn in os.listdir(path):
        if (fn not in excl):
            nn = re.sub(r'\.xml$', '', fn) # normalizer file name must end with .xml suffix
            validate_norm(fn, nn, VERSION, iterations)
            print ".",
            sys.stdout.flush()

    # Print results
    print "\nPrinting results:" 
    result.print_result()
    
    print "\n-----------------------\nTesting full normalization chain:"
    bench_full(iterations)
    
