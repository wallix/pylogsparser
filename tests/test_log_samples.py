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

"""Testing that normalization work as excepted

Here you can add samples logs to test existing or new normalizers.

In addition to examples validation defined in each normalizer xml definition
you should add validation tests here.
In this test all normalizer definitions are loaded and therefore
it is useful to detect normalization conflicts.

"""
import os
import unittest
from datetime import datetime, timedelta
import pytz

from logsparser import lognormalizer

normalizer_path = os.environ['NORMALIZERS_PATH']
ln = lognormalizer.LogNormalizer(normalizer_path)

def _get_timeoffset(timezone, localtz):
        n = datetime.now()
        return localtz.localize(n) - timezone.localize(n)

class Test(unittest.TestCase):

    def aS(self, log, subset, notexpected = (), tzinfo = None):
        """Assert that the result of normalization of a given line log has the given subset."""
        data = {'raw' : log,
                'body' : log}
        if tzinfo:
            data['_timezone'] = tzinfo
        ln.lognormalize(data)
        for key in subset:
            self.assertEqual(data[key], subset[key])
        for key in notexpected:
            self.assertFalse(key in data.keys())

    def test_simple_syslog(self):
        """Test syslog logs"""
        now = datetime.now()
        self.aS("<40>%s neo kernel: tun_wallix: Disabled Privacy Extensions" % now.strftime("%b %d %H:%M:%S"),
                {'body': 'tun_wallix: Disabled Privacy Extensions',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'neo',
                 'program': 'kernel',
                 'date': now.replace(microsecond=0)})

        self.aS("<40>%s fbo sSMTP[8847]: Cannot open mail:25" % now.strftime("%b %d %H:%M:%S"),
                {'body': 'Cannot open mail:25',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'fbo',
                 'program': 'sSMTP',
                 'pid': '8847',
                 'date': now.replace(microsecond=0)})
        
        self.aS("%s fbo sSMTP[8847]: Cannot open mail:25" % now.strftime("%b %d %H:%M:%S"),
                {'body': 'Cannot open mail:25',
                 'source': 'fbo',
                 'program': 'sSMTP',
                 'pid': '8847',
                 'date': now.replace(microsecond=0)})

        now = now.replace(month=now.month%12+1, day=1)
        self.aS("<40>%s neo kernel: tun_wallix: Disabled Privacy Extensions" % now.strftime("%b %d %H:%M:%S"),
                {'date': now.replace(microsecond=0, year=now.year-1),
                 'body': 'tun_wallix: Disabled Privacy Extensions',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'neo',
                 'program': 'kernel' })
        
        # test the tolerance up to the minute : 1 ...
        now = datetime.now() + timedelta(seconds = +57)
        self.aS("<40>%s neo kernel: tun_wallix: Disabled Privacy Extensions" % now.strftime("%b %d %H:%M:%S"),
                {'date': now.replace(microsecond=0),
                 'body': 'tun_wallix: Disabled Privacy Extensions',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'neo',
                 'program': 'kernel' })
        # ... and 2
        now = datetime.now() + timedelta(seconds = +63)
        self.aS("<40>%s neo kernel: tun_wallix: Disabled Privacy Extensions" % now.strftime("%b %d %H:%M:%S"),
                {'date': now.replace(microsecond=0, year=now.year-1),
                 'body': 'tun_wallix: Disabled Privacy Extensions',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'neo',
                 'program': 'kernel' })

    def test_syslog_with_timezone(self):
        """Test syslog logs with a timezone info"""
        try:
            # Linux/Unix specific I guess ?
            localtz = pytz.timezone(file('/etc/timezone').read()[:-1])
        except:
            self.skipTest("Could not find local timezone, skipping test")    
        # Tokyo drift
        tokyo = pytz.timezone('Asia/Tokyo')
        offset = _get_timeoffset(tokyo,localtz)
        # first test the past
        now = datetime.now() + offset + timedelta(hours=-2)
        self.aS("<40>%s neo kernel: tun_wallix: Disabled Privacy Extensions" % now.strftime("%b %d %H:%M:%S"),
                {'body': 'tun_wallix: Disabled Privacy Extensions',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'neo',
                 'program': 'kernel',
                 'date': now.replace(microsecond=0)},
                 tzinfo = 'Asia/Tokyo')
        # then fight the future
        now = datetime.now() + offset + timedelta(hours=+2)
        self.aS("<40>%s neo kernel: tun_wallix: Disabled Privacy Extensions" % now.strftime("%b %d %H:%M:%S"),
                {'body': 'tun_wallix: Disabled Privacy Extensions',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'neo',
                 'program': 'kernel',
                 'date': now.replace(microsecond=0, year=now.year-1)},
                 tzinfo = 'Asia/Tokyo')
        # and finally, without the tz info ?
        now = datetime.now() + offset
        total_seconds = (offset.microseconds + (offset.seconds + offset.days * 24 * 3600) * 10**6) / 10**6
        # New in python 2.7
        #total_seconds = offset.total_seconds()
        if total_seconds > 60:
            d = now.replace(microsecond=0, year=now.year-1)
        else:
            d = now.replace(microsecond=0)
        self.aS("<40>%s neo kernel: tun_wallix: Disabled Privacy Extensions" % now.strftime("%b %d %H:%M:%S"),
                {'body': 'tun_wallix: Disabled Privacy Extensions',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'neo',
                 'program': 'kernel',
                 'date': d})
        # Operation Anchorage
        anchorage = pytz.timezone('America/Anchorage')
        offset = _get_timeoffset(anchorage,localtz)
        # first test the past
        now = datetime.now() + offset + timedelta(hours=-2)
        self.aS("<40>%s neo kernel: tun_wallix: Disabled Privacy Extensions" % now.strftime("%b %d %H:%M:%S"),
                {'body': 'tun_wallix: Disabled Privacy Extensions',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'neo',
                 'program': 'kernel',
                 'date': now.replace(microsecond=0)},
                 tzinfo = 'America/Anchorage')
        # then fight the future
        now = datetime.now() + offset + timedelta(hours=+2)
        self.aS("<40>%s neo kernel: tun_wallix: Disabled Privacy Extensions" % now.strftime("%b %d %H:%M:%S"),
                {'body': 'tun_wallix: Disabled Privacy Extensions',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'neo',
                 'program': 'kernel',
                 'date': now.replace(microsecond=0, year=now.year-1)},
                 tzinfo = 'America/Anchorage')
        # and finally, without the tz info ?
        now = datetime.now() + offset
        total_seconds = (offset.microseconds + (offset.seconds + offset.days * 24 * 3600) * 10**6) / 10**6
        # New in python 2.7
        #total_seconds = offset.total_seconds()
        if total_seconds > 60:
            d = now.replace(microsecond=0, year=now.year-1)
        else:
            d = now.replace(microsecond=0)
        self.aS("<40>%s neo kernel: tun_wallix: Disabled Privacy Extensions" % now.strftime("%b %d %H:%M:%S"),
                {'body': 'tun_wallix: Disabled Privacy Extensions',
                 'severity': 'emerg',
                 'severity_code' : '0',
                 'facility': 'syslog',
                 'facility_code' : '5',
                 'source': 'neo',
                 'program': 'kernel',
                 'date': d})
                 
    def test_postfix(self):
        """Test postfix logs"""
        self.aS("<40>Dec 21 07:49:02 hosting03 postfix/cleanup[23416]: 2BD731B4017: message-id=<20071221073237.5244419B327@paris.office.wallix.com>",
                {'program': 'postfix',
                 'component': 'cleanup',
                 'queue_id': '2BD731B4017',
                 'pid': '23416',
                 'message_id': '20071221073237.5244419B327@paris.office.wallix.com'})

