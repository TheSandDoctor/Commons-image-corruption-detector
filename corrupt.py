#TODO: Should the corruption checking methods etc be forked into their own
# file (for reuse in others)?

from __future__ import absolute_import

import traceback, mwclient, sys, re, configparser, json, pathlib

from datetime import datetime, timezone
from image_corruption_utils import *
from database_stuff import store_image, have_seen_image
from PIL import FileFormatError
import os


number_saved = 0

# Save edit, we aren't checking if we are exclusion compliant as that isn't relevant in this task
def save_page(site, page, text, edit_summary, isBotEdit = True, isMinor = True):
    if not call_home(site, "full_scan"):
        raise ValueError("Kill switch on-wiki is false. Terminating program.")
    time = 0
    while True:
        if time == 1:
            text = site.Pages["File:" + page.page_title].text()
        try:
            page.save(text,summary=edit_summary, bot=isBotEdit, minor=isMinor)
            print("Saved page")
            global number_saved
            number_saved += 1
            if time == 1:
                time = 0
            break
        except [[EditError]]:
            print("Error")
            time = 1
            sleep(5) # sleep for 5 seconds before trying again
            continue
        except [[ProtectedPageError]]:
            print('Could not edit ' + page.page_title + ' due to protection')
        break


# Process image
def process_file(image_page, site):
    text = failed = None
    _, ext = os.path.splitext(image_page.page_title)    # get filetype
    download_attempts = 0
    # Download image
    while True:
        with open("./Example" + ext,"wb") as fd:
            try:
                image_page.download(fd)
            except FileFormatError:
                os.remove("./Example" + ext)    # file not an image.
                raise
        if not verifyHash(site, "./Example" + ext, image_page):
            if download_attempts => 10:
                failed = 1
                break
            download_attempts += 1
            continue
        else:
            break
    if failed:
        raise ValueError("Hash check failed for " + "./Example" + ext + " vs " + str(image_page.name) + " " + download_attempts + " times. Aborting...")
    del download_attempts
    # Read and check if valid
    with open("./Example" + ext, "rb") as f:
        result = image_is_corrupt(f)
    del ext # no longer a needed variable
    if result: # image corrupt
        text = tag_page(image_page, site, "{{Template:User:TheSandDoctor/Template:TSB image identified corrupt|" + datetime.now(timezone.utc).strftime("%Y-%m-%d") + "}}")
        save_page(site, image_page, text,"Image detected as corrupt, tagging.")
        store_image(page.name, True) # store in database
        print("Saved page and logged in database")
        # Notify the user that the file needs updating
        try: #TODO: Add record to database about successful notification?
            notifyUser(site, image_page, getUploaderAndTimestamp(site, str(image_page.name)), "30 days")
        except: #TODO: Add record to database about failed notification?
            print("ERROR: Could not notify user about " + str(image_page.name) + " being corrupt.")
    else: # image not corrupt
        store_image(page.name, False) # store in database


def run(utils):
    site = utils[1]
    offset = utils[2]
    limit = utils[3]
    global number_saved
    for page in site.allimages(): # allimages() avoids issues with non-images
        if offset > 0:
            offset -= 1
            print("Skipped due to offset config")
            continue
        print("Working with: " + page.name)
        print(number_saved)
        if number_saved < limit:
            text = page.text()
            try:
                if have_seen_image(page.name):#page.name in pages_run_set:
                    print("Found duplicate, no need to check")
                    continue
                try:
                    process_file(page, site)
                except FileFormatError as e: # File not an image. Best to just continue
                    continue
                except ValueError as e2:
                    print(e2)
                    with open('downloads_failed.txt', 'a+') as f:
                        print(e2,file=f) # print to file
                    continue
            except ValueError:
                raise
        else:
            return # tun out of pages in limited run

def main():
    site = mwclient.Site(('https', 'commons.wikimedia.org'), '/w/')
    config = configparser.RawConfigParser()
    config.read('credentials.txt')
    try:
        site.login(config.get('enwiki_sandbot', 'username'), config.get('enwiki_sandbot', 'password'))
    except errors.LoginError as e:
        print(e)
        raise ValueError("Login failed")
    offset = 0
    limit = 2
    utils = [config,site,offset,limit]
    run(utils)

if __name__ == '__main__':
    #main()
    pass
