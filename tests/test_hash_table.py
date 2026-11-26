"""같은 테스트를 체이닝과 선형 탐지 양쪽에 돌린다."""
import unittest

from src.hash_table import HashTable, LinearProbingTable, horner_hash, horner_trace


def keys_with_home(size, home, n):
    """호너 해시가 home 칸인 키 n개."""
    out, i = [], 0
    while len(out) < n:
        k = f"key-{i}"
        if horner_hash(k, size) == home:
            out.append(k)
        i += 1
    return out


class HornerTest(unittest.TestCase):
    def test_known_value(self):
        # "ab", M=97: h=97 mod 97=0 -> (31*0+97)%97=0 ; then (31*0+98)%97=1
        self.assertEqual(horner_hash("ab", 97), 1)

    def test_deterministic_and_in_range(self):
        for k in ["", "a", "https://github.com", "한글"]:
            self.assertEqual(horner_hash(k, 11), horner_hash(k, 11))
            self.assertTrue(0 <= horner_hash(k, 11) < 11)

    def test_trace_matches_hash(self):
        url = "https://www.yonsei.ac.kr"
        steps = horner_trace(url, 11)
        self.assertEqual(steps[-1][3], horner_hash(url, 11))
        h = 0
        for ch, code, before, after in steps:
            self.assertEqual(before, h)
            self.assertEqual(after, (31 * before + code) % 11)
            h = after


class TableContract:
    """서브클래스가 make(size, max_load)를 정의한다."""

    def make(self, size=11, max_load=0.75):
        raise NotImplementedError

    def test_empty(self):
        t = self.make()
        self.assertEqual(len(t), 0)
        self.assertIsNone(t.get("x"))
        self.assertNotIn("x", t)

    def test_put_get(self):
        t = self.make()
        t.put("a", 1)
        t.put("b", 2)
        self.assertEqual(t.get("a"), 1)
        self.assertEqual(t.get("b"), 2)
        self.assertIn("a", t)
        self.assertEqual(len(t), 2)

    def test_update_same_key(self):
        t = self.make()
        t.put("a", 1)
        t.put("a", 2)
        self.assertEqual(t.get("a"), 2)
        self.assertEqual(len(t), 1)

    def test_collision_keys_all_retrievable(self):
        t = self.make(size=11, max_load=None)
        keys = keys_with_home(11, 3, 5)  # 모두 같은 칸에 떨어진다
        for i, k in enumerate(keys):
            t.put(k, i)
        for i, k in enumerate(keys):
            self.assertEqual(t.get(k), i)
        self.assertEqual(len(t), 5)

    def test_search_cost(self):
        t = self.make(size=11, max_load=None)
        a, b, c = keys_with_home(11, 3, 3)
        t.put(a, 1)
        t.put(b, 2)
        self.assertEqual(t.search(a), (1, 1))  # 첫 번째로 만난다
        self.assertEqual(t.search(b)[1], 2)  # 충돌한 뒤 두 번째
        # 없는 키: 체이닝은 노드 2개 비교, 선형 탐지는 칸 3개(마지막 빈 칸 포함)
        value, cost = t.search(c)
        self.assertIsNone(value)
        self.assertEqual(cost, self.miss_cost_after_two)

    def test_miss_on_empty_slot(self):
        t = self.make(size=11, max_load=None)
        value, cost = t.search("nothing")
        self.assertIsNone(value)
        self.assertEqual(cost, self.miss_cost_empty)

    def test_grow_keeps_everything(self):
        t = self.make(size=3, max_load=0.7)
        for i in range(200):
            t.put(f"https://example.com/{i}", i)
        self.assertGreater(t.size, 3)
        self.assertLessEqual(t.load, 0.7 + 1e-9)
        for i in range(200):
            self.assertEqual(t.get(f"https://example.com/{i}"), i)
        self.assertEqual(len(t), 200)
        self.assertEqual(sorted(v for _, v in t.items()), list(range(200)))

    def test_no_grow_when_max_load_none(self):
        t = self.make(size=7, max_load=None)
        for i in range(5):
            t.put(f"k{i}", i)
        self.assertEqual(t.size, 7)


class ChainingTest(TableContract, unittest.TestCase):
    miss_cost_after_two = 2
    miss_cost_empty = 0

    def make(self, size=11, max_load=0.75):
        return HashTable(size, max_load)

    def test_load_above_one(self):
        t = self.make(size=5, max_load=None)
        for i in range(20):
            t.put(f"k{i}", i)
        self.assertEqual(len(t), 20)
        self.assertAlmostEqual(t.load, 4.0)
        for i in range(20):
            self.assertEqual(t.get(f"k{i}"), i)

    def test_chains_view(self):
        t = self.make(size=11, max_load=None)
        a, b = keys_with_home(11, 3, 2)
        t.put(a, 1)
        t.put(b, 2)
        chains = dict(t.chains())
        self.assertEqual(chains[3], [(a, 1), (b, 2)])


class LinearProbingTest(TableContract, unittest.TestCase):
    miss_cost_after_two = 3
    miss_cost_empty = 1

    def make(self, size=11, max_load=0.7):
        return LinearProbingTable(size, max_load)

    def test_wrap_around(self):
        t = self.make(size=5, max_load=None)
        keys = keys_with_home(5, 4, 3)  # 마지막 칸(4번)이 원래 자리
        for i, k in enumerate(keys):
            t.put(k, i)
        slots = {i: s for i, s in t.entries() if s is not None}
        self.assertEqual(slots[4][0], keys[0])
        self.assertEqual(slots[0][0], keys[1])  # 끝 칸에서 0번 칸으로 넘어간다
        self.assertEqual(slots[1][0], keys[2])
        for i, k in enumerate(keys):
            self.assertEqual(t.get(k), i)

    def test_full_table(self):
        t = self.make(size=5, max_load=None)
        for i in range(5):
            t.put(f"k{i}", i)
        self.assertEqual(len(t), 5)
        for i in range(5):
            self.assertEqual(t.get(f"k{i}"), i)
        value, cost = t.search("not-there")  # 가득 차도 무한 반복하지 않는다
        self.assertIsNone(value)
        self.assertEqual(cost, 5)
        with self.assertRaises(OverflowError):
            t.put("one-more", 9)
        t.put("k0", 100)  # 이미 있는 키의 갱신은 가능하다
        self.assertEqual(t.get("k0"), 100)

    def test_probe_path(self):
        t = self.make(size=11, max_load=None)
        a, b = keys_with_home(11, 3, 2)
        t.put(a, 1)
        t.put(b, 2)
        self.assertEqual(t.probe_path(a), [3])
        self.assertEqual(t.probe_path(b), [3, 4])


if __name__ == "__main__":
    unittest.main()
