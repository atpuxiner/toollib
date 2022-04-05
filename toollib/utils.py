"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:20
@abstract 实用工具
@description
@history
"""
import os
import stat
import subprocess
import tarfile
import traceback
from datetime import datetime
import typing as t
from json import dumps, loads
from pathlib import Path
from threading import Lock

from toollib.common import rarfile, zipfile
from toollib.validator import choicer

__all__ = [
    'Singleton',
    'Chars',
    'now2str',
    'str2datetime',
    'json',
    'listfile',
    'decompress',
    'home',
    'syscmd',
]


class Singleton(type):
    """
    单例模式
    使用示例：
        # 比如使类A为单例模式
        class A(metaclass=utils.Singleton):
            pass
        # res: 得到一个单例类A
    """

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


class Chars:
    """
    字符
    使用示例：
        # 比如获取小写字母
        low_cases = utils.Chars.lowercases
        # res: 返回指定的字符
        +++++[更多详见参数或源码]+++++
    """
    lowercases = 'abcdefghijklmnopqrstuvwxyz'
    uppercases = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    punctuation = r"""~`!@#$%^&*()_-+={[}]|\:;"'<,>.?/"""
    whitespace = ' \t\n\r\v\f'


def now2str(fmt: str = 'S') -> str:
    """
    now datetime to str (获取当前时间的字符串)
    使用示例：
        # 比如获取当前时间
        now = utils.now2str()
        # 比如获取当前日期
        now_year = utils.now2str(fmt='d')  # 或者 fmt='%Y-%m-%d'
        # res: 返回指定格式时间的字符串
        +++++[更多详见参数或源码]+++++
    :param fmt:
    :return:
    """
    _ = {
        'S': '%Y-%m-%d %H:%M:%S',
        'M': '%Y-%m-%d %H:%M',
        'H': '%Y-%m-%d %H',
        'd': '%Y-%m-%d',
        'm': '%Y-%m',
        'Y': '%Y'
    }
    fmt = _.get(fmt, fmt)
    str_now = datetime.now().strftime(fmt)
    return str_now


def str2datetime(time_str: str, fmt: str = None) -> datetime:
    """
    时间字符串转换成日期（默认自动识别 fmt）
    使用示例：
        time_str = '2021-12-12'
        date = utils.str2datetime(time_str)
        # res: datetime.datetime(2021, 12, 12, 0, 0)
        +++++[更多详见参数或源码]+++++
    :param time_str: 时间字符串
    :param fmt: 格式化
    :return:
    """
    _ = {
        19: '%Y-%m-%d %H:%M:%S',
        16: '%Y-%m-%d %H:%M',
        13: '%Y-%m-%d %H',
        10: '%Y-%m-%d',
        7: '%Y-%m',
        4: '%Y'
    }
    fmt = fmt if fmt else _.get(len(time_str))
    dt = datetime.strptime(time_str, fmt)
    return dt


def json(data, mode='loads', default=None, *args, **kwargs):
    """
    json loads or dumps
    使用示例：
        data = {'name': 'x', age: 20}
        data_json = utils.json(data, mode='dumps')
        # res: (一个json)
        +++++[更多详见参数或源码]+++++
    :param data:
    :param mode: loads or dumps
    :param default: 默认值（如果入参data为空，优先返回给定的默认值）
    :param args:
    :param kwargs:
    :return:
    """
    mode = choicer(mode, choices=['loads', 'dumps'], lable='mode')
    if not data:
        data = default or data
    else:
        if mode == 'loads':
            data = loads(data, *args, **kwargs)
        else:
            data = dumps(data, *args, **kwargs)
    return data


def listfile(src_dir: t.Union[str, Path], pattern: str = '*',
             is_str: bool = False, is_name: bool = False, is_r: bool = False) -> t.Generator:
    """
    文件列表
    使用示例：
        # 比如获取某目录下的.py文件
        src_dir = 'D:/tmp'
        flist = utils.listfile(src_dir, pattern='*.py')
        # res: 输出匹配的文件路径生成器
        +++++[更多详见参数或源码]+++++
    :param src_dir: 源目录
    :param pattern: 匹配模式
    :param is_str: 是否返回字符串（True: 若为路径返回字符串，False: 若为路径返回Path类型）
    :param is_name: 是否获取文件名（True: 返回文件路径，False: 返回文件名）
    :param is_r: 是否递规查找
    :return:
    """
    src_dir = Path(src_dir).absolute()
    src_files = src_dir.rglob(pattern) if is_r is True else src_dir.glob(pattern)
    count = 0
    for f in src_files:
        if f.is_file():
            count += 1
            if is_name is True:
                yield f.name
            else:
                if is_str is True:
                    yield f.as_posix()
                else:
                    yield f
    else:
        if count == 0:
            yield


def decompress(src: t.Union[str, Path], dest_dir: t.Union[str, Path] = None,
               pattern: str = '*[.pzr2]', is_r: bool = False, is_raise: bool = True) -> int:
    """
    解压文件
    使用示例：
        # 比如解压某目录下的.zip文件
        src = 'D:/tmp'
        count = utils.decompress(src, pattern='*.zip')
        # res: 解压数量
        +++++[更多详见参数或源码]+++++
    :param src: 源目录或文件
    :param dest_dir: 目标目录
    :param pattern: 匹配模式（当src为目录时生效，默认匹配所有支持的压缩包）
    :param is_r: 是否递规查找（当src为目录时生效）
    :param is_raise: 是否抛异常
    :return: count（解压数量）
    """
    __support_types = [
        '.zip',
        '.rar',
        '.tar',
        '.gz', '.tgz',
        '.xz', '.txz',
        '.bz2', '.tbz', '.tbz2', '.tb2',
    ]
    src = Path(src).absolute()
    src_is_dir = False
    if src.is_dir():
        src_is_dir = True
        src_files = listfile(src, pattern=pattern, is_r=is_r)
    else:
        if src.suffix not in __support_types:
            raise ValueError('only supported: %s' % __support_types)
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
            if file_type == '.zip':
                zip_file = zipfile.ZipFile(src_file)
                for f in zip_file.namelist():
                    zip_file.extract(f, dest_dir)
                zip_file.close()
            elif file_type == '.rar':
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


def home():
    """
    家目录
    使用示例：
        h = utils.home()
        # res: 返回家目录的路径
        +++++[更多详见参数或源码]+++++
    :return:
    """
    return os.environ.get("HOME") or os.path.join(os.environ.get("HOMEDRIVE"), os.environ.get("HOMEPATH"))


def syscmd(cmd, shell=True, env=None, *args, **kwargs) -> subprocess.Popen:
    """
    系统命令（基于subprocess.Popen，具体参数见源）
    使用示例：
        # 比如获取当前路径（linux）
        utils.syscmd('pwd')
        # res: 返回 subprocess.Popen
        +++++[更多详见参数或源码]+++++
    :param cmd:
    :param shell:
    :param env:
    :param args:
    :param kwargs:
    :return:
    """
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        shell=shell, env=env, *args, **kwargs)
    return p
