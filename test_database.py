# -*- coding: UTF-8 -*-
from __future__ import print_function
import database_stuff
import image_corruption_utils
import manapi

###
# These tests require two jpg files, one named "test1.jph" and the other named "test2.jpg".
###

if __name__ == "__main__":
    ###
    # Currently testing the ability to add hashes and connect. The isCorrupt field is deliberately set as well and is
    # not authentic to the image at hand (for this test it doesn't matter).
    ###
    print("Starting 1")
    database_stuff.store_image("tests/test1.jpg", False, image_corruption_utils.get_local_hash("tests/test1.jpg"), 7, 1)
    print("Done 1")
    database_stuff.store_image("tests/test1.jpg", True, image_corruption_utils.get_local_hash("tests/test2.jpg"), page_id=2)
    print("Done 2")
    database_stuff.store_image("tests/test1.jpg", False, image_corruption_utils.get_local_hash("tests/test2.jpg"),
                               page_id=manapi.getPageID('USMC-080114-M-3913K-001.jpg'))
    database_stuff.store_image("Wirtschaftsschule Bayreuth.JPG", False, image_corruption_utils.get_local_hash("tests/test2.jpg"))
    print("Done 4")
    #database_stuff.update_entry("test1.jpg", True, datetime.now(timezone.utc).date().strftime('%B/%d/%Y'), image_corruption_utils.get_local_hash("test.jpg"))
