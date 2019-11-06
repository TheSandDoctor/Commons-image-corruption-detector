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
from database_stuff import store_image, have_seen_image

#TODO: Write file




if __name__ == '__main__':
    pass
