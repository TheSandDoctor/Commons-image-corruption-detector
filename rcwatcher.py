#! /usr/bin/env python
# -*- coding: UTF-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General License for more details.
#
# You should have received a copy of the GNU General License
# along with self program.  If not, see <http://www.gnu.org/licenses/>
#

# From https://github.com/toolforge/embeddeddata/blob/5ecd31417a4c3c5d1be9c2a58f55a1665d9c767f/rcwatcher.py
# not yet integrated


import json
from redis import Redis
import pywikibot
from pywikibot.comms.eventstreams import site_rc_listener

from config import REDIS_KEY
from Image import ImageObj


def run_watcher():
    site = pywikibot.Site(user="TheSandBot")
    redis = Redis(host="localhost")

    rc = site_rc_listener(site)
    for change in rc:

        if (
            change['type'] == 'log' and
            change['namespace'] == 6 and
            change['log_type'] == 'upload'
        ):
            #redis.rpush(REDIS_KEY, json.dumps(change))
            #redis.rpush(REDIS_KEY, ImageObj(json.loads(change)))
            if change['title'] == "WARNING: Empty message found.":
                print("CAUGHT: " + change['title'])
            else:
                print(change['title'])

    pywikibot.output("Exit - THIS SHOULD NOT HAPPEN")


def main():
    pywikibot.handle_args()
    run_watcher()


if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
