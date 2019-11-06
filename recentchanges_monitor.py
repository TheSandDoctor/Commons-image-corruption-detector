# Purpose of this file is to monitor recent changes for corrupt images, tagging
# them as necessary.

# This should _really_ be done using a database. Perhaps pybind11 eventually(?)

from __future__ import absolute_import

import traceback, mwclient, mwparserfromhell, sys, re, configparser, json, pathlib
from image_corruption_utils import *
import mysql.connector
from database_stuff import store_image, have_seen_image

#TODO: Write file

if __name__ == '__main__':
    pass
