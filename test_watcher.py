import pywikibot
from pywikibot.comms.eventstreams import site_rc_listener
from Image import ImageObj

site = pywikibot.Site(user="TheSandBot")
rc = site_rc_listener(site)
myl = []
for change in rc:

    if (
            change['type'] == 'log' and
            change['namespace'] == 6 and
            change['log_type'] == 'upload'
    ):
        myl.append(ImageObj(change))
print(myl)