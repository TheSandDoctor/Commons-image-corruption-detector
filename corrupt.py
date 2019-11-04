from __future__ import absolute_import

import traceback, mwclient, mwparserfromhell, sys, re, configparser, json, pathlib

from PIL import Image
from PIL import ImageFile

from datetime import datetime, timezone


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
def process_file(page_name, site):
    image_page = site.Pages["""""" + str(page_name) + """"""]
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
    #TODO: Continue writing based on previous save_edit functions.
    try:
        page.save(text,summary=edit_summary, bot=isBotEdit, minor=isMinor)
        print("Saved page")
    except [[EditError]]:
        print("Error")

if __name__ == '__main__':
    #image_is_corrupt("./River_GK_rojo_.png")
    #image_is_corrupt("./Test.jpg")
