from functools import total_ordering

# ========================
# 字符分类表
# 0=other, 1=digit, 2=alpha
# ========================
_TYPE_TABLE = [0] * 128
for i in range(ord("0"), ord("9") + 1):
    _TYPE_TABLE[i] = 1
for i in range(ord("a"), ord("z") + 1):
    _TYPE_TABLE[i] = 2


def _h(word: str) -> int:
    """rolling hash"""
    h = 0
    for c in word:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return h


@total_ordering
class VersionCmper:
    """
    版本比较器

    e.g.::

        from toollib.utils import VersionCmper

        VersionCmper.gt("1.0.1", "1.0.a")

        sorted(["1.0.a", "1.0.1"], key=VersionCmper.key)

        VersionCmper.set_order(["a", "b", "rc", "1"])

        +++++[更多详见参数或源码]+++++
    """

    __slots__ = ("_s",)

    DEFAULT_ORDER = ["dev", "alpha", "a", "beta", "b", "rc", "post"]
    _order_hash: dict[int, int] = {_h(word): idx for idx, word in enumerate(DEFAULT_ORDER)}

    @classmethod
    def set_order(cls, order: list[str]):
        """设置顺序（靠后更大）"""
        cls._order_hash = {_h(word): idx for idx, word in enumerate(order)}

    @classmethod
    def reset_order(cls):
        """重置顺序"""
        cls._order_hash = {_h(word): idx for idx, word in enumerate(cls.DEFAULT_ORDER)}

    @classmethod
    def compare(cls, v1: str, v2: str) -> int:
        """比较版本：返回 -1 / 0 / 1"""
        return cls(v1)._compare(cls(v2))

    @classmethod
    def gt(cls, v1: str, v2: str) -> bool:
        return cls.compare(v1, v2) > 0

    @classmethod
    def lt(cls, v1: str, v2: str) -> bool:
        return cls.compare(v1, v2) < 0

    @classmethod
    def eq(cls, v1: str, v2: str) -> bool:
        return cls.compare(v1, v2) == 0

    @classmethod
    def ge(cls, v1: str, v2: str) -> bool:
        return cls.compare(v1, v2) >= 0

    @classmethod
    def le(cls, v1: str, v2: str) -> bool:
        return cls.compare(v1, v2) <= 0

    @classmethod
    def key(cls, v: str):
        """用于排序的 key"""
        return cls(v)

    # 核心实现

    def __init__(self, version: str):
        self._s = version.lower()

    def _compare(self, other: "VersionCmper"):
        s1, s2 = self._s, other._s
        n1, n2 = len(s1), len(s2)
        i = j = 0
        type_table = _TYPE_TABLE
        order_hash = self._order_hash

        while True:
            # 跳过分隔符
            while i < n1:
                c = ord(s1[i])
                if c < 128 and type_table[c]:
                    break
                i += 1
            while j < n2:
                c = ord(s2[j])
                if c < 128 and type_table[c]:
                    break
                j += 1

            # 结束判断
            if i >= n1 and j >= n2:
                return 0
            if i >= n1:
                return -1
            if j >= n2:
                return 1

            c1, c2 = s1[i], s2[j]
            t1 = type_table[ord(c1)] if ord(c1) < 128 else 0
            t2 = type_table[ord(c2)] if ord(c2) < 128 else 0

            # 数字 vs 数字
            if t1 == 1 and t2 == 1:
                num1 = num2 = 0
                while i < n1 and ord(s1[i]) < 128 and type_table[ord(s1[i])] == 1:
                    num1 = num1 * 10 + (ord(s1[i]) - 48)
                    i += 1
                while j < n2 and ord(s2[j]) < 128 and type_table[ord(s2[j])] == 1:
                    num2 = num2 * 10 + (ord(s2[j]) - 48)
                    j += 1
                if num1 != num2:
                    return 1 if num1 > num2 else -1
                continue

            # 字母 vs 字母
            if t1 == 2 and t2 == 2:
                h1 = h2 = 0
                len1 = len2 = 0
                while i < n1 and ord(s1[i]) < 128 and type_table[ord(s1[i])] == 2:
                    h1 = (h1 * 31 + ord(s1[i])) & 0xFFFFFFFF
                    len1 += 1
                    i += 1
                while j < n2 and ord(s2[j]) < 128 and type_table[ord(s2[j])] == 2:
                    h2 = (h2 * 31 + ord(s2[j])) & 0xFFFFFFFF
                    len2 += 1
                    j += 1

                # 自定义顺序
                m1 = order_hash.get(h1)
                m2 = order_hash.get(h2)
                if m1 is not None or m2 is not None:
                    v1_idx = m1 if m1 is not None else -1
                    v2_idx = m2 if m2 is not None else -1
                    if v1_idx != v2_idx:
                        return 1 if v1_idx > v2_idx else -1

                # fallback
                if len1 != len2:
                    return 1 if len1 > len2 else -1
                if h1 != h2:
                    return 1 if h1 > h2 else -1
                continue

            # 混合类型
            m1 = order_hash.get(_h(c1))
            m2 = order_hash.get(_h(c2))
            if m1 is not None or m2 is not None:
                v1_idx = m1 if m1 is not None else -1
                v2_idx = m2 if m2 is not None else -1
                if v1_idx != v2_idx:
                    return 1 if v1_idx > v2_idx else -1
            else:
                # 默认：数字 < 字母
                return -1 if t1 == 1 else 1

    def __eq__(self, other):
        if not isinstance(other, VersionCmper):
            return NotImplemented
        return self._compare(other) == 0

    def __lt__(self, other):
        if not isinstance(other, VersionCmper):
            return NotImplemented
        return self._compare(other) < 0

    def __repr__(self):
        return f"VersionCmper('{self._s}')"
