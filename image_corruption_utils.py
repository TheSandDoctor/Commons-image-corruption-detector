from PIL import Image
from PIL import ImageFile
from PIL import FileFormatError
import mysql.connector
import hashlib
ImageFile.MAXBLOCK = 1

supported_formats = { #TODO: Use this somehow
    "BMP",
    "EPS",
    "GIF",
    "ICNS",
    "ICO",
    "IM",
    "JPEG",
    "jpg",
    "jpe",
    "jif",
    "jfif",
    "jfi"
    "jp2",
    "j2k",
    "jpf",
    "jpx",
    "jpm",
    "mj2",
    "MSP",
    "PCX",
    "PNG",
    "pbm",
    "pgm",
    "ppm",
    "pnm",
    "sgi",
    "rgb",
    "rgba",
    "bw",
    "int",
    "inta",
    "spi",
    "tga",
    "icb",
    "vda",
    "vst",
    "tiff",
    "tif",
    "webp",
    "xbm",
    "blp",
    "cur",
    "dcx",
    "DDS",
    "fli",
    "flc",
    "fpx",
    "ftex",
    "gbr",
    "gd",
    "imt",
    "pixar",
    "psd",
    "wal",
    "xpm",
    "svg"
}

# Check if image is corrupt. If an image is corrupt, it will fail .tobytes()
def image_is_corrupt(f):
    try:
        image = Image.open(f)
        image.tobytes()
        print("Works")
        return False
    except FileFormatError as e:
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

def getRemoteHash(site, filename):
    # https://commons.wikimedia.org/wiki/Special:ApiSandbox#action=query&format=json&prop=imageinfo&titles=File%3ASalda%C3%B1a%20-%20015%20(26238038617).jpg&iiprop=timestamp%7Cuser%7Csha1
    result = site.api('query', prop = 'imageinfo', iiprop = 'timestamp|user|sha1', titles=filename)
    pageid = sha = None
    for i in result['query']['pages']:
        pageid = str(i)
    for i in result['query']['pages'][pageid]['imageinfo']:
        sha = i['sha1']
    return sha


def verifyHash(site, lhash, rhash): #TODO: Verify that everything works correctly
    return lhash == rhash

# Add template to image page
def tag_page(page, site, tag):
    text = page.text()
    text = tag + "\n" + text
    return text

# This should _really_ be done using a database. Perhaps pybind11 eventually(?)
def store_run_pages():
    global pages_run_set
    with open('run.txt', 'a+') as f:
        for item in pages_run_set:
            f.write('%s\n' % item)

# This should _really_ be done using a database. Perhaps pybind11 eventually(?)
def load_run_pages():
    global pages_run_set
    print("Loading pages")
    with open('run.txt', 'r') as f:
        for item in f:
            pages_run_set.add(item)
            print("Adding " + item) #FIXME: This spams console a LOT


def call_home(site_obj, key):
    page = site_obj.Pages['User:TheSandBot/status']
    text = page.text()
    data = json.loads(text)["run"]["corrupt_image_finder"][key]
    if str(data) == str(True):
        return True
    return False
