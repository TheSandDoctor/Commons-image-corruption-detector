from PIL import Image
from PIL import ImageFile
ImageFile.MAXBLOCK = 1

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

# Process image
def process_file(page, site):
    image_page = page #site.Pages["""""" + str(page_name) + """"""]
    text = None
    # Download image
    with open("./Example.jpg","wb") as fd:
        image_page.download(fd)
    # Read and check if valid
    with open("./Example.jpg", "rb") as f:
        result = image_is_corrupt(f) #TODO: Add logic to tag page
    if result:
        text = tag_page(image_page, site, "{{Template:User:TheSandDoctor/Template:TSB image identified corrupt|" + datetime.now(timezone.utc).strftime("%Y-%m-%d") + "}}")
        save_page(text,"Image detected as corrupt, tagging.")
        print("Saved page")


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
