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

number_saved = 0


# Save edit, we aren't checking if we are exclusion compliant as that isn't relevant in this task
# def save_page(site, page, text, edit_summary, is_bot_edit=True, is_minor=True):
#     if not call_home(site, "full_scan"):
#         raise ValueError("Kill switch on-wiki is false. Terminating program.")
#     retry_apierror(
#         lambda:
#         page.save(appendtext=text, summary=edit_summary, minor=is_minor, botflag=is_bot_edit, force=True)
#     )


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
        print("Saved page and logged in database")
        global number_saved
        number_saved += 1
        print(number_saved)
        # Notify the user that the file needs updating
        try:  # TODO: Add record to database about successful notification?
            notify_user(site, image_page, EDayCount.DAYS_30, EJobType.FULL_SCAN, minor=False)
        except:  # TODO: Add record to database about failed notification?
            print("ERROR: Could not notify user about " + str(image_page.title()) + " being corrupt.")
    else:  # image not corrupt
        store_image(image_page.title(), False, img_hash=img_hash)  # store in database


def run(utils):
    site = utils[1]
    offset = utils[2]
    for page in pwb_wrappers.allimages():
        if offset > 0:
            offset -= 1
            print("Skipped due to offset config")
            continue
        global number_saved  # FIXME: This section MUST be removed once trials done and approved
        if number_saved >= 10:
            break  # FIXME: End section
        print("Working with: " + str(page.title()))
        # print(number_saved)
        #text = page.text
        try:
            if have_seen_image(site, page.title()):
                print("Found duplicate, no need to check")
                continue
            if not allow_bots(page.text, "TheSandBot"):
                print("Not to edit " + page.title())
                continue
            try:
                process_file(page, site)
            except UnidentifiedImageError as e:  # File not an image. Best to just continue
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
    login_result = site.login()
    if not login_result:
        raise ValueError('Incorrect password')
    offset = 0
    utils = [config, site, offset]
    run(utils)


if __name__ == '__main__':
    # main()
    pass
