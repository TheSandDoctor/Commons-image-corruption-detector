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
from database_stuff import store_image
from image_corruption_utils import image_is_corrupt, notify_user
from config import REDIS_KEY
from PIL import Image
from redis import Redis

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


def add_speedy(filepage, msg):
    # https://github.com/toolforge/embeddeddata/blob/5ecd31417a4c3c5d1be9c2a58f55a1665d9c767f/worker.py#L361
    filepage.clear_cache()

    if not filepage.exists():
        pywikibot.warning("Page doesn't exist, skipping save.")
        return

    # Make sure no edit conflicts happen here
    retry_apierror(
        lambda:
        filepage.save(prependtext='{{embedded data|suspect=1|1=%s}}\n' % msg,
                      summary='Bot: Adding {{[[Template:Embedded data|'
                              'embedded data]]}} to this embedded data suspect.')
    )


def run_worker():
    try:
        tmpdir = tempfile.mkdtemp()

        site = pywikibot.Site(user="TheSandBot")
        site._throttle = Throttle(site, multiplydelay=False)

        # Multi-workers are enough to cause problems, no need for internal
        # locking to cause even more problems
        site.lock_page = lambda *args, **kwargs: None  # noop
        site.unlock_page = lambda *args, **kwargs: None  # noop

        redis = Redis(host="tools-redis")

        while True:
            if number_saved >= 10:  # FIXME: This MUST be removed once trials done and approved
                break  # FIXME: This MUST be removed once trials done and approved
            _, change = redis.blpop(REDIS_KEY)
            change = json.loads(change)
            filepage = pywikibot.FilePage(site, change['title'])

            if not filepage.exists():
                continue

            for i in range(8):
                try:
                    filepage.get_file_history()
                except pywikibot.exceptions.PageRelatedError as e:
                    # pywikibot.exceptions.PageRelatedError:
                    # loadimageinfo: Query on ... returned no imageinfo
                    pywikibot.exception(e)
                    site.throttle(write=True)
                else:
                    break
            else:
                raise

            try:
                revision = filepage.get_file_history()[
                    pywikibot.Timestamp.fromtimestampformat(
                        change['log_params']['img_timestamp'])]
            except KeyError:
                try:
                    # From rcbacklog
                    revision = filepage.get_file_history()[
                        pywikibot.Timestamp.fromISOformat(
                            change['params']['img_timestamp'])]
                except KeyError:
                    try:
                        revision = filepage.get_file_history()[
                            pywikibot.Timestamp.fromtimestamp(
                                change['timestamp'])]
                    except KeyError:
                        revision = filepage.latest_file_info
                        pywikibot.warning(
                            'Cannot fetch specified revision, falling back to '
                            'latest revision.')

            pywikibot.output('Working on: %s at %s' % (change['title'],
                                                       revision.timestamp))

            path = os.path.join(tmpdir, str(uuid.uuid1()))

            # Download
            try:
                for i in range(8):
                    try:
                        success = filepage.download(path, revision=revision)
                    except Exception as e:
                        pywikibot.exception(e)
                        success = False
                    if success:
                        break
                    else:
                        pywikibot.warning(
                            'Possibly corrupted download on attempt %d' % i)
                        site.throttle(write=True)
                else:
                    pywikibot.warning('FIXME: Download attempt exhausted')
                    pywikibot.warning('FIXME: Download of ' + str(filepage.title() + ' failed. Aborting...'))
                    continue  # move on to the next file

                del success
                try:
                    corrupt_result = image_is_corrupt(path)
                except Image.FileFormatError as e:
                    print("Not an image (or at very least not currently supported by PIL)")
                    os.remove(path)  # file not an image
                    # Previously the idea was to just raise the error,
                    # but since this is a constant running loop, just move on
                    # to the next file (once local removed)
                    continue

                img_hash = str(change['log_params']['img_sha1'])
                if corrupt_result:
                    text = pwb_wrappers.tag_page(filepage,
                                                 "{{Template:User:TheSandDoctor/Template:TSB image identified corrupt|"
                                                 + datetime.now(
                                                     datetime.timezone.utc).strftime("%Y-%m-%d") + "}}",
                                                 "Image detected as corrupt, tagging.")
                    store_image(filepage.title(), True, img_hash=img_hash, day_count=7)  # store in database
                    print("Saved page and logged in database")
                    global number_saved  # FIXME: This MUST be removed once trials done and approved
                    number_saved += 1  # FIXME: This MUST be removed once trials done and approved
                    # Notify the user that the file needs updating
                    try:  # TODO: Add record to database about successful notification?
                        notify_user(site, filepage, "30 days", "monitor")
                    except:  # TODO: Add record to database about failed notification?
                        print("ERROR: Could not notify user about " + str(filepage.title()) + " being corrupt.")
                else:  # image not corrupt
                    store_image(filepage.title(), False, img_hash=img_hash)  # store in database

            except Exception:
                traceback.print_exc()
            finally:
                os.remove(path)

        pywikibot.output("Exit - THIS SHOULD NOT HAPPEN")
    finally:
        shutil.rmtree(tmpdir)


def main():
    pywikibot.handleArgs()
    run_worker()


if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
