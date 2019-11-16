# Purpose of this file is to monitor recent changes for corrupt images, tagging
# them as necessary.

# This should _really_ be done using a database. Perhaps pybind11 eventually(?)

from __future__ import absolute_import

import traceback, mwclient, mwparserfromhell, sys, re, configparser, json, pathlib
from image_corruption_utils import *
import mysql.connector
from database_stuff import store_image, have_seen_image
import os


# Save edit, we aren't checking if we are exclusion compliant as that isn't relevant in this task
def save_page(site, page, text, edit_summary, isBotEdit = True, isMinor = True):
    if not call_home(site, "monitor"):
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
    text = None
    _, ext = os.path.splitext(image_page.page_title)    # get filetype
    # Download image
    text = failed = hash = None
    _, ext = os.path.splitext(image_page.page_title)    # get filetype
    download_attempts = 0
    # Download image
    while True:
        with open("./Example2" + ext,"wb") as fd:
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
        raise ValueError("Hash check failed for " + "./Example2" + ext + " vs " + str(image_page.name) + " " + download_attempts + " times. Aborting...")
    del download_attempts
    # Read and check if valid
    with open("./Example2" + ext, "rb") as f:
        try:
            result = image_is_corrupt(f) #TODO: Add logic to tag page
        except FileFormatError:
            os.remove("./Example2" + ext)    # file not an image.
            raise
    del ext # no longer a needed variable
    if result: # image corrupt
        text = tag_page(image_page, site, "{{Template:User:TheSandDoctor/Template:TSB image identified corrupt|" + datetime.now(timezone.utc).strftime("%Y-%m-%d") + "}}")
        save_page(site, image_page, text,"Image detected as corrupt, tagging.")
        store_image(page.name, True, day_count = 7, hash) # store in database
        print("Saved page and logged in database")
        # Notify the user that the file needs updating
        try: #TODO: Add record to database about successful notification?
            notifyUser(site, image_page, getUploaderAndTimestamp(site, str(image_page.name)), "7 days")
        except: #TODO: Add record to database about failed notification?
            print("ERROR: Could not notify user about " + str(image_page.name) + " being corrupt.")
    else: # image not corrupt
        store_image(page.name, False, hash = hash) # store in database


#TODO: Replace
def getMostRecentUploads(site):
    rc = site.api('query', list='logevents',type='upload', lenamespace=6, lelimit=50)
    data = set()
    for i in rc['query']['logevents']:
        data.add(site.Pages[i['title']])
    return data


def run(site):
    global number_saved
    for page in getMostRecentUploads(site):
        print("Working with: " + page.name)
        number_saved += 1
        print(number_saved)
        text = page.text()
        try:
            if have_seen_image(site, page.name):#page.name in pages_run_set:
                print("Found duplicate, no need to check")
                continue
            process_file(page, site)
        except ValueError:
            raise


def main():
    site = mwclient.Site(('https', 'commons.wikimedia.org'), '/w/')
    config = configparser.RawConfigParser()
    config.read('credentials.txt')
    try:
        site.login(config.get('enwiki_sandbot', 'username'), config.get('enwiki_sandbot', 'password'))
    except errors.LoginError as e:
        print(e)
        raise ValueError("Login failed")
    run(site)


if __name__ == '__main__':
    #main()
    pass