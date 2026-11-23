from collections.abc import (
    Callable,
    Iterable,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set as ABSSet,
)
from contextlib import suppress
from datetime import date, datetime, time
from enum import Enum
from functools import lru_cache
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin

from toollib.utils import VConverter, VFrom

try:
    import orjson as _json
except ImportError:
    import json as _json

_UNION_TYPES = (Union, UnionType)
_Converter = Callable[[Any, str], Any]
_CONTAINER_TYPES = {
    Sequence: list,
    MutableSequence: list,
    Iterable: list,
    ABSSet: set,
    MutableSet: set,
    Mapping: dict,
    MutableMapping: dict,
}
_BOOL_TRUE = {"true", "1", "yes", "on"}
_BOOL_FALSE = {"false", "0", "no", "off"}
_JSON_ORIGINS = (list, tuple, set, frozenset, dict)
_BYTES_ORIGINS = (bytes, bytearray)
_NUMERIC_ORIGINS = (int, float)
_MISSING = object()


def _unwrap(annotation: Any) -> Any:
    while hasattr(annotation, "__metadata__"):
        annotation = get_args(annotation)[0]
    while hasattr(annotation, "__supertype__"):
        annotation = annotation.__supertype__
    return annotation


def _resolve(annotation: Any) -> tuple[Any, tuple]:
    annotation = _unwrap(annotation)
    origin = get_origin(annotation) or annotation
    return _CONTAINER_TYPES.get(origin, origin), get_args(annotation)


def _bytes_converter(origin: type):
    def convert(value: Any, k: str) -> Any:
        if isinstance(value, str):
            return origin(value.encode())
        if isinstance(value, (list, tuple, set, frozenset)):
            return origin(value)
        raise ValueError(f"Cannot convert {value!r} to {origin.__name__} for {k!r}")

    return convert


def _iso_converter(origin: type):
    def convert(value: Any, k: str) -> Any:
        if not isinstance(value, str):
            raise ValueError(f"Cannot convert {value!r} to {origin.__name__} for {k!r}")
        if origin is datetime:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return origin.fromisoformat(value)

    return convert


def _normalize(annotation: Any) -> Any:
    annotation = _unwrap(annotation)
    args = get_args(annotation)
    if not args:
        return annotation
    origin = get_origin(annotation)
    if origin is None:
        return annotation
    args = tuple(_normalize(arg) for arg in args)
    if origin is UnionType:
        result = args[0]
        for arg in args[1:]:
            result |= arg
        return result
    try:
        return origin[args]
    except TypeError:
        return annotation


