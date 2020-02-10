# -*- coding: UTF-8 -*-
# TODO: Should the corruption checking methods etc be forked into their own
# file (for reuse in others)?

from __future__ import absolute_import

#import traceback, sys, re, configparser, json, pathlib

from datetime import datetime, timezone
from image_corruption_utils import *
from database_stuff import store_image, have_seen_image, gen_nom_date
from PIL import UnidentifiedImageError
from EUtils import EDayCount, EJobType
import pywikibot
import pwb_wrappers
import os
import tempfile
import uuid
from pywikibot.data.api import APIError
from pywikibot.throttle import Throttle
import shutil
import traceback
import argparse
import copy

logger = None
skip = False


# Save edit, we aren't checking if we are exclusion compliant as that isn't relevant in this task
# def save_page(site, page, text, edit_summary, is_bot_edit=True, is_minor=True):
#     if not call_home(site, "full_scan"):
#         raise ValueError("Kill switch on-wiki is false. Terminating program.")
#     retry_apierror(
#         lambda:
#         page.save(appendtext=text, summary=edit_summary, minor=is_minor, botflag=is_bot_edit, force=True)
#     )

def file_is_empty(path):
    return os.stat(path).st_size==0


def process_file2():
    tmpdir = None
    global logger
    try:
        tmpdir = tempfile.mkdtemp()
        site = pywikibot.Site(user="TheSandBot")
        site._throttle = Throttle(site, multiplydelay=False)

        # Multi-workers are enough to cause problems, no need for internal
        # locking to cause even more problems
        site.lock_page = lambda *args, **kwargs: None  # noop
        site.unlock_page = lambda *args, **kwargs: None  # noop

        global skip
        # T111
        if os.path.exists("./corrupt_have_seen_count.txt") and not file_is_empty("./corrupt_have_seen_count.txt"):
            with open("./corrupt_have_seen_count.txt", 'r') as f:
                try:
                    count_have_seen = int(f.readline())
                except (TypeError, ValueError):
                    logger.critical("Cannot cast string to int. Check corrupt_have_seen_count.txt format.")
                    raise
        else:
            count_have_seen = 0
        tmp_count = copy.deepcopy(count_have_seen)
        for image_page in pwb_wrappers.allimages():
            if skip and tmp_count > 0:
                tmp_count -= 1
                continue
            elif have_seen_image(site, image_page.title()):
                logger.debug("Have seen:: " + image_page.title())
                count_have_seen += 1
                continue

            if not allow_bots(image_page.text, "TheSandBot"):
                logger.critical("Not to edit " + image_page.title())
                continue

            if not skip:
                with open("./corrupt_have_seen_count.txt", 'w+') as f:
                    f.write('{}'.format(count_have_seen))

            if not image_page.exists():
                logger.warning('File page does not exist:: ' + image_page.title())
                continue
            for i in range(8):
                try:
                    image_page.get_file_history()
                except pywikibot.exceptions.PageRelatedError as e:
                    # pywikibot.exceptions.PageRelatedError:
                    # loadimageinfo: Query on ... returned no imageinfo
                    pywikibot.exception(e)
                    site.throttle(write=True)
                else:
                    break
            else:
                raise

            path = os.path.join(tmpdir, str(uuid.uuid1()))
            revision = image_page.latest_file_info
            # Download image
            try:
                for i in range(8): # Attempt to download 8 times. If it fails after this many, move on
                    try:
                        # returns download success result (True or False)
                        success = image_page.download(path, revision=revision)
                    except Exception as e:
                        logger.exception(e)
                        success = False
                    if success:
                        break  # if we have a success, no point continuing to try and download
                    else:
                        logger.warning(
                            'Possibly corrupted download on attempt %d' % i)
                        site.throttle(write=True)
                else:
                    logger.warning('FIXME: Download attempt exhausted')
                    logger.warning('FIXME: Download of ' + str(image_page.title() + ' failed. Aborting...'))
                    continue  # move on to the next file

                del success
                img_hash = get_local_hash(path)
                try:
                    corrupt_result = image_is_corrupt(path)
                except UnidentifiedImageError as e:
                    logger.debug(
                        image_page.title() + " ::: is not an image (or at very least not currently supported by PIL)")
                    os.remove(path)  # file not an image
                    store_image(image_page.title(), False, img_hash=img_hash, not_image=True)  # store in database
                    # Previously the idea was to just raise the error,
                    # but since this is a constant running loop, just move on
                    # to the next file (once local removed)
                    continue

                if corrupt_result:
                    pwb_wrappers.tag_page(image_page,
                                          "{{TSB image identified corrupt|" +
                                          datetime.now(
                                              timezone.utc).strftime("%m/%d/%Y") + "|day=" + gen_nom_date()[
                                              1] + "|month=" +
                                          gen_nom_date()[0] + "|year=" + gen_nom_date()[2] + "}}",
                                          "Image detected as corrupt, tagging.")
                    store_image(image_page.title(), True, img_hash=img_hash, day_count=30)  # store in database

                    try:  # TODO: Add record to database about successful notification?
                        notify_user(site, image_page, EDayCount.DAYS_30, EJobType.FULL_SCAN, minor=False)
                    except:  # TODO: Add record to database about failed notification?
                        logger.error("ERROR: Could not notify user about " + str(image_page.title()) + " being corrupt.")
                else:  # image not corrupt
                    # store_image(file_page.title(), False, img_hash=img_hash)  # store in database
                    store_image(image_page.title(), False, img_hash=img_hash)  # store in database
                    logger.info(image_page.title() + " :Not corrupt. Stored")

            except Exception:
                traceback.print_exc()
            finally:
                if os.path.exists(path):
                    os.remove(path)

        logger.critical("Exit - THIS SHOULD NOT HAPPEN")
    finally:
        shutil.rmtree(tmpdir)


