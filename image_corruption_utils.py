from PIL import Image
from PIL import ImageFile
import mysql.connector
import hashlib
import pywikibot
from pwb_wrappers import retry_apierror
ImageFile.MAXBLOCK = 1

# Check if image is corrupt. If an image is corrupt, it will fail .tobytes()
def image_is_corrupt(f):
    try:
        image = Image.open(f)
        image.tobytes()
        print("Works")
        return False
    except Image.FileFormatError as e:
        print("Not an image")
        raise
    except Exception as e2:
        print("Corrupt\n") # If we get this far, image is corrupt
        #print(e)
        return True

def getLocalHash(filename):
    """"This function returns the SHA-1 hash
   of the file passed into it
   Retrieved from https://www.programiz.com/python-programming/examples/hash-file
   2019-11-07"""

   h = hashlib.sha1() # make hash object
   # open file for reading in binary mode
   with open(filename, 'rb') as file:
       # loop till the end of the file
       chunk = 0
       while chunk != b'':
           # read only 1024 bytes at a time
           chuck = file.read(1024)
           h.update(chuck)

   # return the hex representation of digest
   return h.hexdigest()

def getRemoteHash_PWB(site, filename):
    # https://github.com/wikimedia/pywikibot/blob/298ff28eacb0cd50cca8ad19484758daab05d86c/pywikibot/page.py#L2633
    fp = pywikibot.FilePage(site, filename)
    return str(fp.latest_file_info.sha1)

def getRemoteHash(site, filename):
    """
        Fetch remote hash from the mediawiki API.
        This method returns a sha1 hash in the form of a string.
        Parameters:
            site: site object
            filename: file name to get the remote hash from (string)
        Returns: sha1 hash (as a string)
    """
    # https://commons.wikimedia.org/wiki/Special:ApiSandbox#action=query&format=json&prop=imageinfo&titles=File%3ASalda%C3%B1a%20-%20015%20(26238038617).jpg&iiprop=timestamp%7Cuser%7Csha1
    result = site.api('query', prop = 'imageinfo', iiprop = 'timestamp|user|sha1', titles=filename)
    pageid = sha = None
    for i in result['query']['pages']:
        pageid = str(i)
    for i in result['query']['pages'][pageid]['imageinfo']:
        sha = i['sha1']
    del pageid
    return sha


def verifyHash(site, local, image_page):
    """
        Verifies that two given hashes match.
        Parameters:
            site: site object
            local: local filename
            image_page: image page object
        Returns: True if match, False if not
    """
    lhash = getLocalHash(local)
    rhash = getRemoteHash(site, str(image_page.name))
    result = lhash == rhash
    return [result, rhash]

def getUploaderAndTimestamp_PWB(site, filename):
    # https://github.com/wikimedia/pywikibot/blob/298ff28eacb0cd50cca8ad19484758daab05d86c/pywikibot/page.py#L2634
    fp = pywikibot.FilePage(site, filename)
    return [str(fp.latest_file_info.user),
                UnicodeType(fp.latest_file_info.timestamp.isoformat())]

#TODO: verify functionality
def getUploaderAndTimestamp(site, filename):
    """
        Get most recent file uploader and timestamp of that upload. This method
        may potentially throw an error due to issues with the mediawiki software itself
        it is unclear and unforeseeable what the specific errors may be at this time,
        it is just a distinct possibility. As such, this method should _always_ be wrapped in
        a try/except statement.

        Parameters:
            site: site object
            filename: filename to fetch the information of (string)
        Returns: [user, timestamp] list (user and timestamp both strings)
    """
    result = site.api('query', prop = 'imageinfo', iiprop = 'timestamp|user|sha1', titles=filename)
    pageid = user = timestamp = None
    for i in result['query']['pages']:
        pageid = str(i)
    for i in result['query']['pages'][pageid]['imageinfo']:
        user = i['user']
        timestamp = i['timestamp']
    del pageid
    return [user, timestamp]


