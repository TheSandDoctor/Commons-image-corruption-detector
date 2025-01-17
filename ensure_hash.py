import image_corruption_utils as icu
import database_stuff as db
from PIL import UnidentifiedImageError
import mwparserfromhell
import pywikibot
import pwb_wrappers
import os

def run(site, image, isCorrupt, date_scanned, to_delete_nom):
    image_page = pywikibot.FilePage(site, image)
    _, ext = os.path.splitext(image_page.title())  # get filetype
    if not icu.allow_bots(image_page.text, "TheSandBot"):
        print("Not to edit " + image_page.title())
        return
    download_attempts = 0
    failed = 0
    while True:
        #with open("./Example4" + ext, "wb") as fd:
        image_page.download("./Example4" + ext)

        hash_result, img_hash = icu.verify_hash(site, "./Example4" + ext, image_page)
        if not hash_result:
            if download_attempts >= 10:
                failed = 1
                break
            download_attempts += 1
            continue
        else:
            break
    if failed:
        raise ValueError(
            "Hash check failed for ./Example4{0} vs {1} {2} times. Aborting...".format(ext, str(image_page.title()),
                                                                                       str(download_attempts)))

    del download_attempts
    try:
        result = icu.image_is_corrupt("./Example4" + ext)
    except UnidentifiedImageError:
        os.remove("./Example4" + ext)  # file not an image.
        raise
    del ext  # no longer a needed variable
    if result:  # image corrupt
        return
    else:  # image not corrupt
        edit_summary = "Removing [[Template:TSB image identified corrupt]] - image no longer corrupt"

        code = mwparserfromhell.parse(image_page.text)
        for template in code.filter_templates():
            if template.name.matches("TSB image identified corrupt"):
                code.remove(template)  # template no longer needed
        try:
            pwb_wrappers.retry_apierror(
                lambda:
                image_page.save(text=str(code),
                                summary=edit_summary, minor=False, botflag=True, force=True)
            )
        except pywikibot.exceptions.LockedPage as e:
            print(image_page.title())
            print(e.message)
        # update database entry to set image as no longer corrupt and nullify to_delete_nom
        db.update_entry(str(image_page.title()), False, None, img_hash, was_fixed=True)


if __name__ == '__main__':
    site = pywikibot.Site('commons', 'commons', user='TheSandBot')
    raw = db.get_all_corrupt()
    for i in raw:
        run(site, i[0], i[1], i[2], i[3])