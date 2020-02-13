import pwb_wrappers
for image_page in pwb_wrappers.allimages(reverse=True):
    print(image_page.title())