def notifyUser_PWB(site, image, time_duration, task_name, minor = True, day_count = None):
    if not call_home(site, task_name):
        raise ValueError("Kill switch on-wiki is false. Terminating program.")
        
    user, timestamp = getUploaderAndTimestamp_PWB(site, image)
    tp = pywikibot.Page(site, "User talk:" + user]
    if task_name == 'full_scan' or task_name == 'monitor':
        msg = "{{subst:TSB corruption notification|user=" + str(user) + "|file=" + str(image.title()) + "|time=" + str(timestamp)
        msg += "|time_duration=" + str(time_duration) + "}}"
        #msg = "Hello " + user + ", it appears that the version of [[" + str(image.title()) + "]] which you uploaded " + timestamp
        #msg += " is broken or corrupt. Please review the image and attempt to correct this issue by uploading a new version of the file. [[User:TheSandBot|TheSandBot]] will re-review this image again in " + time_duration
        #msg += " if it is not resolved by then, the file will be [[Commons:CSD|nominated for deletion]] automatically."

        summary = "Notify about corrupt image [[" + str(image.title()) + "]]"
        print("Notification of corruption of " + str(image.title())))
    else: # if task_name == 'followup':
        msg = "{{TSB corruption CSD notification|user=" + str(user) + "|file=" + str(image.title()) + "|time_duration=" + str(day_count) + "}}"
        summary = "Nominating corrupt file for deletion - passed " + str(day_count) + " day grace period."
        #msg = "Hello " + str(user) + ", this message is to notify you that "
        #msg += str(image.title()) + " has been nominated for [[Commons:CSD|speedy deletion]] "
        #msg += "as it is still corrupt after the " + str(day_count) + " day grace period."
        #userTP.append(msg,summary="Notify about corrupt image [[" + str(image.title()) + "]]", bot=True, minor=False, section='new')
        #summary = "Notify about corrupt image [[" + str(image.title()) + "]]" + " nomination for [[Commons:CSD|speedy deletion]]"
        print("Notification of CSD nomination of " + str(image.title()))

    retry_apierror(
        lambda:
        filepage.save(appendtext=msg, section=new, #FIXME: appendtext and section=new surely don't play together(?)
                      summary=summary, minor=minor, botflag=True, force=True)
    )

#TODO: Formalize/improve further
def notifyUser(site, image, user, time_duration, task_name):
    if not call_home(site, task_name):
        raise ValueError("Kill switch on-wiki is false. Terminating program.")
    #time = 0
    msg = "Hello " + user + ", it appears that the version of [[" + str(image.name) + "]] which you uploaded " + user[1]
    msg += " is broken or corrupt. Please review the image and attempt to correct this issue by uploading a new version of the file. [[User:TheSandBot|TheSandBot]] will re-review this image again in " + time_duration
    msg += " if it is not resolved by then, the file will be [[Commons:CSD|nominated for deletion]] automatically."
    user_talk = site.Pages['User talk:' + user[0]]
    while True:
        try:
            user_talk.append(msg,summary="Notify about corrupt image [[" + str(image.name) + "]]", bot=True, minor=False, section='new')
            print("Notified user of corrupt " + str(image.name))
        #    if time == 1:
            #    time = 0
            break
        except [[EditError]]:
            print("Error")
            #time = 1
            sleep(5) # sleep for 5 seconds before trying again
            continue
        except [[ProtectedPageError]]:
            print('Could not edit [[User talk:' + user[0] + ']] due to protection')
            break


# Add template to image page
def tag_page(page, site, tag):
    text = page.text()
    text = tag + "\n" + text
    return text

def call_home_PWB(site_obj, key):
    page = pywikibot.Page(site_obj, 'User:TheSandBot/status')
    text = page.text
    data = json.loads(text)["run"]["corrupt_image_finder"][key]
    return str(data) == str(True)

def call_home(site_obj, key):
    page = site_obj.Pages['User:TheSandBot/status']
    text = page.text()
    data = json.loads(text)["run"]["corrupt_image_finder"][key]
    if str(data) == str(True):
        return True
    return False
