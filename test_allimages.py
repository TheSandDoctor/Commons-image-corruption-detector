import pwb_wrappers
for image_page in pwb_wrappers.allimages(reverse=False):
    print(image_page.title())