"""base62: 0-9, a-z, A-Z 순서. encode(0)은 "0"."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = 62


def encode(n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n must be a non-negative integer")
    if n == 0:
        return ALPHABET[0]
    out = []
    while n > 0:
        n, r = divmod(n, BASE)
        out.append(ALPHABET[r])
    return "".join(reversed(out))


def decode(s):
    if not isinstance(s, str) or s == "":
        raise ValueError("s must be a non-empty string")
    n = 0
    for ch in s:
        d = ALPHABET.find(ch)
        if d < 0:
            raise ValueError(f"invalid base62 character: {ch!r}")
        n = n * BASE + d
    return n
