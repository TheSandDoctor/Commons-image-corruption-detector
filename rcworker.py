# -*- coding: UTF-8 -*-
import datetime
import json
import os
import shutil
import tempfile
import threading
import traceback
import uuid

import pywikibot
from pywikibot.data.api import APIError
from pywikibot.throttle import Throttle

import pwb_wrappers
from database_stuff import store_image, get_next_month
from image_corruption_utils import image_is_corrupt, notify_user, allow_bots
from config import REDIS_KEY
from PIL import UnidentifiedImageError
from redis import Redis
from Image import ImageObj
from EUtils import EDayCount, EJobType

number_saved = 0


def retry_apierror(f):
    # https://github.com/toolforge/embeddeddata/blob/5ecd31417a4c3c5d1be9c2a58f55a1665d9c767f/worker.py#L238
    for i in range(8):
        try:
            f()
        except APIError:
            pywikibot.warning(
                'Failed API request on attempt %d' % i)
        else:
            break
    else:
        raise


def run_worker():
    tmpdir = None  # Gets rid of IDE complaint/warning about access before assignment
    try:
        tmpdir = tempfile.mkdtemp()

        site = pywikibot.Site(user="TheSandBot")
        site._throttle = Throttle(site, multiplydelay=False)

        # Multi-workers are enough to cause problems, no need for internal
        # locking to cause even more problems
        site.lock_page = lambda *args, **kwargs: None  # noop
        site.unlock_page = lambda *args, **kwargs: None  # noop

        redis = Redis(host="localhost")
        global number_saved  # FIXME: This MUST be removed once trials done and approved
        while True:
            if number_saved >= 10:  # FIXME: This MUST be removed once trials done and approved
                break  # FIXME: This MUST be removed once trials done and approved
            _, change = redis.blpop(REDIS_KEY)
            # change = json.loads(change)
            #file_page = pywikibot.FilePage(site, change['title'])
            file_page = pywikibot.FilePage(site, change.title)

            if not allow_bots(file_page.text, "TheSandBot"):
                print("Not to edit " + file_page.title())
                continue

            if not file_page.exists():
                #print(pywikibot.warning('File page does not exist ' + str(change['title'])))
                print(pywikibot.warning('File page does not exist ' + change.title))
                continue

            for i in range(8):
                try:
                    file_page.get_file_history()
                except pywikibot.exceptions.PageRelatedError as e:
                    # pywikibot.exceptions.PageRelatedError:
                    # loadimageinfo: Query on ... returned no imageinfo
                    pywikibot.exception(e)
                    site.throttle(write=True)
                else:
                    break
            else:
                raise

            # try:
            #     revision = file_page.get_file_history()[
            #         pywikibot.Timestamp.fromtimestampformat(
            #             change['log_params']['img_timestamp'])]
            # except KeyError:
            #     try:
            #         # From rcbacklog
            #         revision = file_page.get_file_history()[
            #             pywikibot.Timestamp.fromISOformat(
            #                 change['params']['img_timestamp'])]
            #     except KeyError:
            #         try:
            #             revision = file_page.get_file_history()[
            #                 pywikibot.Timestamp.fromtimestamp(
            #                     change['timestamp'])]
            #         except KeyError:
            #             revision = file_page.latest_file_info
            #             pywikibot.warning(
            #                 'Cannot fetch specified revision, falling back to '
            #                 'latest revision.')
            revision = change.getRevision(file_page)

            #pywikibot.output('Working on: %s at %s' % (change['title'],
            #                                           revision.timestamp))
            pywikibot.output('Working on: %s at %s' % (change.title, revision.timestamp))

            path = os.path.join(tmpdir, str(uuid.uuid1()))

            # Download image
            try:
                for i in range(8):  # Attempt to download 8 times. If it fails after this many, move on
                    try:
                        # returns download success result (True or False)
                        success = file_page.download(path, revision=revision)
                    except Exception as e:
                        pywikibot.exception(e)
                        success = False
                    if success:
                        break   # if we have a success, no point continuing to try and download
                    else:
                        pywikibot.warning(
                            'Possibly corrupted download on attempt %d' % i)
                        site.throttle(write=True)
                else:
                    pywikibot.warning('FIXME: Download attempt exhausted')
                    pywikibot.warning('FIXME: Download of ' + str(file_page.title() + ' failed. Aborting...'))
                    continue  # move on to the next file

                del success
                try:
                    corrupt_result = image_is_corrupt(path)
                except UnidentifiedImageError as e:
                    print("Not an image (or at very least not currently supported by PIL)")
                    os.remove(path)  # file not an image
                    # Previously the idea was to just raise the error,
                    # but since this is a constant running loop, just move on
                    # to the next file (once local removed)
                    continue

                #img_hash = str(change['log_params']['img_sha1'])
                #img_hash = change.hash
                if corrupt_result:
                    nom_date = str(get_next_month(7)).split('/')
                    pwb_wrappers.tag_page(file_page,
                                          "{{TSB image identified corrupt|"
                                          + datetime.now(
                                              datetime.timezone.utc).strftime("%m/%d/%Y") + "|day=" +
                                          nom_date[1] + "|month=" + nom_date[0] + "|year=" + nom_date[2] + "}}",
                                          "Image detected as corrupt, tagging.")
                    #store_image(file_page.title(), True, img_hash=img_hash, day_count=7)  # store in database
                    store_image(file_page.title(), True, img_hash=change.hash, day_count=7)  # store in database
                    print("Saved page and logged in database")
                    number_saved += 1  # FIXME: This MUST be removed once trials done and approved
                    # Notify the user that the file needs updating
                    try:  # TODO: Add record to database about successful notification?
                        notify_user(site, file_page, EDayCount.DAYS_7, EJobType.MONITOR, minor=False)
                    except:  # TODO: Add record to database about failed notification?
                        print("ERROR: Could not notify user about " + str(file_page.title()) + " being corrupt.")
                else:  # image not corrupt
                    #store_image(file_page.title(), False, img_hash=img_hash)  # store in database
                    store_image(file_page.title(), False, img_hash=change.hash)  # store in database
                    print(file_page.title() + " :Not corrupt. Stored")

            except Exception:
                traceback.print_exc()
            finally:
                os.remove(path)

        pywikibot.output("Exit - THIS SHOULD NOT HAPPEN")
    finally:
        shutil.rmtree(tmpdir)


def main():
    pywikibot.handle_args()
    run_worker()


if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
