import unittest

from src.base62 import decode, encode


class Base62Test(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(encode(0), "0")

    def test_alphabet_order(self):
        self.assertEqual(encode(9), "9")
        self.assertEqual(encode(10), "a")
        self.assertEqual(encode(35), "z")
        self.assertEqual(encode(36), "A")
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")
        self.assertEqual(encode(3844), "100")

    def test_roundtrip(self):
        for n in [0, 1, 61, 62, 3843, 3844, 100_000_000, 2**64]:
            self.assertEqual(decode(encode(n)), n)

    def test_invalid(self):
        for bad in [-1, 1.5, "1", None, True]:
            with self.assertRaises(ValueError):
                encode(bad)
        for bad in ["", "a-b", " ", None]:
            with self.assertRaises(ValueError):
                decode(bad)


if __name__ == "__main__":
    unittest.main()
