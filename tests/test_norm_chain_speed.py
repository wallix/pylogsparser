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

import os
import timeit
from logsparser.lognormalizer import LogNormalizer

if __name__ == "__main__":
    path = os.environ['NORMALIZERS_PATH']
    ln = LogNormalizer(path)

    def test():
        l = {'raw' : "<29>Jul 18 08:55:35 naruto squid[3245]: 1259844091.407    307 82.238.42.70 TCP_MISS/200 1015 GET http://www.ietf.org/css/ietf.css fbo DIRECT/64.170.98.32 text/css" }
        l = ln.uuidify(l)
        ln.normalize(l)
    
    print "Testing speed ..."
    t = timeit.Timer("test()", "from __main__ import test")
    speed = t.timeit(100000)/100000
    print "%.2f microseconds per pass, giving a theoretical speed of %i logs/s." % (speed * 1000000, 1 / speed) 
    
    print "Testing speed with minimal normalization ..."
    ln.set_active_normalizers({'syslog' : True})
    ln.reload()
    t = timeit.Timer("test()", "from __main__ import test")
    speed = t.timeit(100000)/100000
    print "%.2f microseconds per pass, giving a theoretical speed of %i logs/s." % (speed * 1000000, 1 / speed)
