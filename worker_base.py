# -*- coding: UTF-8 -*-
from datetime import timezone, datetime
import os
import shutil
import tempfile
import traceback
import uuid
import logging
from logging.config import fileConfig
from sys import exc_info
import requests

import pywikibot
from pywikibot.throttle import Throttle

import pwb_wrappers
from database_stuff import store_image, get_next_month
from image_corruption_utils import image_is_corrupt, notify_user, allow_bots, get_local_hash, get_remote_hash
from config import REDIS_KEY
from PIL import UnidentifiedImageError
from redis import Redis
from Image import ImageObj  # Despite IDE warnings, this is used implicitly by pickle & cannot be removed as a result
from EUtils import EDayCount, EJobType
from EDirections import EDirections
import pickle


def tag_page(file_page):
    nom_date = str(get_next_month(7)).split('/')
    pwb_wrappers.tag_page(file_page,
                          "{{TSB image identified corrupt|"
                          + datetime.now(
                              timezone.utc).strftime("%m/%d/%Y") + "|day=" +
                          nom_date[1] + "|month=" + nom_date[0] + "|year=" + nom_date[2] + "}}",
                          "Image detected as corrupt, tagging.")
    # store_image(file_page.title(), True, img_hash=change.hash, day_count=7)  # store in database


class WorkerBase():
    def __init__(self, direction):
        self.direction = direction
        self.site = pywikibot.Site(user="TheSandBot")
        self.site._throttle = Throttle(self.site, multiplydelay=False)
        self.site.lock_page = lambda *args, **kwargs: None  # noop
        self.site.unlock_page = lambda *args, **kwargs: None  # noop
        self.redis = Redis(host="localhost")

        fileConfig('logging_config.ini')
        self.logger = logging.getLogger(__name__)

    def run_worker(self):
        tmpdir = None  # Gets rid of IDE complaint/warning about access before assignment
        try:
            tmpdir = tempfile.mkdtemp()

            while True:
                if self.direction == EDirections.LEFT:
                    _, picklemsg = self.redis.blpop(REDIS_KEY)
                else:
                    _, picklemsg = self.redis.brpop(REDIS_KEY)
                change = pickle.loads(picklemsg)  # Need to unpickle and build object once more - T99
                self.logger.info(change.title)
                self.logger.info(change.hash)

                #Skip dealing with tif images and just consider them non-images w/o having to download them - T135
                if change.title[-3:].lower() == 'tif':
                    store_image(change.title, False, img_hash=change.hash, not_image=True)  # store in database
                    continue
                try:
                    file_page = pywikibot.FilePage(self.site, change.title)
                except pywikibot.InvalidTitle:
                    exc_type, exc_value, exc_traceback = exc_info()
                    self.logger.critical(
                        "CHARI " + ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)).strip())
                    continue  # Logging as a critical error & move on

                if not file_page.exists():
                    self.logger.debug(pywikibot.warning('File page does not exist ' + change.title))
                    continue

                # T125
                if file_page.isRedirectPage():
                    self.logger.debug(pywikibot.warning('File page is redirect' + change.title))
                    continue

                if not allow_bots(file_page.text, "TheSandBot"):
                    self.logger.critical("Not to edit " + file_page.title())
                    continue

                revision = file_page.latest_file_info
                pywikibot.output('Working on: %s at %s' % (change.title, revision.timestamp))

                path = os.path.join(tmpdir, str(uuid.uuid1()))

                # Download image
                try:
                    for i in range(8):  # Attempt to download 8 times. If it fails after this many, move on
                        try:
                            # returns download success result (True or False)
                            #if file_page.latest_file_info['width'] > 600:
                            #    success = self.download_thumbnail(file_page, path)
                            #else:
                            success = file_page.download(path, revision=file_page.latest_file_info)
                        except Exception as e:
                            pywikibot.exception(e)
                            success = False
                        if success:
                            break  # if we have a success, no point continuing to try and download
                        else:
                            pywikibot.warning(
                                'Possibly corrupted download on attempt %d' % i)
                            self.site.throttle(write=True)
                    else:
                        pywikibot.warning('FIXME: Download attempt exhausted')
                        pywikibot.warning('FIXME: Download of ' + str(file_page.title() + ' failed. Aborting...'))
                        if os.path.exists(path):
                            os.remove(path)
                        continue  # move on to the next file

                    del success
                    self.logger.info(get_local_hash(path))
                    self.logger.info(get_remote_hash(self.site, change.title))
                    try:
                        corrupt_result = image_is_corrupt(path)
                    except UnidentifiedImageError as e:
                        self.logger.debug(
                            change.title + " ::: is not an image (or at very least not currently supported by PIL)")
                        os.remove(path)  # file not an image; delete local download of it
                        store_image(change.title, False, img_hash=change.hash, not_image=True)  # store in database
                        # Move on to the next file
                        continue
                    except FileNotFoundError as e2:
                        if os.path.exists(path):
                            os.remove(path)
                        continue
                    if corrupt_result:
                        self.handle_result(self.site, file_page, change)
                        #os.remove(path)
                    else:  # image not corrupt
                        store_image(file_page.title(), False, img_hash=change.hash)  # store in database
                        self.logger.info(file_page.title() + " :Not corrupt. Stored")

                except Exception:
                    traceback.print_exc()
                finally:
                    if os.path.exists(path):
                        os.remove(path)

            pywikibot.output("Exit - THIS SHOULD NOT HAPPEN")
        finally:
            shutil.rmtree(tmpdir)

    def handle_result(self, site, file_page, change):
        tag_page(file_page)
        store_image(file_page.title(), True, img_hash=change.hash, day_count=7)  # store in database
        self.logger.info("Saved page and logged in database")
        # Notify the user that the file needs updating
        try:  # TODO: Add record to database about successful notification?
            notify_user(site, file_page, EDayCount.DAYS_7, EJobType.MONITOR, minor=False)
        except ValueError:
            self.logger.error("ERROR: Could not notify user about " + str(file_page.title()) + " being corrupt.")

    def download_thumbnail(self, fp, path):
        revision = fp.latest_file_info
        r = requests.get(fp.get_file_url(url_width=800), stream=True)
        if r.status_code == 200:
            try:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
            except IOError as e:
                raise e
            #sha1 = pywikibot.tools.compute_file_hash(fp.title())
            #return sha1 == revision.sha1
            return True
        else:
            self.logger.error("Could not download:: " + str(fp.title()))
            return False

    def run(self):
        pywikibot.handle_args()
        self.run_worker()
