# TODO: Should the corruption checking methods etc be forked into their own
# file (for reuse in others)?

from __future__ import absolute_import

import traceback, sys, re, configparser, json, pathlib

from datetime import datetime, timezone
from image_corruption_utils import *
from database_stuff import store_image, have_seen_image
from PIL import FileFormatError
import pywikibot
import pwb_wrappers
import os

number_saved = 0


# Save edit, we aren't checking if we are exclusion compliant as that isn't relevant in this task
def save_page(site, page, text, edit_summary, is_bot_edit=True, is_minor=True):
    if not call_home(site, "full_scan"):
        raise ValueError("Kill switch on-wiki is false. Terminating program.")
    retry_apierror(
        lambda:
        page.save(appendtext=text, section='new',  # FIXME: appendtext and section=new surely don't play together(?)
                  summary=edit_summary, minor=is_minor, botflag=is_bot_edit, force=True)
    )


def process_file(image_page, site):
    text = failed = img_hash = None
    _, ext = os.path.splitext(image_page.title())  # TODO: reduce this to not include "File:"?
    download_attempts = 0
    while True:
        with open('./Example' + ext, 'wb') as fd:
            image_page.download(fd)

        hash_result, img_hash = verifyHash(site, "./Example" + ext, image_page)
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
        except FileFormatError:
            os.remove('./Example' + ext)  # file not an image
            raise
    del ext  # no longer a needed variable
    if result:  # image corrupt
        text = pwb_wrappers.tag_page(image_page,
                                     "{{Template:User:TheSandDoctor/Template:TSB image identified corrupt|" +
                                     datetime.now(
                                         timezone.utc).strftime("%Y-%m-%d") + "}}",
                                     "Image detected as corrupt, tagging.")
        store_image(image_page.title(), True, hash=img_hash)  # store in database
        print("Saved page and logged in database")
        # Notify the user that the file needs updating
        try:  # TODO: Add record to database about successful notification?
            notifyUser(site, image_page, "30 days", "full_scan")
        except:  # TODO: Add record to database about failed notification?
            print("ERROR: Could not notify user about " + str(image_page.title()) + " being corrupt.")
    else:  # image not corrupt
        store_image(image_page.title(), False, hash=img_hash)  # store in database


def run(utils):
    site = utils[1]
    offset = utils[2]
    for page in pwb_wrappers.allimages():
        if offset > 0:
            offset -= 1
            print("Skipped due to offset config")
            continue
        print("Working with: " + str(page.title()))
        # print(number_saved)
        text = page.text
        try:
            if have_seen_image(site, page.title()):
                print("Found duplicate, no need to check")
                continue
            try:
                process_file(page, site)
            except FileFormatError as e:  # File not an image. Best to just continue
                continue
            except ValueError as e2:
                print(e2)
                with open('downloads_failed.txt', 'a+') as f:
                    print(e2, file=f)  # print to file
                continue
        except ValueError:
            raise
    return


def main():
    config = None
    site = pywikibot.Site(code='commons', fam='commons', user='TheSandBot')
    lresult = site.login()
    if not lresult:
        raise ValueError('Incorrect password')
    offset = 0
    utils = [config, site, offset]
    run(utils)


if __name__ == '__main__':
    # main()
    pass
