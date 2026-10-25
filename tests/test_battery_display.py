import unittest

from nothingx.battery_display import battery_percent


class BatteryDisplayTests(unittest.TestCase):
    def test_zero_percent_is_displayed_as_a_reading(self):
        self.assertEqual(battery_percent(0), "0%")

    def test_missing_reading_is_displayed_as_unavailable(self):
        self.assertEqual(battery_percent(None), "--%")

    def test_positive_reading_is_displayed_as_a_percentage(self):
        self.assertEqual(battery_percent(67), "67%")


if __name__ == "__main__":
    unittest.main()
