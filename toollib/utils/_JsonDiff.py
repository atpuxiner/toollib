from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class JsonDiff:
    """
    Json差异检测

    e.g.::

        jd = JsonDiff()

        1. normalize: JSON 标准化
        2. compare: 是否等价
        3. diff: 结构差异分析

        +++++[更多详见参数或源码]+++++
    """

    __slots__ = (
        "ignore_keys",
        "float_digits",
        "int_as_float",
        "ignore_list_order",
    )

    def __init__(
        self,
        ignore_keys: set[str] | None = None,
        float_digits: int = 9,
        int_as_float: bool = False,
        ignore_list_order: bool = True,
    ):
        self.ignore_keys = ignore_keys or set()
        self.float_digits = float_digits
        self.int_as_float = int_as_float
        self.ignore_list_order = ignore_list_order

    # =========================================================
    # Public API
    # =========================================================

    def normalize(
        self,
        obj: Any,
    ) -> Any:
        """
        将 JSON 结构转换为 canonical form
        """
        return self._normalize(obj)

    def compare(
        self,
        obj1: Any,
        obj2: Any,
    ) -> bool:
        """
        判断两个 JSON 是否等价
        """
        return self.normalize(obj1) == self.normalize(obj2)

    def diff(
        self,
        obj1: Any,
        obj2: Any,
        *,
        int_as_float: bool | None = None,
        max_diffs: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        返回结构差异

        max_diffs:
            None -> 全量 diff
            1    -> first diff
        """
        left = self.normalize(obj1)
        right = self.normalize(obj2)

        result: list[dict[str, Any]] = []

        self._diff(
            left,
            right,
            path="$",
            out=result,
            max_diffs=max_diffs,
        )

        return result

    # =========================================================
    # Normalization
    # =========================================================

    def _normalize(
        self,
        obj: Any,
    ) -> Any:

        # dict
        if isinstance(obj, dict):
            return {k: self._normalize(v) for k, v in sorted(obj.items()) if k not in self.ignore_keys}

        # list
        if isinstance(obj, list):
            items = [self._normalize(v) for v in obj]

            if self.ignore_list_order:
                items.sort(key=repr)

            return items

        # float
        if isinstance(obj, float):
            v = self._normalize_float(obj)

            if not self.int_as_float and v.is_integer():
                return int(v)

            return v

        # int
        if isinstance(obj, int) and not isinstance(obj, bool):
            if self.int_as_float:
                return self._normalize_float(float(obj))
            return obj

        # bool / str / None
        return obj

    def _normalize_float(self, value: float) -> float:
        """
        float 精度统一
        """
        quantize_str = "1." + ("0" * self.float_digits)

        return float(
            Decimal(str(value)).quantize(
                Decimal(quantize_str),
                rounding=ROUND_HALF_UP,
            )
        )

    # =========================================================
    # Diff Engine
    # =========================================================

    def _diff(
        self,
        left: Any,
        right: Any,
        *,
        path: str,
        out: list[dict[str, Any]],
        max_diffs: int | None,
    ) -> None:

        # early stop
        if max_diffs is not None and len(out) >= max_diffs:
            return

        # type mismatch
        if type(left) is not type(right):
            out.append(
                {
                    "path": path,
                    "reason": "type_mismatch",
                    "left": left,
                    "right": right,
                }
            )
            return

        # dict
        if isinstance(left, dict):
            lk = set(left.keys())
            rk = set(right.keys())

            # missing in right
            for k in lk - rk:
                if max_diffs is not None and len(out) >= max_diffs:
                    return

                out.append(
                    {
                        "path": f"{path}.{k}",
                        "reason": "missing_in_right",
                        "left": left[k],
                        "right": None,
                    }
                )

            # missing in left
            for k in rk - lk:
                if max_diffs is not None and len(out) >= max_diffs:
                    return

                out.append(
                    {
                        "path": f"{path}.{k}",
                        "reason": "missing_in_left",
                        "left": None,
                        "right": right[k],
                    }
                )

            # recurse
            for k in lk & rk:
                self._diff(
                    left[k],
                    right[k],
                    path=f"{path}.{k}",
                    out=out,
                    max_diffs=max_diffs,
                )

            return

        # list
        if isinstance(left, list):
            if len(left) != len(right):
                out.append(
                    {
                        "path": path,
                        "reason": "length_mismatch",
                        "left": len(left),
                        "right": len(right),
                    }
                )
                return

            for i, (l, r) in enumerate(zip(left, right, strict=False)):
                self._diff(
                    l,
                    r,
                    path=f"{path}[{i}]",
                    out=out,
                    max_diffs=max_diffs,
                )

            return

        # value
        if left != right:
            out.append(
                {
                    "path": path,
                    "reason": "value_mismatch",
                    "left": left,
                    "right": right,
                }
            )
