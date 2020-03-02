import unittest
from database_stuff import have_seen_image
import pywikibot


class Test_have_seen_image(unittest.TestCase):
    def test_something(self):
        import pywikibot
        site = pywikibot.Site(user="TheSandBot")
        image_page = pywikibot.FilePage(site, "File:Forssa.sijainti.Suomi.2020.svg")
        self.assertEqual(True, have_seen_image(site, image_page.title()))


if __name__ == '__main__':
    unittest.main()
