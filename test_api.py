import unittest
import manapi

class TestManAPI(unittest.TestCase):
    def test_getPageID(self):
        self.assertEqual(manapi.getPageID("Ermita de Santo Cristo de Miranda, Santa"
                                          " María de las Hoyas, Soria, España, 2017-05-26, DD 65.jpg"), 63029000)


if __name__ == '__main__':
    unittest.main()
