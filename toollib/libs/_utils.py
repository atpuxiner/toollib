"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:20
@abstract
@description
@history
"""
import typing as t
from json import dumps, loads
from pathlib import Path


class ToolUtils(object):
    """utils"""

    @staticmethod
    def json(data, loadordumps="loads", default=None, *args, **kwargs):
        """
        json loads or dumps
        :param data:
        :param loadordumps:
        :param default:
        :param args:
        :param kwargs:
        :return:
        """
        if not data:
            data = default or data
        else:
            if loadordumps == "loads":
                data = loads(data, *args, **kwargs)
            elif loadordumps == "dumps":
                data = dumps(data, *args, **kwargs)
            else:
                raise ValueError("Only select from: [loads, dumps]")
        return data

    @staticmethod
    def get_files(src_dir: t.Union[str, Path], pattern: str = "*",
                  is_name: bool = False, is_r: bool = False) -> list:
        """
        获取文件
        :param src_dir:
        :param pattern:
        :param is_name:
        :param is_r:
        :return:
        """
        files = []
        src_dir = Path(src_dir)
        src_files = src_dir.rglob(pattern) if is_r is True else src_dir.glob(pattern)
        for f in src_files:
            if f.is_file():
                files.append(f.name if is_name is True else f)
        return files
