from PIL import Image
from PIL import ImageFile
import mysql.connector
ImageFile.MAXBLOCK = 1

config = {
  'user': 'scott',
  'password': 'password',
  'host': '127.0.0.1',
  'database': 'employees',
  'raise_on_warnings': True
}

# Check if image is corrupt. If an image is corrupt, it will fail .tobytes()
def image_is_corrupt(f):
    try:
        image = Image.open(f)
        image.tobytes()
        print("Works")
        return False
    except Exception as e:
        print("Corrupt\n") # If we get this far, image is corrupt
        #print(e)
        return True

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


def call_home(site_obj):
    page = site_obj.Pages['User:TheSandBot/status']
    text = page.text()
    data = json.loads(text)["run"]["corrupt_image_finder"]
    if str(data) == str(True):
        return True
    return False
