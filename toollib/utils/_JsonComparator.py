from __future__ import annotations

import hashlib
import json
import zlib
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal


@dataclass(slots=True)
class _Config:
    excluded_keys: set[str]
    float_precision: int
    strict_numtype: bool
    list_sort: Literal["json", "repr", "smart"] | None


class JsonComparator:
    """JSON比较器

    提供 JSON 数据的标准化、等价比较、差异分析和稳定摘要功能。
    支持自定义浮点精度、忽略指定字段、列表排序策略等配置。

    Attributes:
        excluded_keys: 标准化时忽略的字段名集合。
        float_precision: 浮点数保留的小数位数。
        strict_numtype: 是否严格区分数字类型 int 与 float。
        list_sort: 列表排序策略。
            - None 表示有序比较
            - Literal["json", "repr", "smart"] 表示无序比较及排序方式

    e.g.::

        jc = JsonComparator()

        jc.normalize({"a": 1.000000001, "b": [3, 2]})
        jc.compare({"a": 1}, {"a": 1.0})
        jc.diff({"a": 1}, {"a": 1.0})
        jc.digest({"a": 1})

        +++++[更多详见参数或源码]+++++
    """

    __slots__ = (
        "excluded_keys",
        "float_precision",
        "strict_numtype",
        "list_sort",
        "_quantizers",
    )

    def __init__(
        self,
        *,
        excluded_keys: set[str] | None = None,
        float_precision: int = 9,
        strict_numtype: bool = True,
        list_sort: Literal["json", "repr", "smart"] | None = None,
    ) -> None:
        """初始化 JsonComparator。

        Args:
            excluded_keys: 标准化时忽略的字段名集合。默认 None。
            float_precision: 浮点数保留的小数位数。默认 9。
            strict_numtype: 是否严格区分数字类型 int 与 float。
                True 时 1 和 1.0 不相等，False 时相等。默认 True。
            list_sort: 列表排序策略，可选值：

                - None: 有序比较，[1,2] 与 [2,1] 不等（默认）。
                - "json": 无序比较，最稳定的排序方式，但速度较慢。
                - "repr": 无序比较，最快的排序方式，但可能不稳定。
                - "smart": 无序比较，兼顾速度与稳定性，工业推荐。
        """

        self.excluded_keys = excluded_keys or set()
        self.float_precision = float_precision
        self.strict_numtype = strict_numtype
        self.list_sort = list_sort

        self._validate_list_sort(self.list_sort)

        self._quantizers: dict[int, Decimal] = {}

    # =========================================================
    # Public API
    # =========================================================

    def normalize(
        self,
        obj: Any,
        *,
        excluded_keys: set[str] | None = None,
        float_precision: int | None = None,
        strict_numtype: bool | None = None,
        list_sort: Literal["json", "repr", "smart"] | None = ...,
    ) -> Any:
        """将 JSON 对象标准化为规范形式。

        对 dict 按键排序并移除排除字段，对 list 按策略排序，
        对 float 按精度舍入。标准化后的对象可直接用 == 进行语义等价比较。

        Args:
            obj: 待标准化的 JSON 对象。
            excluded_keys: 覆盖实例级别的忽略字段集合。
            float_precision: 覆盖实例级别的浮点精度。
            strict_numtype: 覆盖实例级别的数字类型严格模式。
            list_sort: 覆盖实例级别的列表排序策略。

        Returns:
            标准化后的 JSON 对象。
        """

        config = self._build_config(
            excluded_keys,
            float_precision,
            strict_numtype,
            list_sort,
        )

        return self._normalize(obj, config)

    def compare(
        self,
        obj1: Any,
        obj2: Any,
        **kwargs,
    ) -> bool:
        """判断两个 JSON 对象是否语义等价。

        分别标准化两个对象后使用 == 比较。

        Args:
            obj1: 第一个 JSON 对象。
            obj2: 第二个 JSON 对象。
            **kwargs: 传递给 normalize 的覆盖参数。

        Returns:
            语义等价返回 True，否则返回 False。
        """

        return self.normalize(obj1, **kwargs) == self.normalize(obj2, **kwargs)

    def diff(
        self,
        obj1: Any,
        obj2: Any,
        *,
        max_diffs: int | None = None,
        **kwargs,
    ) -> list[dict]:
        """比较两个 JSON 对象并返回差异列表。

        先标准化再逐层递归比较，记录所有差异点。

        Args:
            obj1: 第一个 JSON 对象。
            obj2: 第二个 JSON 对象。
            max_diffs: 最大返回差异数量，None 表示不限制。
            **kwargs: 传递给 normalize 的覆盖参数。

        Returns:
            差异列表，每项是包含以下字段的字典：

                - path (str): JSONPath 路径。
                - reason (str): 差异原因，可能值：
                  "type_mismatch"、"missing_in_right"、"missing_in_left"、
                  "length_mismatch"、"value_mismatch"。
                - left: 左侧值。
                - right: 右侧值。
        """

        config = self._build_config(**kwargs)

        left = self._normalize(obj1, config)
        right = self._normalize(obj2, config)

        out: list[dict] = []

        self._diff(left, right, path="$", out=out, max_diffs=max_diffs)

        return out

    def digest(self, obj: Any, **kwargs) -> str:
        """生成 JSON 对象的稳定 SHA-256 摘要。

        先标准化再序列化为规范 JSON 字符串，计算 SHA-256 哈希。
        相同语义的对象生成相同摘要，适合用于缓存键或去重。

        Args:
            obj: 待摘要的 JSON 对象。
            **kwargs: 传递给 normalize 的覆盖参数。

        Returns:
            64 位十六进制 SHA-256 摘要字符串。
        """

        normalized = self.normalize(obj, **kwargs)

        canonical = json.dumps(
            normalized,
            sort_keys=kwargs.get("list_sort", self.list_sort) is None,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        return hashlib.sha256(canonical.encode()).hexdigest()

    # =========================================================
    # Config
    # =========================================================

    _VALID_LIST_SORTS = frozenset({"json", "repr", "smart"})

    @classmethod
    def _validate_list_sort(cls, value: str | None) -> None:
        if value is not None and value not in cls._VALID_LIST_SORTS:
            raise ValueError(f"list_sort must be None or one of {sorted(cls._VALID_LIST_SORTS)}, got {value!r}")

    def _build_config(
        self,
        excluded_keys=None,
        float_precision=None,
        strict_numtype=None,
        list_sort=...,
    ) -> _Config:

        return _Config(
            excluded_keys=self.excluded_keys if excluded_keys is None else excluded_keys,
            float_precision=self.float_precision if float_precision is None else float_precision,
            strict_numtype=self.strict_numtype if strict_numtype is None else strict_numtype,
            list_sort=self.list_sort if list_sort is ... else list_sort,
        )

    # =========================================================
    # Normalize
    # =========================================================

    def _normalize(self, obj: Any, cfg: _Config) -> Any:

        if isinstance(obj, dict):
            return {k: self._normalize(v, cfg) for k, v in sorted(obj.items()) if k not in cfg.excluded_keys}

        if isinstance(obj, list):
            items = [self._normalize(v, cfg) for v in obj]

            if cfg.list_sort is not None:
                items.sort(key=lambda x: self._sort_key(x, cfg.list_sort))

            return items

        if isinstance(obj, bool):
            return obj

        if isinstance(obj, int) and not isinstance(obj, bool):
            if cfg.strict_numtype:
                return obj
            return self._normalize_float(float(obj), cfg.float_precision)

        if isinstance(obj, float):
            v = self._normalize_float(obj, cfg.float_precision)

            if cfg.strict_numtype:
                return v

            return int(v) if v.is_integer() else v

        return obj

    # =========================================================
    # Float
    # =========================================================

    def _normalize_float(self, value: float, precision: int) -> float:
        q = self._quantizers.get(precision)
        if q is None:
            q = Decimal("1." + "0" * precision)
            self._quantizers[precision] = q

        return float(Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP))

    # =========================================================
    # Sort Key
    # =========================================================

    def _sort_key(self, value: Any, mode: Literal["json", "repr", "smart"]) -> Any:

        # 1. 快路径：简单类型
        if value is None or isinstance(value, (int, float, bool, str)):
            return (0, value)

        # 2. repr（最快）
        if mode == "repr":
            return (1, repr(value))

        # 3. smart（推荐）
        if mode == "smart":
            try:
                h = zlib.crc32(repr(value).encode())
                return (2, h)
            except Exception:
                return (3, id(value))

        # 4. json（最稳定）
        return (
            4,
            json.dumps(
                value,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

    # =========================================================
    # Diff
    # =========================================================

    def _diff(self, left, right, *, path, out, max_diffs):

        if max_diffs is not None and len(out) >= max_diffs:
            return

        if left == right:
            return

        if type(left) is not type(right):
            out.append({"path": path, "reason": "type_mismatch", "left": left, "right": right})
            return

        if isinstance(left, dict):
            lk, rk = set(left), set(right)

            for k in lk - rk:
                out.append({"path": f"{path}.{k}", "reason": "missing_in_right", "left": left[k], "right": None})

            for k in rk - lk:
                out.append({"path": f"{path}.{k}", "reason": "missing_in_left", "left": None, "right": right[k]})

            for k in lk & rk:
                self._diff(left[k], right[k], path=f"{path}.{k}", out=out, max_diffs=max_diffs)

            return

        if isinstance(left, list):
            if len(left) != len(right):
                out.append({"path": path, "reason": "length_mismatch", "left": len(left), "right": len(right)})
                return

            for i, (l, r) in enumerate(zip(left, right, strict=True)):
                self._diff(l, r, path=f"{path}[{i}]", out=out, max_diffs=max_diffs)

            return

        out.append({"path": path, "reason": "value_mismatch", "left": left, "right": right})