def process_file(image_page, site):
    text = failed = img_hash = None
    _, ext = os.path.splitext(image_page.title())  # TODO: reduce this to not include "File:"?

    download_attempts = 0
    while True:
        with open('./Example' + ext, 'wb') as fd:
            image_page.download(fd)

        hash_result, img_hash = verify_hash(site, "./Example" + ext, image_page)
        if not hash_result:
            if download_attempts >= 10:
                failed = 1
                break
            download_attempts += 1
            continue
        else:
            break
    if failed:
        raise ValueError("Hash check failed for " + "./Example" + ext + " vs " + str(
            image_page.title()) + " " + download_attempts + " times. Aborting...")
    del download_attempts
    # Read and check if valid
    with open("./Example" + ext, "rb") as f:
        try:
            result = image_is_corrupt(f)
        except UnidentifiedImageError:
            os.remove('./Example' + ext)  # file not an image
            raise
    del ext  # no longer a needed variable
    if result:  # image corrupt
        pwb_wrappers.tag_page(image_page,
                              "{{TSB image identified corrupt|" +
                              datetime.now(
                                  timezone.utc).strftime("%m/%d/%Y") + "|day=" + gen_nom_date()[1] + "|month=" +
                              gen_nom_date()[0] + "|year=" + gen_nom_date()[2] + "}}",
                              "Image detected as corrupt, tagging.")
        store_image(image_page.title(), True, img_hash=img_hash)  # store in database
        logger.info("Saved page and logged in database")
        # Notify the user that the file needs updating
        try:  # TODO: Add record to database about successful notification?
            notify_user(site, image_page, EDayCount.DAYS_30, EJobType.FULL_SCAN, minor=False)
        except:  # TODO: Add record to database about failed notification?
            logger.error("ERROR: Could not notify user about " + str(image_page.title()) + " being corrupt.")
    else:  # image not corrupt
        store_image(image_page.title(), False, img_hash=img_hash)  # store in database


if __name__ == '__main__':
    fileConfig('logging_config.ini')
    logger = logging.getLogger('full_scan')
    parser = argparse.ArgumentParser()
    parser.add_argument('--fs', "--full_scan", help="whether to skip rechecks", action="store_true")
    args = parser.parse_args()
    try:
        if args.full_scan:
            skip = True
    except AttributeError:
        pass
    process_file2()