#        self.aS("<40>Dec 21 07:49:01 hosting03 postfix/anvil[32717]: statistics: max connection rate 2/60s for (smtp:64.14.54.229) at Dec 21 07:40:04",
#                {'program': 'postfix',
#                 'component': 'anvil',
#                 'pid': '32717'})
#

        self.aS("<40>Dec 21 07:49:01 hosting03 postfix/pipe[23417]: 1E83E1B4017: to=<gloubi@wallix.com>, relay=vmail, delay=0.13, delays=0.11/0/0/0.02, dsn=2.0.0, status=sent (delivered via vmail service)",
                {'program': 'postfix',
                 'component': 'pipe',
                 'queue_id': '1E83E1B4017',
                 'message_recipient': 'gloubi@wallix.com',
                 'relay': 'vmail',
                 'dest_host': 'vmail',
                 'status': 'sent'})

        self.aS("<40>Dec 21 07:49:04 hosting03 postfix/smtpd[23446]: C43971B4019: client=paris.office.wallix.com[82.238.42.70]",
                {'program': 'postfix',
                 'component': 'smtpd',
                 'queue_id': 'C43971B4019',
                 'client': 'paris.office.wallix.com[82.238.42.70]',
                 'source_host': 'paris.office.wallix.com',
                 'source_ip': '82.238.42.70'})

