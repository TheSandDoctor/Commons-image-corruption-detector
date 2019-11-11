# Purpose of this file is to follow up with any tagged images
# tagged images are tagged with a template that adds them to a category.
# The template that adds the images to the category has an unnamed parameter
# for the date that the tag was added. This tag is to be scanned in order to
# determine whether the file should now be nominated for deletion.

# Nominating for deletion occurs after 30 days have passed. The image should
# also be re-checked prior to nomination to ensure that it has not been fixed.
# If the image is fixed, then remove the template and take no further action.

# This should _really_ be done using a database. Perhaps pybind11 eventually(?)

from __future__ import absolute_import

import traceback, mwclient, mwparserfromhell, sys, re, configparser, json, pathlib
from image_corruption_utils import *
import mysql.connector
from database_stuff import store_image, have_seen_image, get_expired_images

#TODO: Define day_count
def tagForDeletion(site, page, day_count):
"""
Tags pages for deletion and takes the following parameters:
    site: site object
    page: page object
"""
    text = page.text()
    text = "{{SD|Corrupt image that has not been resolved in "
    text += str(day_count) + "}}\n" + text
    return text

def notify_and_tag_for_deletion(site, page, username):
    userTP = site.Pages["User talk:" + str(username)]
    msg = tagForDeletion(site, userTP, day_count) #FIXME: define day_count
    userTP.append(msg,summary="Notify about corrupt image [[" + str(image.name) + "]]", bot=True, minor=False, section='new')
    print("Notification of CSD nomination of " + str(image.name))

def run(site, image_page):
    text = failed = None
    _, ext = os.path.splitext(image_page.page_title)    # get filetype
    download_attempts = 0
    # Download image
    while True:
        with open("./Example3" + ext,"wb") as fd:
            try:
                image_page.download(fd)
            except FileFormatError:
                os.remove("./Example3" + ext)    # file not an image.
                raise
        #TODO: verify local hash vs api hash
        if not verifyHash(site, "./Example3" + ext, image_page):
            if download_attempts => 10:
                failed = 1
                break
            download_attempts += 1
            continue
        else:
            break
    if failed:
        raise ValueError("Hash check failed for " + "./Example3" + ext + " vs " + str(image_page.name) + " " + download_attempts + " times. Aborting...")
    del download_attempts

    with open("./Example3" + ext, "rb") as f:
        result = image_is_corrupt(f)
    del ext # no longer a needed variable
    if result: # image corrupt
        tagForDeletion(site, page, day_count) #FIXME: define day_count/get from DB (to_delete_nom-date_scanned)


def main():
    to_run = get_expired_images()
    for i in to_run:
        run()

if __name__ == '__main__':
    pass
