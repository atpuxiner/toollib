import warnings
from typing import Type, Any, get_origin

from toollib.utils import VFrom, VConvert


def parse_variable(
        k: str,
        v_type: Type[Any],
        v_from: VFrom,
        v_convert: VConvert = None,
        default: Any = None,
        sep: str = ",",
        kv_sep: str = ":",
        ignore_unsupported_type: bool = True,
        raise_on_error: bool = False,
):
    """
    解析变量

    e.g.::

        value = utils.parse_variable(k="name", v_type=str, v_from=os.environ)

        +++++[更多详见参数或源码]+++++

    :param k: 键
    :param v_type: 值类型
    :param v_from: 值来源
    :param v_convert: 值转换
    :param default: 默认值
    :param sep: 分隔符，针对list、tuple、set、dict
    :param kv_sep: 键值分隔符，针对dict
    :param ignore_unsupported_type: 忽略不支持的类型（直接返回）
    :param raise_on_error: 遇错抛异常
    :return: 转换后的值
    """
    try:
        if k not in v_from:
            return default

        v = v_from.get(k)
        if v is None:
            return default
        if callable(v_convert):
            return v_convert(v)

        v_type = get_origin(v_type) or v_type
        if not isinstance(v_type, type):
            errmsg = f"Unsupported type annotation for {k!r}: {v_type!r}"
            if ignore_unsupported_type:
                warnings.warn(
                    message=errmsg,
                    category=RuntimeWarning,
                    stacklevel=2,
                )
                return v
            raise ValueError(errmsg)
        if isinstance(v, v_type):
            return v

        if isinstance(v, str):
            v = v.strip()
            if v_type is bool:
                res = {"true": True, "false": False}.get(v.lower())
                if res is None:
                    raise ValueError(
                        f"Cannot convert string to bool for {k!r}: {v!r}, "
                        f"supported values (case-insensitive): 'true', 'false'"
                    )
                return res
            elif v_type is int:
                if '.' in v:
                    f = float(v)
                    if not f.is_integer():
                        raise ValueError(f"Cannot convert non-integer float string to int for {k!r}: {v!r}")
                    return int(f)
                return int(v)
            elif v_type is float:
                return v_type(v)
            elif v_type in (list, tuple, set):
                return v_type([vv for v in v.split(sep) if (vv := v.strip())])
            elif v_type is dict:
                return {
                    (parts := item.strip().split(kv_sep, 1))[0].strip():
                        parts[1].strip() if len(parts) > 1 else None
                    for item in v.split(sep)
                    if item.strip()
                }
        return v_type(v)
    except (
            AttributeError,
            ValueError,
            TypeError,
            Exception,
    ) as e:
        if raise_on_error:
            raise
        warnings.warn(
            message=f"Failed to parse {k!r}: {e}",
            category=RuntimeWarning,
            stacklevel=2,
        )
    return default