#        self.aS("<40>Dec 21 07:52:56 hosting03 postfix/smtpd[23485]: connect from mail.gloubi.com[65.45.12.22]",
#                {'program': 'postfix',
#                 'component': 'smtpd',
#                 'ip': '65.45.12.22'})

        self.aS("<40>Dec 21 08:42:17 hosting03 postfix/pipe[26065]: CEFFB1B4020: to=<gloubi@wallix.com@autoreply.wallix.com>, orig_to=<gloubi@wallix.com>, relay=vacation, delay=4.1, delays=4/0/0/0.08, dsn=2.0.0, status=sent (delivered via vacation service)",
                {'program': 'postfix',
                 'component': 'pipe',
                 'message_recipient': 'gloubi@wallix.com@autoreply.wallix.com',
                 'orig_to': 'gloubi@wallix.com',
                 'relay': 'vacation',
                 'dest_host': 'vacation',
                 'status': 'sent'})

    def test_squid(self):
        """Test squid logs"""
        self.aS("<40>Dec 21 07:49:02 hosting03 squid[54]: 1196341497.777    784 127.0.0.1 TCP_MISS/200 106251 GET http://fr.yahoo.com/ vbe DIRECT/217.146.186.51 text/html",
                { 'program': 'squid',
                  'date': datetime(2007, 11, 29, 13, 4, 57, 777000),
                  'elapsed': '784',
                  'source_ip': '127.0.0.1',
                  'event_id': 'TCP_MISS',
                  'status': '200',
                  'len': '106251',
                  'method': 'GET',
                  'url': 'http://fr.yahoo.com/',
                  'user': 'vbe' })
        self.aS("<40>Dec 21 07:49:02 hosting03 : 1196341497.777    784 127.0.0.1 TCP_MISS/404 106251 GET http://fr.yahoo.com/gjkgf/gfgff/ - DIRECT/217.146.186.51 text/html",
                { 'program': 'squid',
                  'date': datetime(2007, 11, 29, 13, 4, 57, 777000),
                  'elapsed': '784',
                  'source_ip': '127.0.0.1',
                  'event_id': 'TCP_MISS',
                  'status': '404',
                  'len': '106251',
                  'method': 'GET',
                  'url': 'http://fr.yahoo.com/gjkgf/gfgff/' })
        self.aS("Oct 22 01:27:16 pluto squid: 1259845087.188     10 82.238.42.70 TCP_MISS/200 13121 GET http://ak.bluestreak.com//adv/sig/%5E16238/%5E7451318/VABT.swf?url_download=&width=300&height=250&vidw=300&vidh=250&startbbanner=http://ak.bluestreak.com//adv/sig/%5E16238/%5E7451318/vdo_300x250_in.swf&endbanner=http://ak.bluestreak.com//adv/sig/%5E16238/%5E7451318/vdo_300x250_out.swf&video_hd=http://aak.bluestreak.com//adv/sig/%5E16238/%5E7451318/vdo_300x250_hd.flv&video_md=http://ak.bluestreak.com//adv/sig/%5E16238/%5E7451318/vdo_300x250_md.flv&video_bd=http://ak.bluestreak.comm//adv/sig/%5E16238/%5E7451318/vdo_300x250_bd.flv&url_tracer=http%3A//s0b.bluestreak.com/ix.e%3Fpx%26s%3D8008666%26a%3D7451318%26t%3D&start=2&duration1=3&duration2=4&duration3=5&durration4=6&duration5=7&end=8&hd=9&md=10&bd=11&gif=12&hover1=13&hover2=14&hover3=15&hover4=16&hover5=17&hover6=18&replay=19&sound_state=off&debug=0&playback_controls=off&tracking_objeect=tracking_object_8008666&url=javascript:bluestreak8008666_clic();&rnd=346.2680651591202 fbo DIRECT/92.123.65.129 application/x-shockwave-flash",
                {'program' : "squid",
                 'date' : datetime.utcfromtimestamp(float(1259845087.188)),
                 'elapsed' : "10",
                 'source_ip' : "82.238.42.70",
                 'event_id' : "TCP_MISS",
                 'status' : "200",
                 'len' : "13121",
                 'method' : "GET",
                 'user' : "fbo",
                 'peer_status' : "DIRECT",
                 'peer_host' : "92.123.65.129",
                 'mime_type' : "application/x-shockwave-flash",
                 'url' : "http://ak.bluestreak.com//adv/sig/%5E16238/%5E7451318/VABT.swf?url_download=&width=300&height=250&vidw=300&vidh=250&startbbanner=http://ak.bluestreak.com//adv/sig/%5E16238/%5E7451318/vdo_300x250_in.swf&endbanner=http://ak.bluestreak.com//adv/sig/%5E16238/%5E7451318/vdo_300x250_out.swf&video_hd=http://aak.bluestreak.com//adv/sig/%5E16238/%5E7451318/vdo_300x250_hd.flv&video_md=http://ak.bluestreak.com//adv/sig/%5E16238/%5E7451318/vdo_300x250_md.flv&video_bd=http://ak.bluestreak.comm//adv/sig/%5E16238/%5E7451318/vdo_300x250_bd.flv&url_tracer=http%3A//s0b.bluestreak.com/ix.e%3Fpx%26s%3D8008666%26a%3D7451318%26t%3D&start=2&duration1=3&duration2=4&duration3=5&durration4=6&duration5=7&end=8&hd=9&md=10&bd=11&gif=12&hover1=13&hover2=14&hover3=15&hover4=16&hover5=17&hover6=18&replay=19&sound_state=off&debug=0&playback_controls=off&tracking_objeect=tracking_object_8008666&url=javascript:bluestreak8008666_clic();&rnd=346.2680651591202"})
        self.aS("<182>Feb 27 09:22:03 golden squid[32525]: 1330330923.254 119 10.10.5.5 TCP_MISS/302 667 GET http://c.astrocenter.fr/r.aspx?M=PRFREEV3_20120226_FR_24651456&L=http*3A*2F*2Fhoroscope.20minutes.fr*2F20Minutes*2Fimages*2FMailHeader*2Faf-0--4700-MailLogo.gif&O=685037391 - DIRECT/193.200.4.204 text/html",
                {'program' : "squid",
                 'date': datetime.utcfromtimestamp(float(1330330923.254)),
                 'elapsed' : "119",
                 "source_ip" : "10.10.5.5",
                 "event_id" : "TCP_MISS",
                 "status" : "302",
                 "len" : "667",
                 "method" : "GET",
                 'url' : "http://c.astrocenter.fr/r.aspx?M=PRFREEV3_20120226_FR_24651456&L=http*3A*2F*2Fhoroscope.20minutes.fr*2F20Minutes*2Fimages*2FMailHeader*2Faf-0--4700-MailLogo.gif&O=685037391"
                 })


    def test_netfilter(self):
        """Test netfilter logs"""
        self.aS("<40>Dec 26 09:30:07 dedibox kernel: FROM_INTERNET_DENY IN=eth0 OUT= MAC=00:40:63:e7:b2:17:00:15:fa:80:47:3f:08:00 SRC=88.252.4.37 DST=88.191.34.16 LEN=48 TOS=0x00 PREC=0x00 TTL=117 ID=56818 DF PROTO=TCP SPT=1184 DPT=445 WINDOW=65535 RES=0x00 SYN URGP=0",
                { 'program': 'netfilter',
                  'inbound_int': 'eth0',
                  'dest_mac': '00:40:63:e7:b2:17',
                  'source_mac': '00:15:fa:80:47:3f',
                  'source_ip': '88.252.4.37',
                  'dest_ip': '88.191.34.16',
                  'len': '48',
                  'protocol': 'TCP',
                  'source_port': '1184',
                  'prefix': 'FROM_INTERNET_DENY',
                  'dest_port': '445' })
        self.aS("<40>Dec 26 08:45:23 dedibox kernel: TO_INTERNET_DENY IN=vif2.0 OUT=eth0 SRC=10.116.128.6 DST=82.225.197.239 LEN=121 TOS=0x00 PREC=0x00 TTL=63 ID=15592 DF PROTO=TCP SPT=993 DPT=56248 WINDOW=4006 RES=0x00 ACK PSH FIN URGP=0 ",
                { 'program': 'netfilter',
                  'inbound_int': 'vif2.0',
                  'outbound_int': 'eth0',
                  'source_ip': '10.116.128.6',
                  'dest_ip': '82.225.197.239',
                  'len': '121',
                  'protocol': 'TCP',
                  'source_port': '993',
                  'dest_port': '56248' })
        
        # One malformed log
        self.aS("<40>Dec 26 08:45:23 dedibox kernel: TO_INTERNET_DENY IN=vif2.0 OUT=eth0 DST=82.225.197.239 LEN=121 TOS=0x00 PREC=0x00 TTL=63 ID=15592 DF PROTO=TCP SPT=993 DPT=56248 WINDOW=4006 RES=0x00 ACK PSH FIN URGP=0 ",
                { 'program': 'kernel' },
                ('inbound_int', 'len'))

        self.aS("Sep 28 15:19:59 tulipe-input kernel: [1655854.311830] DROPPED: IN=eth0 OUT= MAC=32:42:cd:02:72:30:00:23:7d:c6:35:e6:08:00 SRC=10.10.4.7 DST=10.10.4.86 LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=20805 DF PROTO=TCP SPT=34259 DPT=111 WINDOW=5840 RES=0x00 SYN URGP=0",
                {'program': 'netfilter',
                 'inbound_int' : "eth0",
                 'source_ip' : "10.10.4.7",
                 'dest_ip' : "10.10.4.86",
                 'len' : "60",
                 'protocol' : 'TCP',
                 'source_port' : '34259',
                 'dest_port' : '111',
                 'dest_mac' : '32:42:cd:02:72:30',
                 'source_mac' : '00:23:7d:c6:35:e6',
                 'prefix' : '[1655854.311830] DROPPED:' })


    def test_dhcpd(self):
        """Test DHCPd log normalization"""
        self.aS("<40>Dec 25 15:00:15 gnaganok dhcpd: DHCPDISCOVER from 02:1c:25:a3:32:76 via 183.213.184.122",
                { 'program': 'dhcpd',
                  'action': 'DISCOVER',
                  'source_mac': '02:1c:25:a3:32:76',
                  'via': '183.213.184.122' })
        self.aS("<40>Dec 25 15:00:15 gnaganok dhcpd: DHCPDISCOVER from 02:1c:25:a3:32:76 via vlan18.5",
                { 'program': 'dhcpd',
                  'action': 'DISCOVER',
                  'source_mac': '02:1c:25:a3:32:76',
                  'via': 'vlan18.5' })
        for log in [
            "DHCPOFFER on 183.231.184.122 to 00:13:ec:1c:06:5b via 183.213.184.122",
            "DHCPREQUEST for 183.231.184.122 from 00:13:ec:1c:06:5b via 183.213.184.122",
            "DHCPACK on 183.231.184.122 to 00:13:ec:1c:06:5b via 183.213.184.122",
            "DHCPNACK on 183.231.184.122 to 00:13:ec:1c:06:5b via 183.213.184.122",
            "DHCPDECLINE of 183.231.184.122 from 00:13:ec:1c:06:5b via 183.213.184.122 (bla)",
            "DHCPRELEASE of 183.231.184.122 from 00:13:ec:1c:06:5b via 183.213.184.122 for nonexistent lease" ]:
            self.aS("<40>Dec 25 15:00:15 gnaganok dhcpd: %s" % log,
                { 'program': 'dhcpd',
                  'source_ip': '183.231.184.122',
                  'source_mac': '00:13:ec:1c:06:5b',
                  'via': '183.213.184.122' })
        self.aS("<40>Dec 25 15:00:15 gnaganok dhcpd: DHCPINFORM from 183.231.184.122",
                { 'program': 'dhcpd',
                  'source_ip': '183.231.184.122',
                  'action': 'INFORM' })

    def test_sshd(self):
        """Test SSHd normalization"""
        self.aS("<40>Dec 26 10:32:40 naruto sshd[2274]: Failed password for bernat from 127.0.0.1 port 37234 ssh2",
                { 'program': 'sshd',
                  'action': 'fail',
                  'user': 'bernat',
                  'method': 'password',
                  'source_ip': '127.0.0.1' })
        self.aS("<40>Dec 26 10:32:40 naruto sshd[2274]: Failed password for invalid user jfdghfg from 127.0.0.1 port 37234 ssh2",
                { 'program': 'sshd',
                  'action': 'fail',
                  'user': 'jfdghfg',
                  'method': 'password',
                  'source_ip': '127.0.0.1' })
        self.aS("<40>Dec 26 10:32:40 naruto sshd[2274]: Failed none for invalid user kgjfk from 127.0.0.1 port 37233 ssh2",
                { 'program': 'sshd',
                  'action': 'fail',
                  'user': 'kgjfk',
                  'method': 'none',
                  'source_ip': '127.0.0.1' })
        self.aS("<40>Dec 26 10:32:40 naruto sshd[2274]: Accepted password for bernat from 127.0.0.1 port 37234 ssh2",
                { 'program': 'sshd',
                  'action': 'accept',
                  'user': 'bernat',
                  'method': 'password',
                  'source_ip': '127.0.0.1' })
        self.aS("<40>Dec 26 10:32:40 naruto sshd[2274]: Accepted publickey for bernat from 192.168.251.2 port 60429 ssh2",
                { 'program': 'sshd',
                  'action': 'accept',
                  'user': 'bernat',
                  'method': 'publickey',
                  'source_ip': '192.168.251.2' })
        # See http://www.ossec.net/en/attacking-loganalysis.html
        self.aS("<40>Dec 26 10:32:40 naruto sshd[2274]: Failed password for invalid user myfakeuser from 10.1.1.1 port 123 ssh2 from 192.168.50.65 port 34813 ssh2",
               { 'program': 'sshd',
                  'action': 'fail',
                  'user': 'myfakeuser from 10.1.1.1 port 123 ssh2',
                  'method': 'password',
                  'source_ip': '192.168.50.65' })
