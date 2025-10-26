"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:20
@abstract 实用工具
@description
@history
"""
import importlib
from typing import TYPE_CHECKING

__all__ = [
    'Singleton',
    'Chars',
    'now2timestr',
    'timestr2time',
    'now2timestamp',
    'timestamp2time',
    'timerange',
    'home',
    'sysname',
    'RedirectStd12ToNull',
    "VersionCmper",
    'listfile',
    'decompress',
    'writetemp',
    'gen_leveldirs',
    'map_jsontype',
    'pkg_lver',
    'localip',
    'get_cls_attrs',
    'parse_variable',
    'copytree',
]

if TYPE_CHECKING:
    from toollib.utils._Singleton import Singleton
    from toollib.utils._Chars import Chars
    from toollib.utils._now2timestr import now2timestr
    from toollib.utils._timestr2time import timestr2time
    from toollib.utils._now2timestamp import now2timestamp
    from toollib.utils._timestamp2time import timestamp2time
    from toollib.utils._timerange import timerange
    from toollib.utils._home import home
    from toollib.utils._sysname import sysname
    from toollib.utils._RedirectStd12ToNull import RedirectStd12ToNull
    from toollib.utils._VersionCmper import VersionCmper
    from toollib.utils._listfile import listfile
    from toollib.utils._decompress import decompress
    from toollib.utils._writetemp import writetemp
    from toollib.utils._gen_leveldirs import gen_leveldirs
    from toollib.utils._map_jsontype import map_jsontype
    from toollib.utils._pkg_lver import pkg_lver
    from toollib.utils._localip import localip
    from toollib.utils._get_cls_attrs import get_cls_attrs
    from toollib.utils._parse_variable import parse_variable
    from toollib.utils._copytree import copytree


def __getattr__(name):
    if name in __all__:
        module = importlib.import_module(f"toollib.utils._{name}")
        return getattr(module, name)
    raise AttributeError(f"ImportError: cannot import name '{name}' from 'toollib.utils'")
