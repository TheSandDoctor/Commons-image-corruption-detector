#TODO: Should the corruption checking methods etc be forked into their own
# file (for reuse in others)?

from __future__ import absolute_import

import traceback, mwclient, mwparserfromhell, sys, re, configparser, json, pathlib

from PIL import Image
from PIL import ImageFile

from datetime import datetime, timezone
number_saved = 0

ImageFile.MAXBLOCK = 1


def image_is_corrupt(f):
    try:
        image = Image.open(f)
        image.tobytes()
        print("Works")
        return False
    except Exception as e:
        print("Corrupt\n") # If we get this far, image is corrupt
        #print(e)
        return True


def call_home(site_obj):
    page = site_obj.Pages['User:TheSandBot/status']
    text = page.text()
    data = json.loads(text)["run"]["corrupt_image_finder"]
    if str(data) == str(True):
        return True
    return False


# Process image
def process_file(page, site):
    image_page = page #site.Pages["""""" + str(page_name) + """"""]
    text = None
    # Download image
    with open("./Example.jpg","wb") as fd:
        image_page.download(fd)
    # Read and check if valid
    with open("./Example.jpg", "rb") as f:
        result = image_is_corrupt(f) #TODO: Add logic to tag page
    if result:
        text = tag_page(image_page, site, "{{Template:User:TheSandDoctor/Template:TSB image identified corrupt|" + datetime.now(timezone.utc).strftime("%Y-%m-%d") + "}}")
        save_page(text,"Image detected as corrupt, tagging.")
        print("Saved page")

# Add template to image page
def tag_page(page, site, tag):
    text = page.text()
    text = tag + "\n" + text
    return text

# Save edit, we aren't checking if we are exclusion compliant as that isn't relevant in this task
def save_page(text, edit_summary, isBotEdit = True, isMinor = True):
    if not call_home(site):
        raise ValueError("Kill switch on-wiki is false. Terminating program.")
    time = 0
    while True:
        if time == 1:
            text = site.Pages["File:" + page.page_title].text()]
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

def store_run_pages():
    global pages_run_set
    with open('run.txt', 'a+') as f:
        for item in pages_run_set:
            f.write('%s\n' % item)

def load_run_pages():
    global pages_run_set
    print("Loading pages")
    with open('run.txt', 'r') as f:
        for item in f:
            pages_run_set.add(item)
            print("Adding " + item) #FIXME: This spams console a LOT

#TODO: This method most likely needs complete rewrite as this task isn't
# dealing with a category, but rather every file on Commons.
def run(utils):
    site = utils[1]
    offset = utils[2]
    limit = utils[3]
    global number_saved
    global pages_run_set
    load_run_pages()
    for page in site.Categories['']: #TODO: This line needs changing. Won't work in this form. Needs to just scan every file in commons plus new uploads.......
        if offset > 0:
            offset -= 1
            print("Skipped due to offset config")
            continue
        print("Working with: " + page.name)
        print(number_saved)
        if number_saved < limit:
            text = page.text()
            try:
                if page.name in pages_run_set:
                    print("Found duplicate, no need to check")
                    continue
                process_file(page, site)
                pages_run_set.add(page.name)
                print("Added")
            except ValueError:
                raise
        else:
            store_run_pages()
            return # tun out of pages in limited run
    pass

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
    #image_is_corrupt("./River_GK_rojo_.png")
    #image_is_corrupt("./Test.jpg")
