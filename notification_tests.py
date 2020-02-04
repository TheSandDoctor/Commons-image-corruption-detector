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
from DayCount import EDayCount

site = pywikibot.Site()
page = pywikibot.Page(site, u"User talk:TheSandDoctor")
pwb_wrappers.tag_page(page,
                      "{{TSB image identified corrupt|" +
                      datetime.now(
                          timezone.utc).strftime("%m/%d/%Y") + "|day=" + gen_nom_date()[1] + "|month=" +
                      gen_nom_date()[0] + "|year=" + gen_nom_date()[2] + "}}",
                      "Image detected as corrupt, tagging.")

page = pywikibot.FilePage(site,u'File:Rolling Stones crowd glowing cellphones 14 August 2019 Seattle.jpg')
image_corruption_utils.notify_user(site, page, EDayCount.DAYS_30.name, "full_scan")