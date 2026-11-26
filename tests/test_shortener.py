"""단축기 테스트를 두 테이블에서 모두 돌린다."""
import unittest

from src.base62 import encode
from src.hash_table import HashTable, LinearProbingTable
from src.shortener import Shortener


class ShortenerContract:
    table_class = None

    def make(self):
        return Shortener(self.table_class, size=3)  # 작게 시작해서 늘어나는 것도 확인

    def test_shorten_and_resolve(self):
        s = self.make()
        code = s.shorten("https://github.com")
        self.assertEqual(s.resolve(code), "https://github.com")

    def test_same_url_same_code(self):
        s = self.make()
        a = s.shorten("https://www.yonsei.ac.kr")
        b = s.shorten("https://www.yonsei.ac.kr")
        self.assertEqual(a, b)
        self.assertEqual(len(s), 1)

    def test_different_urls_different_codes(self):
        s = self.make()
        urls = [f"https://example.com/{i}" for i in range(300)]
        codes = [s.shorten(u) for u in urls]
        self.assertEqual(len(codes), 300)
        for i, c in enumerate(codes):  # 코드가 서로 겹치지 않는다
            for c2 in codes[i + 1:i + 5]:
                self.assertNotEqual(c, c2)
        self.assertEqual(codes, [encode(i + 1) for i in range(300)])
        for u, c in zip(urls, codes):
            self.assertEqual(s.resolve(c), u)

    def test_unknown_code(self):
        s = self.make()
        self.assertIsNone(s.resolve("zzzz"))
        self.assertIsNone(s.resolve(""))
        self.assertIsNone(s.resolve(None))

    def test_invalid_urls(self):
        s = self.make()
        bad = ["", "ftp://files.example.com", "github.com", "https://", "http://",
               "https://a b.com", " https://github.com", "https://github.com\n",
               "https://" + "a" * 2100, None, 123, "javascript:alert(1)"]
        for url in bad:
            with self.assertRaises(ValueError, msg=repr(url)[:40]):
                s.shorten(url)
        self.assertEqual(len(s), 0)

    def test_http_and_https_are_different_urls(self):
        s = self.make()
        self.assertNotEqual(s.shorten("http://a.com"), s.shorten("https://a.com"))


class ChainingShortenerTest(ShortenerContract, unittest.TestCase):
    table_class = HashTable


class LinearShortenerTest(ShortenerContract, unittest.TestCase):
    table_class = LinearProbingTable


if __name__ == "__main__":
    unittest.main()
