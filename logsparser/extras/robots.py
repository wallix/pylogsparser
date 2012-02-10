# -*- coding: utf-8 -*-

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

"""In this module we define a regular expression used to fetch the most common
robots."""

import re

# taken from genrobotlist.pl in the awstats project : http://awstats.cvs.sourceforge.net
robots = [
    'antibot',
    'appie',
    'architext',
    'bingbot',
    'bjaaland',
    'digout4u',
    'echo',
    'fast-webcrawler',
    'ferret',
    'googlebot',
    'gulliver',
    'harvest',
    'htdig',
    'ia_archiver',
    'askjeeves',
    'jennybot',
    'linkwalker',
    'lycos',
    'mercator',
    'moget',
    'muscatferret',
    'myweb',
    'netcraft',
    'nomad',
    'petersnews',
    'scooter',
    'slurp',
    'unlost_web_crawler',
    'voila',
    'voyager',
    'webbase',
    'weblayers',
    'wisenutbot',
    'aport',
    'awbot',
    'baiduspider',
    'bobby',
    'boris',
    'bumblebee',
    'cscrawler',
    'daviesbot',
    'exactseek',
    'ezresult',
    'gigabot',
    'gnodspider',
    'grub',
    'henrythemiragorobot',
    'holmes',
    'internetseer',
    'justview',
    'linkbot',
    'metager-linkchecker',
    'linkchecker',
    'microsoft_url_control',
    'msiecrawler',
    'nagios',
    'perman',
    'pompos',
    'rambler',
    'redalert',
    'shoutcast',
    'slysearch',
    'surveybot',
    'turnitinbot',
    'turtlescanner',
    'turtle',
    'ultraseek',
    'webclipping.com',
    'webcompass',
    'yahoo-verticalcrawler',
    'yandex',
    'zealbot',
    'zyborg',
]
robot_regex = re.compile("|".join(robots), re.IGNORECASE)
