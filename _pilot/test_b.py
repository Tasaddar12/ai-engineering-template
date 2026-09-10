import unittest

from _pilot.b import double


class DoubleTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(double(0), 0)

    def test_one(self):
        self.assertEqual(double(1), 2)

    def test_negative(self):
        self.assertEqual(double(-2), -4)

    def test_twenty(self):
        self.assertEqual(double(20), 40)


if __name__ == "__main__":
    unittest.main()