#        self.aS("Aug  1 18:30:05 knight sshd[20439]: Illegal user guest from 218.49.183.17",
#               {'program': 'sshd',
#                'source' : 'knight',
#                'user' : 'guest',
#                'source_ip': '218.49.183.17',
#                'body' : 'Illegal user guest from 218.49.183.17',
#                })

    def test_pam(self):
        """Test PAM normalization"""
        self.aS("<40>Dec 26 10:32:25 s_all@naruto sshd[2263]: pam_unix(ssh:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=localhost user=bernat",
                { 'program': 'ssh',
                  'component': 'pam_unix',
                  'type': 'auth',
                  'user': 'bernat' })
        self.aS("<40>Dec 26 10:09:01 s_all@naruto CRON[2030]: pam_unix(cron:session): session opened for user root by (uid=0)",
                { 'program': 'cron',
                  'component': 'pam_unix',
                  'type': 'session',
                  'user': 'root' })
        self.aS("<40>Dec 26 10:32:25 s_all@naruto sshd[2263]: pam_unix(ssh:auth): check pass; user unknown",
                { 'program': 'ssh',
                  'component': 'pam_unix',
                  'type': 'auth' })
        # This one should be better handled
        self.aS("<40>Dec 26 10:32:25 s_all@naruto sshd[2263]: pam_unix(ssh:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=localhost",
                { 'program': 'ssh',
                  'component': 'pam_unix',
                  'type': 'auth' })

    def test_lea(self):
        """Test LEA normalization"""
        self.aS("Oct 22 01:27:16 pluto lea: loc=7803|time=1199716450|action=accept|orig=fw1|i/f_dir=inbound|i/f_name=PCnet1|has_accounting=0|uuid=<47823861,00000253,7b040a0a,000007b6>|product=VPN-1 & FireWall-1|__policy_id_tag=product=VPN-1 & FireWall-1[db_tag={9F95C344-FE3F-4E3E-ACD8-60B5194BAAB4};mgmt=fw1;date=1199701916;policy_name=Standard]|src=naruto|s_port=36973|dst=fw1|service=941|proto=tcp|rule=1",
                {'program' : 'lea',
                 'id' : "7803",
                 'action' : "accept",
                 'source_host' : "naruto",
                 'source_port' : "36973",
                 'dest_host' : "fw1",
                 'dest_port' : "941",
                 'protocol' : "tcp",
                 'product' : "VPN-1 & FireWall-1",
                 'inbound_int' : "PCnet1"})

    def test_apache(self):
        """Test Apache normalization"""
        # Test Common Log Format (CLF) "%h %l %u %t \"%r\" %>s %O"
        self.aS("""127.0.0.1 - - [20/Jul/2009:00:29:39 +0300] "GET /index/helper/test HTTP/1.1" 200 889""",
                {'program' : "apache",
                 'source_ip' : "127.0.0.1",
                 'request' : 'GET /index/helper/test HTTP/1.1',
                 'len' : "889",
                 'date' : datetime(2009, 7, 20, 0, 29, 39), 
                 'body' : '127.0.0.1 - - [20/Jul/2009:00:29:39 +0300] "GET /index/helper/test HTTP/1.1" 200 889'})

        # Test "combined" log format  "%h %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\""
        self.aS('10.10.4.4 - - [04/Dec/2009:16:23:13 +0100] "GET /tulipe.core.persistent.persistent-module.html HTTP/1.1" 200 2937 "http://10.10.4.86/toc.html" "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20090910 Ubuntu/9.04 (jaunty) Shiretoko/3.5.3"',
                {'program' : "apache",
                 'source_ip' : "10.10.4.4",
                 'source_logname' : "-",
                 'user' : "-",
                 'date' : datetime(2009, 12, 4, 16, 23, 13),
                 'request' : 'GET /tulipe.core.persistent.persistent-module.html HTTP/1.1',
                 'status' : "200",
                 'len' : "2937",
                 'request_header_referer_contents' : "http://10.10.4.86/toc.html",
                 'useragent' : "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20090910 Ubuntu/9.04 (jaunty) Shiretoko/3.5.3",
                 'body' : '10.10.4.4 - - [04/Dec/2009:16:23:13 +0100] "GET /tulipe.core.persistent.persistent-module.html HTTP/1.1" 200 2937 "http://10.10.4.86/toc.html" "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20090910 Ubuntu/9.04 (jaunty) Shiretoko/3.5.3"'})

        # Test "vhost_combined" log format "%v:%p %h %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\""
        #TODO: Update apache normalizer to handle this format.


    def test_bind9(self):
        """Test Bind9 normalization"""
        self.aS("Oct 22 01:27:16 pluto named: client 192.168.198.130#4532: bad zone transfer request: 'www.abc.com/IN': non-authoritative zone (NOTAUTH)",
                {'event_id' : "zone_transfer_bad",
                 'zone' : "www.abc.com",
                 'source_ip' : '192.168.198.130',
                 'class' : 'IN',
                 'program' : 'named'})
        self.aS("Oct 22 01:27:16 pluto named: general: notice: client 10.10.4.4#39583: query: tpf.qa.ifr.lan IN SOA +",
                {'event_id' : "client_query",
                 'domain' : "tpf.qa.ifr.lan",
                 'category' : "general",
                 'severity' : "notice",
                 'class' : "IN",
                 'source_ip' : "10.10.4.4",
                 'program' : 'named'})
        self.aS("Oct 22 01:27:16 pluto named: createfetch: 126.92.194.77.zen.spamhaus.org A",
                {'event_id' : "fetch_request",
                 'domain' : "126.92.194.77.zen.spamhaus.org",
                 'program' : 'named'})

    def test_symantec8(self):
        """Test Symantec version 8 normalization"""
        self.aS("""200A13080122,23,2,8,TRAVEL00,SYSTEM,,,,,,,16777216,"Symantec AntiVirus Realtime Protection Loaded.",0,,0,,,,,0,,,,,,,,,,SAMPLE_COMPUTER,,,,Parent,GROUP,,8.0.93330""",
                {"program" : "symantec",
                 "date" : datetime(2002, 11, 19, 8, 1, 34),
                 "category" : "Summary",
                 "local_host" : "TRAVEL00",
                 "domain_name" : "GROUP",
                 "event_logger_type" : "System",
                 "event_id" : "GL_EVENT_RTS_LOAD",
                 "eventblock_action" : "EB_LOG",
                 "group_id" : "0",
                 "operation_flags" : "0",
                 "parent" : "SAMPLE_COMPUTER",
                 "scan_id" : "0",
                 "server_group" : "Parent",
                 "user" : "SYSTEM",
                 "version" : "8.0.93330"})

    # Need to find real symantec version 9 log lines
    def test_symantec9(self):
        """Test Symantec version 9 normalization"""
        self.aS("""200A13080122,23,2,8,TRAVEL00,SYSTEM,,,,,,,16777216,"Symantec AntiVirus Realtime Protection Loaded.",0,,0,,,,,0,,,,,,,,,,SAMPLE_COMPUTER,,,,Parent,GROUP,,9.0.93330,,,,,,,,,,,,,,,,,,,,""",
                {"program" : "symantec",
                 "date" : datetime(2002, 11, 19, 8, 1, 34),
                 "category" : "Summary",
                 "local_host" : "TRAVEL00",
                 "domain_name" : "GROUP",
                 "event_logger_type" : "System",
                 "event_id" : "GL_EVENT_RTS_LOAD",
                 "eventblock_action" : "EB_LOG",
                 "group_id" : "0",
                 "operation_flags" : "0",
                 "parent" : "SAMPLE_COMPUTER",
                 "scan_id" : "0",
                 "server_group" : "Parent",
                 "user" : "SYSTEM",
                 "version" : "9.0.93330"})
    
    def test_arkoonFAST360(self):
        """Test Arkoon FAST360 normalization"""
        self.aS('AKLOG-id=firewall time="2004-02-25 17:38:57" fw=myArkoon aktype=IP gmtime=1077727137 ip_log_type=ENDCONN src=10.10.192.61 dst=10.10.192.255 proto="137/udp" protocol=17 port_src=137 port_dest=137 intf_in=eth0 intf_out= pkt_len=78 nat=NO snat_addr=0 snat_port=0 dnat_addr=0 dnat_port=0 user="userName" pri=3 rule="myRule" action=DENY reason="Blocked by filter" description="dst addr received from Internet is private"',
                {"program" : "arkoon",
                 "date" : datetime(2004, 02, 25, 16, 38, 57),
                 "event_id" : "IP",
                 "priority" : "3",
                 "local_host" : "myArkoon",
                 "user" : "userName",
                 "protocol": "udp",
                 "dest_ip" : "10.10.192.255",
                 "source_ip" : "10.10.192.61",
                 "reason" : "Blocked by filter",
                 "ip_log_type" : "ENDCONN",
                 "body" : 'id=firewall time="2004-02-25 17:38:57" fw=myArkoon aktype=IP gmtime=1077727137 ip_log_type=ENDCONN src=10.10.192.61 dst=10.10.192.255 proto="137/udp" protocol=17 port_src=137 port_dest=137 intf_in=eth0 intf_out= pkt_len=78 nat=NO snat_addr=0 snat_port=0 dnat_addr=0 dnat_port=0 user="userName" pri=3 rule="myRule" action=DENY reason="Blocked by filter" description="dst addr received from Internet is private"'})

        # Assuming this kind of log with syslog like header is typically sent over the wire.
        self.aS('<134>IP-Logs: AKLOG - id=firewall time="2010-10-04 10:38:37" gmtime=1286181517 fw=doberman.jurassic.ta aktype=IP ip_log_type=NEWCONN src=172.10.10.107 dst=204.13.8.181 proto="http" protocol=6 port_src=2619 port_dest=80 intf_in=eth7 intf_out=eth2 pkt_len=48 nat=HIDE snat_addr=10.10.10.199 snat_port=16176 dnat_addr=0 dnat_port=0 tcp_seq=1113958286 tcp_ack=0 tcp_flags="SYN" user="" vpn-src="" pri=6 rule="surf_normal" action=ACCEPT',
                {'program': 'arkoon',
                 'event_id': 'IP',
                 'rule': 'surf_normal',
                 'ip_log_type': 'NEWCONN'})
        
        # This one must not match the arkoonFAST360 parser
        # Assuming this king of log does not exist
        self.aS('<40>Dec 21 08:42:17 hosting arkoon: <134>IP-Logs: AKLOG - id=firewall time="2010-10-04 10:38:37" gmtime=1286181517 fw=doberman.jurassic.ta aktype=IP ip_log_type=NEWCONN src=172.10.10.107 dst=204.13.8.181 proto="http" protocol=6 port_src=2619 port_dest=80 intf_in=eth7 intf_out=eth2 pkt_len=48 nat=HIDE snat_addr=10.10.10.199 snat_port=16176 dnat_addr=0 dnat_port=0 tcp_seq=1113958286 tcp_ack=0 tcp_flags="SYN" user="" vpn-src="" pri=6 rule="surf_normal" action=ACCEPT',
                {'program': 'arkoon'}, # program is set by syslog parser
                ('event_id', 'rule', 'ip_log_type'))
    
    def test_MSExchange2007MTL(self):
        """Test Exchange 2007 message tracking log normalization"""
        self.aS("""2010-04-19T12:29:07.390Z,10.10.14.73,WIN2K3DC,,WIN2K3DC,"MDB:ada3d2c3-6f32-45db-b1ee-a68dbcc86664, Mailbox:68cf09c1-1344-4639-b013-3c6f8a588504, Event:1440, MessageClass:IPM.Note, CreationTime:2010-04-19T12:28:51.312Z, ClientType:User",,STOREDRIVER,SUBMIT,,<C6539E897AEDFA469FE34D029FB708D43495@win2k3dc.qa.ifr.lan>,,,,,,,Coucou !,user7@qa.ifr.lan,,""",
                {'mdb': 'ada3d2c3-6f32-45db-b1ee-a68dbcc86664',
                 'source_host': 'WIN2K3DC',
                 'source_ip': '10.10.14.73',
                 'client_type': 'User',
                 'creation_time': 'Mon Apr 19 12:28:51 2010',
                 'date': datetime(2010, 4, 19, 12, 29, 7, 390000),
                 'event': '1440',
                 'event_id': 'SUBMIT',
                 'exchange_source': 'STOREDRIVER',
                 'mailbox': '68cf09c1-1344-4639-b013-3c6f8a588504',
                 'message_class': 'IPM.Note',
                 'message_id': 'C6539E897AEDFA469FE34D029FB708D43495@win2k3dc.qa.ifr.lan',
                 'message_subject': 'Coucou !',
                 'program': 'MS Exchange 2007 Message Tracking',
                 'dest_host': 'WIN2K3DC'})

    def test_S3(self):
        """Test Amazon S3 bucket log normalization"""
        self.aS("""DEADBEEF testbucket [19/Jul/2011:13:17:11 +0000] 10.194.22.16 FACEDEAD CAFEDECA REST.GET.ACL - "GET /?acl HTTP/1.1" 200 - 951 - 397 - "-" "Jakarta Commons-HttpClient/3.0" -""",
                {'source_ip': '10.194.22.16',
                 'http_method': 'GET',
                 'protocol': 'HTTP/1.1',
                 'status': '200',
                 'user': 'DEADBEEF',
                 'method': 'REST.GET.ACL',
                 'program': 's3'})

    def test_Snare(self):
        """Test Snare for Windows log normalization"""
	self.aS(unicode("""<13> Aug 31 15:46:47 a-zA-Z0-9_ MSWinEventLog	1	System	287	ven. août 26 16:45:45 201	4	Virtual Disk Service	Constantin	N/A	Information	a-zA-Z0-9_	None	 Le service s’est arrêté.	119 """, 'utf8'),
                {'snare_event_log_type': 'MSWinEventLog',
                 'criticality': '1',
                 'event_log_source_name': 'System',
                 'snare_event_counter': '287',
                 'event_id': '4',
                 'event_log_expanded_source_name': 'Virtual Disk Service',
                 'user': 'Constantin',
                 'sid_used': 'N/A',
                 'event_type': 'Information',
                 'source_host': 'a-zA-Z0-9_',
                 'audit_event_category': 'None',
                 'program' : 'EventLog',
                 'body': unicode('Le service s’est arrêté.	119 ', 'utf8')})

	self.aS(unicode("""<13> Aug 31 15:46:47 a-zA-Z0-9_ MSWinEventLog	0	Security	284	ven. août 26 16:42:01 201	4689	Microsoft-Windows-Security-Auditing	A-ZA-Z0-9_\\clo	N/A	Success Audit	a-zA-Z0-9_	Fin du processus	 Un processus est terminé. Sujet : ID de sécurité : S-1-5-21-2423214773-420032381-3839276281-1000 Nom du compte : clo Domaine du compte : A-ZA-Z0-9_ ID d’ouverture de session : 0x21211 Informations sur le processus : ID du processus : 0xb4c Nom du processus : C:\\Windows\\System32\\taskeng.exe État de fin : 0x0	138 """, 'utf8'),
                {'snare_event_log_type': 'MSWinEventLog',
                 'criticality': '0',
                 'event_log_source_name': 'Security',
                 'snare_event_counter': '284',
                 'event_id': '4689',
                 'event_log_expanded_source_name': 'Microsoft-Windows-Security-Auditing',
                 'user': 'A-ZA-Z0-9_\\clo',
                 'sid_used': 'N/A',
                 'event_type': 'Success Audit',
                 'source_host': 'a-zA-Z0-9_',
                 'audit_event_category': 'Fin du processus',
                 'program' : "EventLog",
                 'body': unicode('Un processus est terminé. Sujet : ID de sécurité : S-1-5-21-2423214773-420032381-3839276281-1000 Nom du compte : clo Domaine du compte : A-ZA-Z0-9_ ID d’ouverture de session : 0x21211 Informations sur le processus : ID du processus : 0xb4c Nom du processus : C:\\Windows\\System32\\taskeng.exe État de fin : 0x0	138 ', 'utf8')})

    def test_vmwareESX4_ESXi4(self):
	"""Test VMware ESX 4.x and VMware ESXi 4.x log normalization"""
	self.aS("""[2011-09-05 16:06:30.016 F4CD1B90 verbose 'Locale' opID=996867CC-000002A6] Default resource used for 'host.SystemIdentificationInfo.IdentifierType.ServiceTag.summary' expected in module 'enum'.""",
		{'date': datetime(2011, 9, 5, 16, 6, 30),
	 	 'numeric': 'F4CD1B90',
	 	 'level': 'verbose',
	 	 'alpha': 'Locale',
	 	 'body': 'Default resource used for \'host.SystemIdentificationInfo.IdentifierType.ServiceTag.summary\' expected in module \'enum\'.'})

	self.aS("""sysboot: Executing 'kill -TERM 314'""",
		{'body': 'Executing \'kill -TERM 314\''})

