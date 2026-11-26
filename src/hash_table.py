"""직접 만든 해시 테이블 두 가지. dict, set, 내장 hash()는 쓰지 않는다.

- HashTable            : 개별 체이닝 (칸마다 연결 리스트)
- LinearProbingTable   : 선형 탐지 (open addressing)

두 클래스는 같은 인터페이스를 가진다:
    put(key, value), get(key), search(key) -> (value, cost), key in table,
    len(table), table.size, table.load, items()
search의 cost: 체이닝은 '비교한 노드 수', 선형 탐지는 '들여다본 칸 수'.
max_load=None 이면 테이블이 커지지 않는다 (실험용).
"""

MULTIPLIER = 31


def horner_hash(key, size):
    """호너 방식: h <- (31*h + 글자 코드) mod size"""
    h = 0
    for ch in key:
        h = (MULTIPLIER * h + ord(ch)) % size
    return h


def horner_trace(key, size):
    """글자마다 (글자, 글자 코드, 이전 h, 새 h). 마지막 새 h가 칸 번호."""
    steps = []
    h = 0
    for ch in key:
        before = h
        h = (MULTIPLIER * h + ord(ch)) % size
        steps.append((ch, ord(ch), before, h))
    return steps


def _is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def next_prime(n):
    while not _is_prime(n):
        n += 1
    return n


class _Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None


class HashTable:
    """개별 체이닝."""

    name = "chaining"

    def __init__(self, size=11, max_load=0.75):
        if size < 1:
            raise ValueError("size must be >= 1")
        self.size = size
        self.max_load = max_load
        self._slots = [None] * size  # 칸마다 연결 리스트의 head
        self._count = 0

    def __len__(self):
        return self._count

    @property
    def load(self):
        return self._count / self.size

    def index(self, key):
        return horner_hash(key, self.size)

    def search(self, key):
        """(값 또는 None, 비교한 노드 수). 빈 칸이면 비용 0."""
        node = self._slots[self.index(key)]
        compared = 0
        while node is not None:
            compared += 1
            if node.key == key:
                return node.value, compared
            node = node.next
        return None, compared

    def get(self, key):
        return self.search(key)[0]

    def __contains__(self, key):
        idx = self.index(key)
        node = self._slots[idx]
        while node is not None:
            if node.key == key:
                return True
            node = node.next
        return False

    def put(self, key, value):
        idx = self.index(key)
        node = self._slots[idx]
        last = None
        while node is not None:
            if node.key == key:
                node.value = value  # 같은 키는 값만 갱신
                return
            last = node
            node = node.next
        if self.max_load is not None and (self._count + 1) / self.size > self.max_load:
            self._grow()
            self.put(key, value)
            return
        new = _Node(key, value)
        if last is None:
            self._slots[idx] = new
        else:
            last.next = new
        self._count += 1

    def _grow(self):
        old = list(self.items())
        self.size = next_prime(self.size * 2)
        self._slots = [None] * self.size
        self._count = 0
        for k, v in old:
            self.put(k, v)

    def items(self):
        for _, nodes in self.chains():
            for k, v in nodes:
                yield k, v

    def chains(self):
        """칸 번호와 그 칸의 (key, value) 목록. 화면 표시용."""
        for i, node in enumerate(self._slots):
            nodes = []
            while node is not None:
                nodes.append((node.key, node.value))
                node = node.next
            yield i, nodes


class LinearProbingTable:
    """선형 탐지. 충돌하면 다음 칸으로 가고, 끝 칸 다음은 0번 칸."""

    name = "linear"

    def __init__(self, size=11, max_load=0.7):
        if size < 1:
            raise ValueError("size must be >= 1")
        self.size = size
        self.max_load = max_load
        self._slots = [None] * size  # (key, value) 또는 None
        self._count = 0

    def __len__(self):
        return self._count

    @property
    def load(self):
        return self._count / self.size

    def index(self, key):
        return horner_hash(key, self.size)

    def _find(self, key):
        """(찾은 칸 또는 None, 들여다본 칸 수). 마지막 빈 칸도 1로 센다."""
        idx = self.index(key)
        examined = 0
        while examined < self.size:
            examined += 1
            slot = self._slots[idx]
            if slot is None:
                return None, examined
            if slot[0] == key:
                return idx, examined
            idx = (idx + 1) % self.size
        return None, examined  # 가득 찬 테이블에서 없는 키

    def search(self, key):
        idx, examined = self._find(key)
        if idx is None:
            return None, examined
        return self._slots[idx][1], examined

    def get(self, key):
        return self.search(key)[0]

    def __contains__(self, key):
        return self._find(key)[0] is not None

    def put(self, key, value):
        found, _ = self._find(key)
        if found is not None:
            self._slots[found] = (key, value)
            return
        if self.max_load is not None and (self._count + 1) / self.size > self.max_load:
            self._grow()
            self.put(key, value)
            return
        if self._count >= self.size:
            raise OverflowError("table is full")
        idx = self.index(key)
        while self._slots[idx] is not None:
            idx = (idx + 1) % self.size
        self._slots[idx] = (key, value)
        self._count += 1

    def _grow(self):
        old = list(self.items())
        self.size = next_prime(self.size * 2)
        self._slots = [None] * self.size
        self._count = 0
        for k, v in old:
            self.put(k, v)

    def items(self):
        for slot in self._slots:
            if slot is not None:
                yield slot

    def entries(self):
        """칸 번호, (key, value) 또는 None. 화면 표시용."""
        for i, slot in enumerate(self._slots):
            yield i, slot

    def probe_path(self, key):
        """이 키를 찾을 때 들여다보는 칸 번호들 (원래 칸부터 키가 있는 칸까지)."""
        idx = self.index(key)
        path = []
        for _ in range(self.size):
            path.append(idx)
            slot = self._slots[idx]
            if slot is None or slot[0] == key:
                break
            idx = (idx + 1) % self.size
        return path
