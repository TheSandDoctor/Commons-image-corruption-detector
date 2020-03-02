import unittest
from PIL import Image


# TODO: When figure out how, this should be replaced with proper live func from image_corruption_utils
def is_corrupt(name):
    with open(name, 'rb') as f:
        try:
            image = Image.open(f)
            image.tobytes()
            return False
        except Image.UnidentifiedImageError as e:
            raise
        except OSError:
            return True


class TestCorruptionChecking(unittest.TestCase):

    def test_false(self):
        self.assertEqual(is_corrupt("Test.jpg"), True)

    def test_true(self):
        self.assertEqual(is_corrupt("Tarnow_Park_Strzelecki_wiewiorka_5.jpg"), False)

    def test_non_image(self):
        self.assertRaises(Image.UnidentifiedImageError, is_corrupt, "Video_of_Heat_shrink_tube_before_and_after.ogv")


if __name__ == '__main__':
    unittest.main()
