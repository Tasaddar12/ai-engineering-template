import unittest

from _pilot.a import increment


class TestIncrement(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(increment(0), 1)

    def test_one(self):
        self.assertEqual(increment(1), 2)

    def test_negative_two(self):
        self.assertEqual(increment(-2), -1)

    def test_twenty(self):
        self.assertEqual(increment(20), 21)


if __name__ == "__main__":
    unittest.main()
