from enum import Enum

from PIL import Image
from PIL import ImageFile
from PIL import UnidentifiedImageError
from pywikibot import UnicodeType
import json
# import mysql.connector
import hashlib
import pywikibot
import mwparserfromhell
from pwb_wrappers import retry_apierror

ImageFile.MAXBLOCK = 1


def image_is_corrupt(f):
    """
    Check if image is corrupt. If an image is corrupt, it will fail .tobytes().
    It is also important to note that this will also fail if the file at hand is *not* an image. This is mitigated
    by the custom implementation of UnidentifiedImageError to catch this specific case.
    :param f: path/name of file to check if corrupt
    :return: True if corrupt, False if valid
    :raise UnidentifiedImageError if not a valid image
    """
    try:
        image = Image.open(f)
        image.tobytes()
        print("Works")
        return False
    except UnidentifiedImageError as e:
        print("Not an image")
        raise
    except Exception as e2:
        print("Corrupt\n")  # If we get this far, image is corrupt
        # print(e)
        return True


def get_local_hash(filename):
    """
    This function returns the SHA-1 hash
    of the file passed into it
    Retrieved from https://www.programiz.com/python-programming/examples/hash-file
    2019-11-07
    :param filename: Local file name/path to open
    :return: hex representation of digest (SHA1)
    """

    h = hashlib.sha1()  # make hash object
    # open file for reading in binary mode
    with open(filename, 'rb') as file:
        # loop till the end of the file
        chunk = 0
        while chunk != b'':
            # read only 1024 bytes at a time
            chunk = file.read(1024)
            h.update(chunk)

    return h.hexdigest()


def get_remote_hash(site, filename):
    """
    Get remote hash from Wikimedia Commons.

    Adapted from
    https://github.com/wikimedia/pywikibot/blob/298ff28eacb0cd50cca8ad19484758daab05d86c/pywikibot/page.py#L2633

    :param site: site object
    :param filename: name of file to get remote hash of (string)
    :return: sha1 hash (string)
    """
    fp = pywikibot.FilePage(site, filename)
    return str(fp.latest_file_info.sha1)


def verify_hash(site, local, image_page):
    """
    Verifies that two given hashes match.
    :param site: site object
    :param local: local file path/name
    :param image_page: image page object
    :return: True if match, False if not
    """
    lhash = get_local_hash(local)
    rhash = get_remote_hash(site, str(image_page.name))
    result = lhash == rhash
    return [result, rhash]


def get_uploader_and_timestamp(site, filename):
    """
    Get uploader and timestamp of file upload.
    From https://github.com/wikimedia/pywikibot/blob/298ff28eacb0cd50cca8ad19484758daab05d86c/pywikibot/page.py#L2634
    :param site: site object
    :param filename: filename to get uploader and timestamp from (string)
    :return: [user, timestamp] - user (string), timestamp (iso format)
    """
    # https://github.com/wikimedia/pywikibot/blob/298ff28eacb0cd50cca8ad19484758daab05d86c/pywikibot/page.py#L2634
    fp = pywikibot.FilePage(site, filename)
    return [str(fp.latest_file_info.user),
            UnicodeType(fp.latest_file_info.timestamp.isoformat())]


def notify_user(site, image, time_duration, task_name, minor=True, day_count=None):
    """
    Notify user of corruption (if task_name = 'full_scan' or 'monitor') or of tagging for deletion
    (if parameter anything else).
    :param site: site object
    :param image: image page object
    :param time_duration: duration of grace period (string)
    :param task_name: name of task (used to determine message type left) (string)
    :param minor: whether or not edit is minor (default True)
    :param day_count: passed number of days in grace period (string, default:None)
    :return: None
    """
    if isinstance(time_duration, Enum):
        time_duration = time_duration.value
    if isinstance(task_name, Enum):
        task_name = task_name.value
    if not call_home(site, task_name):
        raise ValueError("Kill switch on-wiki is false. Terminating program.")

    user, timestamp = get_uploader_and_timestamp(site, image.title())
    tp = pywikibot.Page(site, "User talk:" + user)
    if task_name == 'full_scan' or task_name == 'monitor':
        msg = "{{subst:TSB corruption notification|user=" + str(user) + "|file=" + str(image.title()) + "|time=" + str(
            timestamp)
        msg += "|time_duration=" + str(time_duration) + "}} ~~~~"

        summary = "Notify about corrupt image [[" + str(image.title()) + "]]"
        print("Notification of corruption of " + str(image.title()))
    else:  # if task_name == 'followup':
        msg = "{{subst:TSB corruption CSD notification|user=" + str(user) + "|file=" + str(
            image.title()) + "|time_duration=" + str(day_count) + "}} ~~~~"
        summary = "Nominating corrupt file for deletion - passed " + str(day_count) + " day grace period."
        print("Notification of CSD nomination of " + str(image.title()))

    retry_apierror(lambda: tp.save(appendtext=msg, summary=summary, minor=minor, botflag=True, force=True))


def call_home(site_obj, key):
    """
    "Call home" to double check that we are still allowed to edit.
    :param site_obj: site object
    :param key: subsection key
    :return: whether or not we can keep editing
    """
    page = pywikibot.Page(site_obj, 'User:TheSandBot/status')
    text = page.text
    data = json.loads(text)["run"]["corrupt_image_finder"][key]
    return str(data) == str(True)


def allow_bots(text, user):
    """
    This is a modified method from https://en.wikipedia.org/wiki/Template:Bots#Python .
    In short: it should only follow exclusion compliance when it is specifically disallowed.
    This is because all images should be checked but images that it for some reason gets
    consistently incorrect need some sort of method to ensure that it does not touch them again.
    :param text: page text to search
    :param user: bot to search for
    :return: whether or not bot allowed to edit page
    """
    user = user.lower().strip()
    text = mwparserfromhell.parse(text)
    for tl in text.filter_templates():
        if tl.name.matches(['bots', 'nobots']):
            break
    else:
        return True
    for param in tl.params:
        bots = [x.lower().strip() for x in param.value.split(",")]
        #if param.name == 'allow':
            #if ''.join(bots) == 'none': return False
        #    for bot in bots:
        #        if bot in (user, 'all'):
         #           return True
        if param.name == 'deny':
            if ''.join(bots) == 'none': return True
            for bot in bots:
                if bot in (user):
                    return False
    return True
