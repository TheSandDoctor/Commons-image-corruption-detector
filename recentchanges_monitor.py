# Purpose of this file is to monitor recent changes for corrupt images, tagging
# them as necessary.

# This should _really_ be done using a database. Perhaps pybind11 eventually(?)

from __future__ import absolute_import

import traceback, mwclient, mwparserfromhell, sys, re, configparser, json, pathlib


#TODO: Write file
