"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:20
@abstract 实用工具
@description
@history
"""
import importlib

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
]


def __getattr__(name):
    if name in __all__:
        module = importlib.import_module(f"toollib.utils.{name}_")
        return getattr(module, name)
    raise AttributeError(f"ImportError: cannot import name '{name}' from 'toollib.utils'")
