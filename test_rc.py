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
import pickle
import logging
from logging.config import fileConfig

from config import REDIS_KEY
from Image import ImageObj
from pywikibot.throttle import Throttle
logger = None


def run_watcher():
    global logger
    site = pywikibot.Site(user="TheSandBot")
    site._throttle = Throttle(site, multiplydelay=False)
    site.lock_page = lambda *args, **kwargs: None  # noop
    site.unlock_page = lambda *args, **kwargs: None  # noop
    rc = site_rc_listener(site)
    for change in rc:

        if (
            change['type'] == 'log' and
            change['namespace'] == 6 and
            change['log_type'] == 'upload'
        ):
            logger.debug(change['title'])
            file_page = pywikibot.FilePage(site, change['title'])
            #redis.rpush(REDIS_KEY, json.dumps(change))
            #redis.rpush(REDIS_KEY, ImageObj(json.dumps(change)))

    logger.critical("Exit - THIS SHOULD NOT HAPPEN")


def main():
    pywikibot.handle_args()
    run_watcher()


if __name__ == "__main__":
    fileConfig('logging_config.ini')
    logger = logging.getLogger(__name__)

    try:
        main()
    except KeyboardInterrupt:
        logger.critical("Watcher shutdown")
    finally:
        pywikibot.stopme()
