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
from image_corruption_utils import getLocalHash
from redis import Redis

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
    #https://github.com/toolforge/embeddeddata/blob/5ecd31417a4c3c5d1be9c2a58f55a1665d9c767f/worker.py#L361
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
            #TODO: Replace this with PIL
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

#TODO: Write own continuation




                res = detect(path)
                if res:
                    msg = []
                    for item in res:
                        if item['middleware']:
                            pos = item['middleware']
                        else:
                            pos = '%s (%s bytes, via %s)' % (
                                sizeof_fmt(item['pos']),
                                item['pos'],
                                ','.join(item['via']))
                            if not item['posexact']:
                                pos = 'about ' + pos

                        if item['mime'][0] in UNKNOWN_TYPES:
                            mime = 'Unidentified type (%s, %s)' % item['mime']
                        else:
                            mime = 'Identified type: %s (%s)' % item['mime']
                        msg.append('After %s: %s' % (pos, mime))
                    msg = '; '.join(msg)

                    pywikibot.output(u"\n\n>>> %s <<<"
                                     % filepage.title(asLink=True))
                    pywikibot.output(msg)

                    execute_file(filepage, revision, msg, res, path)

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
