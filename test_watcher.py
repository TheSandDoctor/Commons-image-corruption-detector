import pywikibot
from pywikibot.comms.eventstreams import site_rc_listener
from Image import ImageObj

site = pywikibot.Site(user="TheSandBot")
rc = site_rc_listener(site)
myl = []
count = 0
for change in rc:

    if (
            change['type'] == 'log' and
            change['namespace'] == 6 and
            change['log_type'] == 'upload' and count <= 5
    ):
        myl.append(ImageObj(change))
        count += 1
    elif count > 5:
        break
print(myl)