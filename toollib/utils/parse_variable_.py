from typing import Callable, Any, Protocol


class VFrom(Protocol):
    def get(self, key: Any, default: Any = None) -> Any:
        ...


class VConvert(Protocol):
    def __call__(self, value: Any) -> Any:
        ...


def parse_variable(
        k: str,
        v_type: Callable,
        v_from: VFrom,
        v_convert: VConvert = None,
        default: Any = None,
        is_raise: bool = False,
        sep: str = ",",
        kv_sep: str = ":",
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
    :param is_raise: 是否raise
    :param sep: 分隔符，针对list、tuple、set、dict
    :param kv_sep: 键值分隔符，针对dict
    :return: 转换后的值
    """
    v = v_from.get(k)
    if v is None or v == "":
        return default
    try:
        if callable(v_convert):
            return v_convert(v)
        if type(v) == v_type:
            return v
        v_type_name = v_type.__name__
        if v_type_name == "bool":
            return {"true": True, "false": False}.get(v.lower(), bool(v))
        elif v_type_name in ("int", "float"):
            return v_type(v)
        elif v_type_name in ("list", "tuple", "set"):
            return v_type([vv for v in v.split(sep) if (vv := v.strip())])
        elif v_type_name == "dict":
            return {kk.strip(): vv.strip() if kv_sep in item else None for item in v.split(sep)
                    for kk, vv in ((item, None) if kv_sep not in item else item.split(kv_sep, 1),)}
        else:
            return v_type(v)
    except (
            AttributeError,
            ValueError,
            TypeError,
            Exception,
    ):
        if is_raise:
            raise
    return default
