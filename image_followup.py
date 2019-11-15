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
from database_stuff import have_seen_image, get_expired_images

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

def notify_and_tag_for_deletion(site, page, username, day_count):
    while True:
        try:
            msg = tagForDeletion(site, page, day_count)
            edit_summary = "Nominating corrupt file for deletion - passed " + str(day_count) + " day grace period."
            page.save(msg,summary=edit_summary, bot=True, minor=False)
            break
        except [[EditError]]:
            print("Error")
            #time = 1
            sleep(5) # sleep for 5 seconds before trying again
            continue
        except [[ProtectedPageError]]:
            print('Could not edit to nominate ' + str(page.name)  + ' due to protection')
            break
    userTP = site.Pages["User talk:" + str(username)]
    while True:
        try:
            msg = "Hello " + str(username) + ", this message is to notify you that "
            msg += str(page.name) + " has been nominated for [[Commons:CSD|speedy deletion]] "
            msg += "as it is still corrupt after the " + str(day_count) + " day grace period."
            userTP.append(msg,summary="Notify about corrupt image [[" + str(image.name) + "]]", bot=True, minor=False, section='new')
            print("Notification of CSD nomination of " + str(image.name))
            break
        except [[EditError]]:
            print("Error")
            sleep(5)
            continue
        except [[ProtectedPageError]]:
            print('Could not edit [[User talk:' + user[0] + ']] and notify due to protection')
            break

def run(site, image, isCorrupt, date_scanned, to_delete_nom):
    image_page = site.Pages[image]
    text = failed = hash = None
    _, ext = os.path.splitext(image_page.page_title)    # get filetype
    download_attempts = 0
    # Download image
    while True:
        with open("./Example3" + ext,"wb") as fd:
            image_page.download(fd)

        hashResult, hash = verifyHash(site, "./Example2" + ext, image_page)
        if not hashResult:
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
        try:
            result = image_is_corrupt(f)
        except FileFormatError:
            os.remove("./Example3" + ext)    # file not an image.
            raise
    del ext # no longer a needed variable
    if result: # image corrupt
        try: #TODO: Add record to database about successful notification?
            notify_and_tag_for_deletion(site, image_page, username, calculateDifference(date_scanned))
        except: #TODO: Add record to database about failed notification?
            pass
    else: # image not corrupt
        edit_summary = "Removing [[Template:TSB image identified corrupt]] - image no longer corrupt"

        while True:
            code = mwparserfromhell.parse(image_page.text())
            for template in code.filter_templates():
                if template.name.matches("Template:User:TheSandDoctor/Template:TSB image identified corrupt"):
                    code.remove(template) # template no longer needed
                    try:
                        image_page.save(text, summary=edit_summary, bot=True, minor=True)
                        # update database entry to set image as no longer corrupt and nullify to_delete_nom
                        update_entry(str(image_page.name), False, "NULL", hash)
                        break
                    except errors.EditError:
                        print("Error")
                        sleep(5)   # sleep for 5 seconds before trying again
                        continue
                    except errors.ProtectedPageError:
                        print('Could not edit ' + page.page_title + ' due to protection')
                        break
            break # end for


def main():
    site = mwclient.Site(('https', 'commons.wikimedia.org'), '/w/')
    config = configparser.RawConfigParser()
    config.read('credentials.txt')
    try:
        site.login(config.get('enwiki_sandbot', 'username'), config.get('enwiki_sandbot', 'password'))
    except errors.LoginError as e:
        print(e)
        raise ValueError("Login failed")

    raw = get_expired_images()
    for i in raw:
        run(site, i[0], i[1], i[2], i[3])

if __name__ == '__main__':
    #main()
    pass
