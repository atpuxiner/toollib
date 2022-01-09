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
    """utils工具"""

    @staticmethod
    def json(data, loadordumps="loads", default=None, *args, **kwargs):
        """
        json loads or dumps
        :param data:
        :param loadordumps: loads or dumps
        :param default: 默认值（如果入参data为空，优先返回给定的默认值）
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
        :param src_dir: 源目录
        :param pattern: 匹配模式
        :param is_name: 是否获取文件名（True: 获取文件及路径，False: 获取文件名）
        :param is_r: 是否递规查找源目录及子目录所有的文件
        :return:
        """
        files = []
        src_dir = Path(src_dir).absolute()
        src_files = src_dir.rglob(pattern) if is_r is True else src_dir.glob(pattern)
        for f in src_files:
            if f.is_file():
                files.append(f.name if is_name is True else f)
        return files
