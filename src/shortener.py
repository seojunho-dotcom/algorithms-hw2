"""URL 단축기. 저장은 직접 만든 해시 테이블로 하고, 코드는 일련번호를 base62로 바꾼다.
(URL의 해시값을 코드로 쓰면 서로 다른 URL이 같은 코드를 받을 수 있다.)"""

from src.base62 import encode
from src.hash_table import HashTable

MAX_URL_LENGTH = 2048


def validate_url(url):
    """http:// 또는 https://로 시작하는 공백 없는 주소만 허용한다."""
    if not isinstance(url, str):
        raise ValueError("url must be a string")
    if url == "" or len(url) > MAX_URL_LENGTH:
        raise ValueError("url is empty or too long")
    if any(ch.isspace() for ch in url):
        raise ValueError("url must not contain whitespace")
    for scheme in ("http://", "https://"):
        if url.startswith(scheme) and len(url) > len(scheme):
            return url
    raise ValueError("url must start with http:// or https://")


class Shortener:
    def __init__(self, table_class=HashTable, **table_kwargs):
        self.url_to_code = table_class(**table_kwargs)
        self.code_to_url = table_class(**table_kwargs)
        self._next_id = 1

    def __len__(self):
        return len(self.url_to_code)

    def shorten(self, url):
        validate_url(url)
        existing = self.url_to_code.get(url)
        if existing is not None:  # 같은 URL은 같은 코드
            return existing
        code = encode(self._next_id)
        self._next_id += 1
        self.url_to_code.put(url, code)
        self.code_to_url.put(code, url)
        return code

    def resolve(self, code):
        """없는 코드는 None."""
        if not isinstance(code, str):
            return None
        return self.code_to_url.get(code)

    def expand(self, code):
        """resolve와 같다."""
        return self.resolve(code)