def _make_converter(annotation: Any) -> _Converter:
    """按注解编译转换器，避免逐元素重复调用 get_origin/get_args"""
    annotation = _unwrap(annotation)
    if annotation is Any:
        return lambda value, k: value

    raw_origin = get_origin(annotation) or annotation
    origin, args = _resolve(annotation)
    annotation_repr = repr(annotation)

    if origin is Literal:
        literal_values = args
        literal_converters = tuple(_converter_for(type(arg)) for arg in literal_values)

        def convert_literal(value: Any, k: str) -> Any:
            for arg in literal_values:
                if type(value) is type(arg) and value == arg:
                    return value
            for convert, arg in zip(literal_converters, literal_values, strict=True):
                if isinstance(value, bool) and type(arg) in (int, float):
                    continue
                try:
                    if convert(value, k) == arg:
                        return arg
                except (ValueError, TypeError):
                    continue
            raise ValueError(f"Expected one of {literal_values!r} for {k!r}, got {value!r}")

        return convert_literal

    if raw_origin in _UNION_TYPES:
        allows_none = type(None) in args
        candidates = [
            (_resolve(arg)[0], _converter_for(arg)) for arg in args if arg is not type(None)
        ]
        if len(candidates) == 1 and not allows_none:
            return candidates[0][1]

        def convert_union(value: Any, k: str) -> Any:
            if value is None and allows_none:
                return None
            for arg_origin, convert in candidates:
                if isinstance(arg_origin, type) and type(value) is arg_origin:
                    try:
                        return convert(value, k)
                    except (ValueError, TypeError):
                        continue
            for arg_origin, convert in candidates:
                if isinstance(arg_origin, type) and isinstance(value, arg_origin):
                    try:
                        return convert(value, k)
                    except (ValueError, TypeError):
                        continue
            for _, convert in candidates:
                try:
                    return convert(value, k)
                except (ValueError, TypeError):
                    continue
            raise ValueError(f"Cannot coerce {value!r} to {annotation_repr} for {k!r}")

        return convert_union

    if origin is dict:
        key_convert = _converter_for(args[0] if len(args) > 0 else Any)
        value_convert = _converter_for(args[1] if len(args) > 1 else Any)

        def convert_dict(value: Any, k: str) -> Any:
            if not isinstance(value, dict):
                raise ValueError(f"Expected a JSON object for {k!r}, got {value!r}")
            return {key_convert(key, k): value_convert(item, k) for key, item in value.items()}

        return convert_dict

    if origin is tuple:
        if len(args) == 2 and args[1] is Ellipsis:
            item_convert = _converter_for(args[0])

            def convert_variadic_tuple(value: Any, k: str) -> Any:
                if not isinstance(value, (list, tuple, set, frozenset)):
                    raise ValueError(f"Expected a JSON array for {k!r}, got {value!r}")
                return tuple(item_convert(item, k) for item in value)

            return convert_variadic_tuple
        if args:
            converters = tuple(_converter_for(arg) for arg in args)
            count = len(converters)

            def convert_fixed_tuple(value: Any, k: str) -> Any:
                if not isinstance(value, (list, tuple, set, frozenset)):
                    raise ValueError(f"Expected a JSON array for {k!r}, got {value!r}")
                if len(value) != count:
                    raise ValueError(f"Length mismatch for {k!r}: expected {count}, got {len(value)}")
                return tuple(convert(item, k) for item, convert in zip(value, converters, strict=True))

            return convert_fixed_tuple

        def convert_bare_tuple(value: Any, k: str) -> Any:
            if not isinstance(value, (list, tuple, set, frozenset)):
                raise ValueError(f"Expected a JSON array for {k!r}, got {value!r}")
            return tuple(value)

        return convert_bare_tuple

    if origin in (list, set, frozenset):
        container = origin
        item_convert = _converter_for(args[0] if args else Any)

        def convert_sequence(value: Any, k: str) -> Any:
            if not isinstance(value, (list, tuple, set, frozenset)):
                raise ValueError(f"Expected a JSON array for {k!r}, got {value!r}")
            return container(item_convert(item, k) for item in value)

        return convert_sequence

    if origin is bytes or origin is bytearray:
        special = _bytes_converter(origin)
    elif origin in (datetime, date, time):
        special = _iso_converter(origin)
    else:
        special = None
    is_enum = isinstance(origin, type) and issubclass(origin, Enum)
    numeric_origin = origin in (int, float)

    def convert_enum(value: Any, k: str) -> Any:
        try:
            return origin(value)
        except ValueError:
            try:
                return origin[value]
            except (KeyError, TypeError):
                raise ValueError(f"Invalid {annotation_repr} for {k!r}: {value!r}") from None

    def convert_scalar(value: Any, k: str) -> Any:
        if isinstance(value, origin) and not (isinstance(value, bool) and numeric_origin):
            return value
        if isinstance(value, bool) and numeric_origin:
            return origin(value)
        if value is None:
            raise ValueError(f"Unexpected null for {k!r}, expected {annotation_repr}")
        if special is not None:
            return special(value, k)
        if is_enum:
            return convert_enum(value, k)
        if origin is float and isinstance(value, int):
            return float(value)
        if origin is int and isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            s = value.strip()
            if origin is bool:
                low = s.lower()
                if low in _BOOL_TRUE:
                    return True
                if low in _BOOL_FALSE:
                    return False
                raise ValueError(
                    f"Cannot convert string to bool for {k!r}: {value!r}, "
                    f"supported values (case-insensitive): {sorted(_BOOL_TRUE | _BOOL_FALSE)}"
                )
            if origin is int:
                if "." in s:
                    f = float(s)
                    if not f.is_integer():
                        raise ValueError(f"Cannot convert non-integer float string to int for {k!r}: {value!r}")
                    return int(f)
                return int(s)
            if origin is float:
                return float(s)
        if origin is str:
            raise ValueError(f"Cannot coerce {value!r} to str for {k!r}")
        if isinstance(origin, type):
            try:
                return origin(value)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Cannot convert {value!r} to {annotation_repr} for {k!r}: {e}") from e
        raise ValueError(f"Cannot coerce {value!r} to {annotation_repr} for {k!r}")

    return convert_scalar


