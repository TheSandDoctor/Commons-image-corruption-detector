# -*- coding: UTF-8 -*-
"""
Purpose of this file is to test the user notification features to ensure that they work properly as expected.
This is deliberately testing using the TheSandDoctor talk page on Wikimedia Commons to ensure minimal disruption to
others and per my self-consent.
"""

import pywikibot
from database_stuff import gen_nom_date
import pwb_wrappers
from datetime import datetime, timezone
import image_corruption_utils
from EUtils import EDayCount, EJobType
from pwb_wrappers import retry_apierror

site = pywikibot.Site()
#page = pywikibot.Page(site, u"User talk:TheSandDoctor")
#pwb_wrappers.tag_page(page,
 #                     "{{TSB image identified corrupt|" +
  #                    datetime.now(
   #                       timezone.utc).strftime("%m/%d/%Y") + "|day=" + gen_nom_date()[1] + "|month=" +
    #                  gen_nom_date()[0] + "|year=" + gen_nom_date()[2] + "}}",
     #                 "Image detected as corrupt, tagging.")

#page = pywikibot.FilePage(site,u'File:Rolling Stones crowd glowing cellphones 14 August 2019 Seattle.jpg')
#image_corruption_utils.notify_user(site, page, EDayCount.DAYS_30, EJobType.FULL_SCAN, minor=False)
page = pywikibot.Page(site, u'User talk:TheSandBot/ccc_tests')
try:
    retry_apierror(lambda: page.save(appendtext="Testing testing", summary="This is a test edit", minor=False, botflag=True, force=True))
except pywikibot.exceptions.LockedPage as e:
    print(page.title())
    print(e.message)
#if not image_corruption_utils.allow_bots(page.text, "TheSandBot"):
#    print("Not allowed")
#else:
 #   print("Allowed")