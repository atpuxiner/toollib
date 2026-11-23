import json
from datetime import date, datetime
from decimal import Decimal
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Literal, NewType, TypeVar

import pytest

from toollib.utils import ConfModel, parse_variable


class Color(Enum):
    RED = "red"


UserId = NewType("UserId", int)


def source(value, key="K"):
    return {key: value}


@pytest.mark.parametrize(
    ("annotation", "raw", "expected"),
    [
        (str, "abc", "abc"),
        (int, "12", 12),
        (int, "1.0", 1),
        (float, "1.5", 1.5),
        (bool, "true", True),
        (bool, "0", False),
        (bool, "YES", True),
        (bool, "off", False),
        (int, True, 1),
        (float, True, 1.0),
    ],
)
def test_scalar(annotation, raw, expected):
    assert parse_variable("K", annotation, source(raw)) == expected


@pytest.mark.parametrize(
    ("annotation", "raw", "expected"),
    [
        (list, ["a", 1], ["a", 1]),
        (list[str], ["a", "b"], ["a", "b"]),
        (dict, {"k": "v"}, {"k": "v"}),
        (dict[str, int], {"k": 1, "n": "2"}, {"k": 1, "n": 2}),
        (tuple[str, int], ["a", "2"], ("a", 2)),
        (tuple[int, ...], [1, "2"], (1, 2)),
        (tuple, [1, 2], (1, 2)),
        (set[str], ["a", "b"], {"a", "b"}),
        (frozenset[int], [1, "2"], frozenset({1, 2})),
    ],
)
def test_container_from_json(annotation, raw, expected):
    assert parse_variable("K", annotation, source(json.dumps(raw))) == expected


@pytest.mark.parametrize(
    ("annotation", "raw", "expected"),
    [
        (dict[str, list[int]], {"a": [1, "2"]}, {"a": [1, 2]}),
        (dict[str, list[dict[str, int]]], {"g": [{"n": 1, "m": "2"}]}, {"g": [{"n": 1, "m": 2}]}),
        (list[list[int]], [[1, "2"], [3]], [[1, 2], [3]]),
        (list[tuple[str, int]], [["a", "1"]], [("a", 1)]),
        (dict[str, set[int]], {"s": [1, "2", 2]}, {"s": {1, 2}}),
        (set[tuple[int, int]], [[1, "2"]], {(1, 2)}),
        (tuple[list[int], dict[str, str]], [[1, "2"], {"k": "v"}], ([1, 2], {"k": "v"})),
        (list[int | None], [1, None], [1, None]),
        (dict[str, frozenset[int]], {"k": [1, "2"]}, {"k": frozenset({1, 2})}),
    ],
)
def test_nested(annotation, raw, expected):
    assert parse_variable("K", annotation, source(json.dumps(raw))) == expected


@pytest.mark.parametrize(
    ("annotation", "raw", "expected"),
    [
        (int | None, "12", 12),
        (int | str, "1", "1"),
        (str | int, "1", "1"),
        (int | float, "2", 2),
        (int | float, 2.0, 2.0),
        (int | bool, True, True),
        (list[int | None], [1, None], [1, None]),
    ],
)
def test_union(annotation, raw, expected):
    assert parse_variable("K", annotation, source(raw)) == expected


def test_literal():
    assert parse_variable("K", Literal[1, 2], source("1")) == 1
    assert parse_variable("K", Literal["a", "b"], source("a")) == "a"
    with pytest.raises(ValueError):
        parse_variable("K", Literal[1, 2], source(True))
    with pytest.raises(ValueError):
        parse_variable("K", Literal[1, 2], source("3"))


def test_annotated_and_newtype():
    assert parse_variable("K", Annotated[int, "meta"], source("1")) == 1
    assert parse_variable("K", Annotated[list[int], "meta"], source(json.dumps([1, "2"]))) == [1, 2]
    assert parse_variable("K", UserId, source("1")) == 1
    assert parse_variable("K", list[UserId], source(json.dumps([1, "2"]))) == [1, 2]
    assert parse_variable("K", list[Annotated[int, [1, 2]]], source(json.dumps([1, "2"]))) == [1, 2]


def test_abc_containers():
    assert parse_variable("K", Sequence[int], source(json.dumps([1, "2"]))) == [1, 2]
    assert parse_variable("K", Mapping[str, int], source(json.dumps({"k": "1"}))) == {"k": 1}


@pytest.mark.parametrize(
    ("annotation", "raw", "expected"),
    [
        (bytes, "abc", b"abc"),
        (bytes, "123", b"123"),
        (bytes, json.dumps([65, 66]), b"AB"),
        (bytearray, "abc", bytearray(b"abc")),
        (Decimal, "1.2", Decimal("1.2")),
        (Path, "/tmp/x", Path("/tmp/x")),
        (date, "2026-01-01", date(2026, 1, 1)),
        (datetime, "2026-01-01T00:00:00", datetime(2026, 1, 1)),
        (Color, "red", Color.RED),
        (Color, "RED", Color.RED),
        (Any, {"a": "1"}, {"a": "1"}),
        (Any, [1, 2], [1, 2]),
    ],
)
def test_special_types(annotation, raw, expected):
    assert parse_variable("K", annotation, source(raw)) == expected


def test_native_source_and_defaults():
    assert parse_variable("K", dict[str, int], {"K": {"k": "3"}}) == {"k": 3}
    assert parse_variable("MISSING", int, {}, default=7) == 7
    assert parse_variable("K", int, {"K": None}, default=7) == 7


def test_converter_shortcut():
    assert parse_variable("K", list[int], source('["1"]'), v_converter=lambda v: v) == '["1"]'


@pytest.mark.parametrize(
    ("annotation", "raw"),
    [
        (dict[str, int], json.dumps({"k": "bad"})),
        (tuple[str, int], json.dumps(["a", "2", "3"])),
        (list[int], json.dumps(["x"])),
        (list[str], json.dumps([1])),
        (Literal[1, 2], "3"),
        (Color, "blue"),
        (date, "not-a-date"),
    ],
)
def test_parse_errors_raise(annotation, raw):
    with pytest.raises(ValueError):
        parse_variable("K", annotation, source(raw))


def test_arbitrary_types_allowed():
    t = TypeVar("T")
    with pytest.raises(ValueError):
        parse_variable("K", t, source("a"))
    assert parse_variable("K", t, source("a"), arbitrary_types_allowed=True) == "a"


def test_conf_model_raises_on_error():
    class Config(ConfModel):
        MY_DICT: dict[str, int]

    config = Config(v_from={"MY_DICT": {"k": "2"}})
    assert config.MY_DICT == {"k": 2}
    with pytest.raises(ValueError):
        Config(v_from={"MY_DICT": {"k": "bad"}})
