from database_stuff import have_seen_image
import pywikibot
site = pywikibot.Site(user="TheSandBot")
image_page = pywikibot.FilePage(site, "File:Forssa.sijainti.Suomi.2020.svg")
if have_seen_image(site, image_page.title()):
    print("Found")
else:
    print("False")