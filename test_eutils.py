import unittest
from EUtils import EDayCount, EJobType


class TestEUtils(unittest.TestCase):
    def test_days_7(self):
        self.assertEqual(EDayCount.DAYS_7.value, "7 days")

    def test_days_30(self):
        self.assertEqual(EDayCount.DAYS_30.value, "30 days")

    def test_full_scan(self):
        self.assertEqual(EJobType.FULL_SCAN.value, "full_scan")

    def test_monitor(self):
        self.assertEqual(EJobType.MONITOR.value, "monitor")


if __name__ == '__main__':
    unittest.main()
