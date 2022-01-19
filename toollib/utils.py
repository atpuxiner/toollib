"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:20
@abstract
@description
@history
"""
import stat
import tarfile
import traceback
from datetime import datetime
import typing as t
from json import dumps, loads
from pathlib import Path
from threading import Lock

from .common import rarfile, zipfile

__all__ = [
    "Singleton",
    "now2str",
    "str2datetime",
    "json",
    "get_files",
    "decompress",
]


class Singleton(type):
    """单例模式"""

    __instance_lock = Lock()

    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super(Singleton, cls).__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            with cls.__instance_lock:
                if cls.__instance is None:
                    cls.__instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__instance


def now2str(fmt: str = "S") -> str:
    """
    now datetime to str
    :param fmt:
    :return:
    """
    _ = {
        "S": "%Y-%m-%d %H:%M:%S",
        "M": "%Y-%m-%d %H:%M",
        "H": "%Y-%m-%d %H",
        "d": "%Y-%m-%d",
        "m": "%Y-%m",
        "Y": "%Y"
    }
    fmt = _.get(fmt, fmt)
    str_now = datetime.now().strftime(fmt)
    return str_now


def str2datetime(time_str: str, fmt: str = None) -> datetime:
    """
    convert str datetime to datetime
    :param time_str:
    :param fmt:
    :return:
    """
    _ = {
        19: "%Y-%m-%d %H:%M:%S",
        16: "%Y-%m-%d %H:%M",
        13: "%Y-%m-%d %H",
        10: "%Y-%m-%d",
        7: "%Y-%m",
        4: "%Y"
    }
    fmt = fmt if fmt else _.get(len(time_str))
    dt = datetime.strptime(time_str, fmt)
    return dt


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


def get_files(src_dir: t.Union[str, Path], pattern: str = "*",
              is_name: bool = False, is_r: bool = False) -> list:
    """
    获取文件
    :param src_dir: 源目录
    :param pattern: 匹配模式
    :param is_name: 是否获取文件名（True: 获取文件路径，False: 获取文件名）
    :param is_r: 是否递规查找
    :return:
    """
    files = []
    src_dir = Path(src_dir).absolute()
    src_files = src_dir.rglob(pattern) if is_r is True else src_dir.glob(pattern)
    for f in src_files:
        if f.is_file():
            files.append(f.name if is_name is True else f)
    return files


def decompress(src: t.Union[str, Path], dest_dir: t.Union[str, Path] = None,
               pattern: str = "*[.pzr]", is_r: bool = False, is_raise: bool = True) -> int:
    """
    解压文件
    :param src: 源目录或文件
    :param dest_dir: 目标目录
    :param pattern: 匹配模式（当src为目录时生效）
    :param is_r: 是否递规查找（当src为目录时生效）
    :param is_raise: 是否抛异常
    :return: count-解压数量
    """
    __support_types = [".zip", ".rar", ".tar", ".gz", ".tgz"]
    src = Path(src).absolute()
    src_is_dir = False
    if src.is_dir():
        src_is_dir = True
        src_files = get_files(src, pattern=pattern, is_r=is_r)
    else:
        if src.suffix not in __support_types:
            raise ValueError(f"only supported: {__support_types}")
        src_files = [src]
    if not dest_dir:
        dest_dir = src.absolute() if src_is_dir else src.absolute().parent
    else:
        dest_dir = Path(dest_dir).absolute()
        dest_dir.mkdir(parents=True, exist_ok=True)
    dest_dir.chmod(stat.S_IRWXU)
    count = 0
    for src_file in src_files:
        file_name, file_type = src_file.name, src_file.suffix
        if file_type:
            file_type = file_type.lower()
            if file_type not in __support_types:
                continue
        else:
            continue
        try:
            if file_type == ".zip":
                zip_file = zipfile.ZipFile(src_file)
                for f in zip_file.namelist():
                    zip_file.extract(f, dest_dir)
                zip_file.close()
            elif file_type == ".rar":
                rar_file = rarfile.RarFile(src_file)
                rar_file.extractall(dest_dir)
                rar_file.close()
            else:
                tar_file = tarfile.open(src_file)
                for name in tar_file.getnames():
                    tar_file.extract(name, dest_dir)
                tar_file.close()
        except:
            if is_raise is True:
                raise
            else:
                traceback.print_exc()
        else:
            count += 1
    return count
