from __future__ import absolute_import

import traceback

from PIL import Image
from PIL import ImageFile


ImageFile.MAXBLOCK = 1


def detect(f):
    try:
        image = Image.open(f)

        image.tobytes()
        print("Works")
    except Exception as e:
        print("Corrupt\n\n") # If we get this far, image is corrupt
        print(e)


if __name__ == '__main__':
    detect("./River_GK_rojo_.png")
    detect("./Test.jpg")
