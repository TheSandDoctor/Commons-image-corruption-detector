# Purpose of this file is to monitor recent changes for corrupt images, tagging
# them as necessary.

# This should _really_ be done using a database. Perhaps pybind11 eventually(?)

from __future__ import absolute_import

import traceback, mwclient, mwparserfromhell, sys, re, configparser, json, pathlib
from image_corruption_utils import *
import mysql.connector
from database_stuff import store_image, have_seen_image
import os

#TODO: finish writing file

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
def process_file(page, site):
    image_page = page #site.Pages["""""" + str(page_name) + """"""]
    text = None
    _, ext = os.path.splitext(image_page.page_title)    # get filetype
    # Download image
    with open("./Example2" + ext,"wb") as fd:
        image_page.download(fd)
    # Read and check if valid
    with open("./Example2" + ext, "rb") as f:
        result = image_is_corrupt(f) #TODO: Add logic to tag page
    del ext # no longer a needed variable
    if result: # image corrupt
        text = tag_page(image_page, site, "{{Template:User:TheSandDoctor/Template:TSB image identified corrupt|" + datetime.now(timezone.utc).strftime("%Y-%m-%d") + "}}")
        save_page(site, image_page, text,"Image detected as corrupt, tagging.")
        store_image(page.name, True) # store in database
        print("Saved page")
    else: # image not corrupt
        store_image(page.name, False) # store in database



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
            if have_seen_image(page.name):#page.name in pages_run_set:
                print("Found duplicate, no need to check")
                continue
            process_file(page, site)
            #pages_run_set.add(page.name)
            #print("Added")
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
    pass