@lru_cache(maxsize=256)
def _cached_converter(annotation: Any) -> _Converter:
    return _make_converter(_normalize(annotation))


def _converter_for(annotation: Any) -> _Converter:
    try:
        return _cached_converter(annotation)
    except TypeError:
        return _make_converter(_normalize(annotation))


def _build_meta(annotation: Any):
    normalized = _normalize(annotation)
    origin, args = _resolve(normalized)
    return (
        normalized,
        origin,
        args,
        isinstance(origin, type) or origin in _UNION_TYPES or origin is Literal,
        origin in _JSON_ORIGINS,
        origin in _BYTES_ORIGINS,
        origin in _NUMERIC_ORIGINS,
        _make_converter(normalized),
    )


@lru_cache(maxsize=256)
def _cached_meta(annotation: Any):
    return _build_meta(annotation)


def _meta_for(annotation: Any):
    try:
        return _cached_meta(annotation)
    except TypeError:
        return _build_meta(annotation)


def parse_variable(
    k: str,
    v_type: type[Any],
    v_from: VFrom,
    v_converter: VConverter | None = None,
    default: Any = None,
    arbitrary_types_allowed: bool = False,
):
    """
    解析变量

    e.g.::

        value = utils.parse_variable(k="name", v_type=str, v_from=os.environ)

        # 注：
        #   - 安装 orjson 后自动加速 JSON 解码；它把超过 64 位的整数解析为 float（不装则回退标准库 json）
        #   - list/tuple/set/dict 按 JSON 字符串解析，并按元素类型注解转换（tuple、set 与 list 一样使用 JSON 数组）
        #       - MY_LIST='["a", "b", "c"]'          -> list[str]
        #       - MY_DICT='{"key1": 1, "key2": 2}'   -> dict[str, int]

        +++++[更多详见参数或源码]+++++

    :param k: 键
    :param v_type: 值类型（支持泛型、Optional/Union、Literal、Annotated、NewType 等注解）
    :param v_from: 值来源
    :param v_converter: 值转换
    :param default: 默认值
    :param arbitrary_types_allowed: 允许不支持的注解
    :return: 转换后的值
    """
    v = v_from.get(k, _MISSING)
    if v is _MISSING or v is None:
        return default
    if callable(v_converter):
        return v_converter(v)

    annotation, origin, args, supported, need_json, need_bytes_json, numeric, convert = _meta_for(v_type)
    if annotation is Any:
        return v
    if not supported:
        if arbitrary_types_allowed:
            if isinstance(v_type, type) and not isinstance(v, v_type):
                raise ValueError(f"Value {v!r} is not an instance of {v_type!r} for {k!r}")
            return v
        raise ValueError(f"Unsupported type annotation for {k!r}: {v_type!r}")
    if isinstance(origin, type) and isinstance(v, origin) and not args and not (numeric and isinstance(v, bool)):
        return v

    if isinstance(v, str):
        v = v.strip()
        if need_json:
            v = _json.loads(v)
        elif need_bytes_json and v.startswith("["):
            with suppress(ValueError):
                v = _json.loads(v)
    return convert(v, k)
