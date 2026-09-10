import unittest

from _pilot.c import combined


class TestCombined(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(combined(0), 2)

    def test_one(self):
        self.assertEqual(combined(1), 4)

    def test_negative_two(self):
        self.assertEqual(combined(-2), -2)

    def test_twenty(self):
        self.assertEqual(combined(20), 42)


if __name__ == "__main__":
    unittest.main()