#    def test_mysql(self):
#	"""Test mysql log normalization"""
#	self.aS("""110923 11:04:58	   36 Query	show databases""",
#		{'date': datetime(2011, 9, 23, 11, 4, 58),
#		 'id': '36',
#	 	 'type': 'Query',
#	 	 'event': 'show databases'})
#	self.aS("""110923 10:09:11 [Note] Plugin 'FEDERATED' is disabled.""",
#		{'date': datetime(2011, 9, 23, 10, 9, 11),
#	 	 'component': 'Note',
#	 	 'event': 'Plugin \'FEDERATED\' is disabled.'})

    def test_IIS(self):
	"""Test IIS log normalization"""
	self.aS("""172.16.255.255, anonymous, 03/20/01, 23:58:11, MSFTPSVC, SALES1, 172.16.255.255, 60, 275, 0, 0, 0, PASS, /Intro.htm, -,""",
		{'source_ip': '172.16.255.255',
		 'user': 'anonymous',
		 'date': datetime(2001, 3, 20, 23, 58, 11),
		 'service': 'MSFTPSVC',
		 'dest_host': 'SALES1',
		 'dest_ip': '172.16.255.255',
		 'time_taken': 0.06,
		 'sent_bytes_number': '275',
		 'returned_bytes_number': '0',
		 'status': '0',
		 'windows_status_code': '0',
		 'method': 'PASS',
		 'url_path': '/Intro.htm',
		 'script_parameters': '-'})

	self.aS("""2011-09-26 13:57:48 W3SVC1 127.0.0.1 GET /tapage.asp - 80 - 127.0.0.1 Mozilla/4.0+(compatible;MSIE+6.0;+windows+NT5.2;+SV1;+.NET+CLR+1.1.4322) 404 0 2""",
		{'date': datetime(2011, 9, 26, 13, 57, 48),
		'service': 'W3SVC1',
		'dest_ip': '127.0.0.1',
		'method': 'GET',
		'url_path': '/tapage.asp',
		'query': '-',
		'port': '80',
		'user': '-',
		'source_ip': '127.0.0.1',
		'useragent': 'Mozilla/4.0+(compatible;MSIE+6.0;+windows+NT5.2;+SV1;+.NET+CLR+1.1.4322)',
		'status': '404',
		'substatus': '0',
		'win_status': '2'})

    def test_fail2ban(self):
        """Test fail2ban ssh banishment logs"""
        self.aS("""2011-09-25 05:09:02,371 fail2ban.filter : INFO   Log rotation detected for /var/log/auth.log""",
                {'program' : 'fail2ban',
                 'component' : 'filter',
                 'body' : "Log rotation detected for /var/log/auth.log",
                 'date' : datetime(2011,9,25,5,9,2).replace(microsecond = 371000)})
        self.aS("""2011-09-25 21:59:24,304 fail2ban.actions: WARNING [ssh] Ban 219.117.199.6""",
                {'program' : 'fail2ban',
                 'component' : 'actions',
                 'action' : "Ban",
                 'protocol' : "ssh",
                 'source_ip' : "219.117.199.6",
                 'date' : datetime(2011,9,25,21,59,24).replace(microsecond = 304000)})
                 
    def test_bitdefender(self):
        """Test bitdefender spam.log (Mail Server for UNIX version)"""
        self.aS('10/20/2011 07:24:26 BDMAILD SPAM: sender: marcelo@nitex.com.br, recipients: re@corp.com, sender IP: 127.0.0.1, subject: "Lago para pesca, piscina, charrete, Hotel Fazenda", score: 1000, stamp: " v1, build 2.10.1.12405, blacklisted, total: 1000(750)", agent: Smtp Proxy 3.1.3, action: drop (move-to-quarantine;drop), header recipients: ( "cafe almoço e janta incluso" ), headers: ( "Received: from localhost [127.0.0.1] by BitDefender SMTP Proxy on localhost [127.0.0.1] for localhost [127.0.0.1]; Thu, 20 Oct 2011 07:24:26 +0200 (CEST)" "Received: from paris.office.corp.com (go.corp.lan [10.10.1.254]) by as-bd-64.ifr.lan (Postfix) with ESMTP id 4D23D1C7    for <regis.wira@corp.com>; Thu, 20 Oct 2011 07:24:26 +0200 (CEST)" "Received: from rj50ssp.nitex.com.br (rj154ssp.nitex.com.br [177.47.99.154])    by paris.office.corp.com (Postfix) with ESMTP id 28C0D6A4891    for <re@corp.com>; Thu, 20 Oct 2011 07:17:59 +0200 (CEST)" "Received: from rj154ssp.nitex.com.br (ced-sp.tuavitoria.com.br [177.47.99.13])    by rj50ssp.nitex.com.br (Postfix) with ESMTP id 9B867132C9E;    Wed, 19 Oct 2011 22:29:20 -0200 (BRST)" ), group: "Default"',
                {'message_sender' : 'marcelo@nitex.com.br',
                 'program' : 'bitdefender',
                 'action' : 'drop',
                 'message_recipients' : 're@corp.com',
                 'date' : datetime(2011,10,20,07,24,26),
                 'reason' : 'blacklisted'})

        self.aS('10/24/2011 04:31:39 BDSCAND ERROR: failed to initialize the AV core',
                {'program' : 'bitdefender',
                 'body' : 'failed to initialize the AV core',
                 'date' : datetime(2011,10,24,04,31,39)})

    def test_simple_wabauth(self):
        """Test syslog logs"""
        self.aS("Dec 20 17:20:22 wab2 WAB(CORE)[18190]: type='session closed' username='admin' secondary='root@debian32' client_ip='10.10.4.25' src_protocol='SFTP_SESSION' dst_protocol='SFTP_SESSION' message=''",
                { 'account': 'root',
                  'client_ip': '10.10.4.25',
                  'date': datetime(2011, 12, 20, 17, 20, 22),
                  'dest_proto': 'SFTP_SESSION',
                  'message': '',
                  'pid': '18190',
                  'program': 'WAB(CORE)',
                  'resource': 'debian32',
                  'source': 'wab2',
                  'source_proto': 'SFTP_SESSION',
                  'type': 'session closed',
                  'username': 'admin'})

        self.aS("Dec 20 17:19:35 wab2 WAB(CORE)[18190]: type='primary_authentication' timestamp='2011-12-20 17:19:35.621952' username='admin' client_ip='10.10.4.25' diagnostic='SUCCESS'",
                {'client_ip': '10.10.4.25',
                 'date': datetime(2011, 12, 20, 17, 19, 35),
                 'diagnostic': 'SUCCESS',
                 'pid': '18190',
                 'program': 'WAB(CORE)',
                 'source': 'wab2',
                 'type': 'primary_authentication',
                 'username': 'admin'})

        self.aS("Dec 20 17:19:35 wab2 WAB(CORE)[18190]: type='session opened' username='admin' secondary='root@debian32' client_ip='10.10.4.25' src_protocol='SFTP_SESSION' dst_protocol='SFTP_SESSION' message=''",
                { 'account': 'root',
                  'client_ip': '10.10.4.25',
                  'date': datetime(2011, 12, 20, 17, 19, 35),
                  'dest_proto': 'SFTP_SESSION',
                  'message': '',
                  'pid': '18190',
                  'program': 'WAB(CORE)',
                  'resource': 'debian32',
                  'source': 'wab2',
                  'source_proto': 'SFTP_SESSION',
                  'type': 'session opened',
                  'username': 'admin'})

    def test_xferlog(self):
        """Testing xferlog formatted logs"""
        self.aS("Thu Sep 2 09:52:00 2004 50 192.168.20.10 896242 /home/test/file1.tgz b _ o r suporte ftp 0 * c ",
                {'transfer_time' : '50',
                 'source_ip' : '192.168.20.10',
                 'len' : '896242',
                 'filename' : '/home/test/file1.tgz',
                 'transfer_type_code' : 'b',
                 'special_action_flag' : '_',
                 'direction_code' : 'o',
                 'access_mode_code' : 'r',
                 'completion_status_code' : 'c',
                 'authentication_method_code' : '0',
                 'transfer_type' : 'binary',
                 'special_action' : 'none',
                 'direction' : 'outgoing',
                 'access_mode' : 'real',
                 'completion_status' : 'complete',
                 'authentication_method' : 'none',
                 'user' : 'suporte',
                 'service_name' : 'ftp',
                 'authenticated_user_id' : '*',
                 'program' : 'ftpd',
                 'date' : datetime(2004,9,2,9,52),})
        self.aS("Tue Dec 27 11:24:23 2011 1 127.0.0.1 711074 /home/mhu/Documents/Brooks,_Max_-_World_War_Z.mobi b _ o r mhu ftp 0 * c",
                {'transfer_time' : '1',
                 'source_ip' : '127.0.0.1',
                 'len' : '711074',
                 'filename' : '/home/mhu/Documents/Brooks,_Max_-_World_War_Z.mobi',
                 'transfer_type_code' : 'b',
                 'special_action_flag' : '_',
                 'direction_code' : 'o',
                 'access_mode_code' : 'r',
                 'completion_status_code' : 'c',
                 'authentication_method_code' : '0',
                 'transfer_type' : 'binary',
                 'special_action' : 'none',
                 'direction' : 'outgoing',
                 'access_mode' : 'real',
                 'completion_status' : 'complete',
                 'authentication_method' : 'none',
                 'user' : 'mhu',
                 'service_name' : 'ftp',
                 'authenticated_user_id' : '*',
                 'program' : 'ftpd',
                 'date' : datetime(2011,12,27,11,24,23),}) 
 
    def test_dansguardian(self):
        """Testing dansguardian logs"""
        self.aS("2011.12.13 10:41:28 10.10.42.23 10.10.42.23 http://safebrowsing.clients.google.com/safebrowsing/downloads?client=Iceweasel&appver=3.5.16&pver=2.2&wrkey=AKEgNityGqylPYNyNETvnRjDjo4mIKcwv7f-8UCJaKERjXG6cXrikbgdA0AG6J8A6zng73h9U1GoE7P5ZPn0dDLmD_t3q1csCw== *EXCEPTION* Site interdit trouv&ecute;. POST 491 0  2 200 -  limited_access -",
                {'program' : 'dansguardian',
                 'user' : '10.10.42.23',
                 'source_ip' : '10.10.42.23',
                 'url' : 'http://safebrowsing.clients.google.com/safebrowsing/downloads?client=Iceweasel&appver=3.5.16&pver=2.2&wrkey=AKEgNityGqylPYNyNETvnRjDjo4mIKcwv7f-8UCJaKERjXG6cXrikbgdA0AG6J8A6zng73h9U1GoE7P5ZPn0dDLmD_t3q1csCw==',
                 'actions' : "*EXCEPTION*",
                 'action' : 'EXCEPTION',
                 'reason' : "Site interdit trouv&ecute;.",
                 "method" : "POST",
                 "len" : "491",
                 "naughtiness" : "0",
                 "filter_group_number" : "2",
                 "status" : "200",
                 "mime_type" : "-",
                 "filter_group_name" : "limited_access",
                 'date' : datetime(2011,12,13,10,41,28),})

    def test_deny_event(self):
        """Testing denyAll event logs"""
        self.aS("""224,2011-01-24 17:44:46.061903,2011-01-24 17:44:46.061903,,,192.168.219.10,127.0.0.1,,2,1,4,0,"Session opened (read-write), Forwarded for 192.168.219.1.",superadmin,gui,,{403ec510-27d9-11e0-bbe7-000c298895c5}Session,,,,,,,,,,,,,,,,,,,,""",
                {'alert_id': '0',
                 'alert_subtype': 'Access',
                 'alert_subtype_id': '1',
                 'alert_type': 'System',
                 'alert_type_id': '2',
                 'alert_value': 'Session opened (read-write), Forwarded for 192.168.219.1.',
                 'body': '224,2011-01-24 17:44:46.061903,2011-01-24 17:44:46.061903,,,192.168.219.10,127.0.0.1,,2,1,4,0,"Session opened (read-write), Forwarded for 192.168.219.1.",superadmin,gui,,{403ec510-27d9-11e0-bbe7-000c298895c5}Session,,,,,,,,,,,,,,,,,,,,',
                 'date': datetime(2011, 1, 24, 17, 44, 46),
                 'end_date': '2011-01-24 17:44:46.061903',
                 'event': 'User successful login',
                 'event_uid': '224',
                 'interface': 'gui',
                 'ip_device': '192.168.219.10',
                 'parameter_changed': '{403ec510-27d9-11e0-bbe7-000c298895c5}Session',
                 'raw': '224,2011-01-24 17:44:46.061903,2011-01-24 17:44:46.061903,,,192.168.219.10,127.0.0.1,,2,1,4,0,"Session opened (read-write), Forwarded for 192.168.219.1.",superadmin,gui,,{403ec510-27d9-11e0-bbe7-000c298895c5}Session,,,,,,,,,,,,,,,,,,,,',
                 'severity': 'Warn',
                 'severity_code': '4',
                 'source_ip': '127.0.0.1',
                 'user': 'superadmin'})
        self.aS("""1,2011-01-20 15:09:38.130965,2011-01-20 15:09:38.130965,,,::1,,,2,2,5,0,rWeb started.,,,,,,,,,,,,,,,,,,,,,,,,""",
               {'alert_id': '0',
                'alert_subtype': 'Device Operations',
                'alert_subtype_id': '2',
                'alert_type': 'System',
                'alert_type_id': '2',
                'alert_value': 'rWeb started.',
                'body': '1,2011-01-20 15:09:38.130965,2011-01-20 15:09:38.130965,,,::1,,,2,2,5,0,rWeb started.,,,,,,,,,,,,,,,,,,,,,,,,',
                'date': datetime(2011, 1, 20, 15, 9, 38),
                'end_date': '2011-01-20 15:09:38.130965',
                'event': 'rWeb started',
                'event_uid': '1',
                'ip_device': '::1',
                'raw': '1,2011-01-20 15:09:38.130965,2011-01-20 15:09:38.130965,,,::1,,,2,2,5,0,rWeb started.,,,,,,,,,,,,,,,,,,,,,,,,',
                'severity': 'Notice',
                'severity_code': '5'} )

    def test_cisco_asa(self):
        """Testing CISCO ASA logs"""
        self.aS("""<168>Mar 05 2010 11:06:12 ciscoasa : %ASA-6-305011: Built dynamic TCP translation from 14net:14.36.103.220/300 to 172net:172.18.254.146/55""",
               {'program': 'cisco-asa',
                'severity_code': '6',
                'event_id': '305011',
                'date': datetime(2010, 3, 5, 11, 6, 12),
                'taxonomy': 'firewall',
                'outbound_int': '172net',
                'dest_port': '55'})
        self.aS("""<168>Jul 02 2006 07:33:45 ciscoasa : %ASA-6-302013: Built outbound TCP connection 8300517 for outside:64.156.4.191/110 (64.156.4.191/110) to inside:192.168.8.12/3109 (xxx.xxx.185.142/11310)""",
               {'program': 'cisco-asa',
                'severity_code': '6',
                'event_id': '302013',
                'date': datetime(2006, 7, 2, 7, 33, 45),
                'taxonomy': 'firewall',
                'outbound_int': 'inside',
                'dest_ip': '192.168.8.12'})

    def test_openLDAP(self):
        """Testing openLDAP logs"""
        self.aS("""Jun 12 11:18:47 openLDAP slapd[870]: conn=1007 op=0 RESULT tag=97 err=53 text=unauthenticated bind (DN with no password) disallowed""",
               {'program': 'slapd',
                'source': 'openLDAP',
                'connection_id' : '1007',
                'operation_id' : '0',
                'action' : 'RESULT',
                'tag_code' : '97',
                'error_code': '53',
                'response_type' : 'Bind',
                'status' : 'Service error - unwilling to perform',
                'reason' : 'unauthenticated bind (DN with no password) disallowed',
                })
        self.aS('Jun 12 11:14:20 openLDAP slapd[870]: conn=1002 op=0 SRCH base="" scope=0 deref=0 filter="(objectClass=*)"',
               {'program': 'slapd',
                'source': 'openLDAP',
                'connection_id' : '1002',
                'operation_id' : '0',
                'action' : 'SRCH',
                'deref' : '0',
                'scope_code': '0',
                'scope' : 'base',
                'filter' : '(objectClass=*)',
                })
        self.aS('Jun 11 15:52:37 openLDAP slapd[1814]: conn=1012 fd=14 ACCEPT from IP=10.10.4.7:39450 (IP=10.10.4.250:389)',
               {'program': 'slapd',
                'source': 'openLDAP',
                'connection_id' : '1012',
                'socket_id' : '14',
                'action' : 'ACCEPT',
                'source_ip' : '10.10.4.7',
                'source_port': '39450',
                'local_ip' : '10.10.4.250',
                'local_port' : '389',
                })
        


if __name__ == "__main__":
    unittest.main()
