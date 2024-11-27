"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:20
@abstract 实用工具
@description
@history
"""
import os
import platform
import re
import stat
import subprocess
import tarfile
import tempfile
import traceback
from datetime import datetime, timezone
import typing as t
from json import dumps, loads
from pathlib import Path
from threading import Lock
from zoneinfo import ZoneInfo

from toollib.common import rarfile, zipfile

__all__ = [
    'Singleton',
    'Chars',
    'now2timestamp',
    'timestamp2time',
    'now2timestr',
    'timestr2time',
    'get_time_range',
    'home',
    'sysname',
    'RedirectStd12ToNull',
    "VersionCmper",
    'json',
    'read_by_block',
    'gen_tmp_file',
    'listfile',
    'decompress',
]


class Singleton(type):
    """
    单例模式

    e.g.::

        # 比如使类A为单例模式
        class A(metaclass=utils.Singleton):
            pass

        +++++[更多详见参数或源码]+++++
    """

    _instances = {}
    _locks = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            if cls not in cls._locks:
                cls._locks[cls] = Lock()
            with cls._locks[cls]:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Chars:
    """
    字符

    e.g.::

        # 比如获取小写字母
        low_cases = utils.Chars.lowercases

        +++++[更多详见参数或源码]+++++
    """
    lowercases = 'abcdefghijklmnopqrstuvwxyz'
    uppercases = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    punctuation = r"""~`!@#$%^&*()_-+={[}]|\:;"'<,>.?/"""
    whitespace = ' \t\n\r\v\f'


def now2timestamp(
        fmt: t.Literal['s', 'ms', 'us'] = "ms",
        tz_str: str = "Asia/Shanghai",
) -> int:
    """
    获取当前时间的时间戳

    e.g.::

        timestamp = utils.now2timestamp()

        +++++[更多详见参数或源码]+++++

    :param fmt: 格式化（s-秒，ms-毫秒，us-微秒）
    :param tz_str: 时区字符串
    :return:
    """
    tz = ZoneInfo(tz_str)
    now_timestamp_tz = datetime.utcnow().timestamp() + tz.utcoffset(datetime.now().astimezone(tz)).total_seconds()
    timestamp_fmts = {"s": 1, "ms": 1000, "us": 1000000}
    return int(now_timestamp_tz * timestamp_fmts.get(fmt, 1000))


def timestamp2time(
        timestamp: int,
        fmt: t.Optional[str] = "%Y-%m-%d %H:%M:%S",
        tz_str="Asia/Shanghai",
) -> t.Union[str, datetime]:
    """
    时间戳转换为时间对象或时间字符串

    e.g.::

        timestamp = utils.timestamp2time()

        +++++[更多详见参数或源码]+++++

    :param timestamp: 时间戳
    :param fmt: 格式化，空则返回时间对象
    :param tz_str: 时区字符串
    :return:
    """
    if len(str(timestamp)) > 10:
        timestamp = timestamp / 1000.0
    time_tz = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc).astimezone(ZoneInfo(tz_str))
    if fmt:
        return time_tz.strftime(fmt)
    return time_tz


def now2timestr(
        fmt: str = 'S',
        tz_str="Asia/Shanghai",
) -> str:
    """
    获取当前时间的字符串

    e.g.::

        # 比如获取当前时间
        now = utils.now2str()

        # 比如获取当前日期
        now_year = utils.now2str(fmt='d')  # 或者 fmt='%Y-%m-%d'

        +++++[更多详见参数或源码]+++++

    :param fmt: 格式化
    :param tz_str: 时区字符串
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
    return datetime.now(timezone.utc).astimezone(ZoneInfo(tz_str)).strftime(_.get(fmt, fmt))


def timestr2time(
        time_str: str,
        fmt: str = None,
) -> datetime:
    """
    时间字符串转换为时间对象（默认自动识别 fmt）

    e.g.::

        time_str = '2021-12-12'
        date = utils.str2datetime(time_str)

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
    return datetime.strptime(time_str, fmt)


def get_time_range(
        start_timestr: str,
        end_timestr: str = None,
        result_type: str = "datetime",
        timestr_fmt: str = "%Y-%m-%d %H:%M:%S",
        timestamp_fmt: t.Literal['s', 'ms', 'us'] = "ms",
) -> tuple:
    """
        获取时间范围

        e.g.::

            start_timestr = '2021-12-12'
            date = utils.get_time_range(start_timestr)

            +++++[更多详见参数或源码]+++++

        :param start_timestr: 开始时间字符串
        :param end_timestr: 结束时间字符串
        :param result_type: 结果类型：(datetime: 时间对象，timestr: 时间字符串，timestamp: 时间戳)
        :param timestr_fmt: 时间字符串格式
        :param timestamp_fmt: 时间戳格式（s-秒，ms-毫秒，us-微秒）
        :return:
        """
    start_time = timestr2time(start_timestr)
    end_time = timestr2time(end_timestr or start_timestr)
    if not end_timestr or len(end_timestr) == 10:
        end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)
    if result_type == "timestr":
        return (
            start_time.strftime(timestr_fmt),
            end_time.strftime(timestr_fmt)
        )
    elif result_type == "timestamp":
        timestamp_fmts = {"s": 1, "ms": 1000, "us": 1000000}
        return (
            int(start_time.timestamp() * timestamp_fmts.get(timestamp_fmt, 1000)),
            int(end_time.timestamp() * timestamp_fmts.get(timestamp_fmt, 1000))
        )
    return (
        start_time,
        end_time
    )


def home() -> str:
    """
    家目录

    e.g.::

        h = utils.home()

        +++++[更多详见参数或源码]+++++
    """
    return os.environ.get("HOME") or os.path.join(os.environ.get("HOMEDRIVE"), os.environ.get("HOMEPATH"))


def sysname() -> str:
    """
    系统名称

    e.g.::

        s = utils.sysname()

        +++++[更多详见参数或源码]+++++
    """
    name = platform.uname().system
    if name == 'Linux':
        try:
            result = subprocess.run(
                'cat /etc/*-release',
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                encoding='utf8',
                shell=True,
            )
            r = re.search(r'[\n\s]+ID=(.*?)[\n\s]+', result.stdout)
            name = r.group(1) if r else name
        except Exception:
            pass
    elif name == 'Darwin':
        name = 'macOS'
    return name.lower().replace(' ', '')


class RedirectStd12ToNull:
    """
    重定向标准输出错误到null

    e.g.::

        with RedirectStd12ToNull():
            # 你要重定向的代码块

        # 另：取消stderr的重定向
        with RedirectStd12ToNull(is_stderr=False):
            # 你要重定向的代码块

        +++++[更多详见参数或源码]+++++
    """

    def __init__(self, is_stderr: bool = True):
        """
        初始化
        :param is_stderr: 是否重定向stderr
        """
        self.is_stderr = is_stderr
        self.null_1fd = os.open(os.devnull, os.O_RDWR)
        self.save_1fd = os.dup(1)
        if self.is_stderr is True:
            self.null_2fd = os.open(os.devnull, os.O_RDWR)
            self.save_2fd = os.dup(2)

    def __enter__(self):
        os.dup2(self.null_1fd, 1)
        if self.is_stderr is True:
            os.dup2(self.null_2fd, 2)

    def __exit__(self, *_):
        os.dup2(self.save_1fd, 1)
        os.close(self.null_1fd)
        if self.is_stderr is True:
            os.dup2(self.save_2fd, 2)
            os.close(self.null_2fd)


class VersionCmper:
    """
    版本比较

    e.g.::

        from toollib.utils import VersionCmper

        ver1 = VersionCmper("1.0.1")
        ver2 = VersionCmper("1.0.2")
        print(ver1 > ver2)  # Out: False

        +++++[更多详见参数或源码]+++++
    """

    def __init__(self, version: str, is_strgtnum: bool = True):
        """
        版本比较
        :param version: 版本号
        :param is_strgtnum: 是否字符串大于数字。比如：True: 1.0.a > 1.0.11
        """
        self.version = version
        self.is_strgtnum = is_strgtnum
        self.parts = self._split_version(version)

    @staticmethod
    def _split_version(version):
        parts = re.split(r'(\d+|[a-zA-Z]+)', version)
        return [int(part) if part.isdigit() else part for part in parts if part]

    def _compare_parts(self, other_parts):
        for part1, part2 in zip(self.parts, other_parts):
            if isinstance(part1, int) and isinstance(part2, int):
                if part1 != part2:
                    return (part1 > part2) - (part1 < part2)
            elif isinstance(part1, str) and isinstance(part2, str):
                if part1 != part2:
                    return (part1 > part2) - (part1 < part2)
            else:
                if self.is_strgtnum:
                    return 1 if isinstance(part1, str) else -1
                else:
                    return 1 if isinstance(part1, int) else -1
        return (len(self.parts) > len(other_parts)) - (len(self.parts) < len(other_parts))

    def __eq__(self, other):
        return self._compare_parts(other.parts) == 0

    def __lt__(self, other):
        return self._compare_parts(other.parts) < 0

    def __le__(self, other):
        return self._compare_parts(other.parts) <= 0

    def __gt__(self, other):
        return self._compare_parts(other.parts) > 0

    def __ge__(self, other):
        return self._compare_parts(other.parts) >= 0

    def __ne__(self, other):
        return self._compare_parts(other.parts) != 0


def json(data, is_dumps: bool = False, default=None, *args, **kwargs):
    """
    json loads or dumps

    e.g.::

        data = {'name': 'x', age: 20}
        data_json = utils.json(data, is_dumps=True)

        +++++[更多详见参数或源码]+++++

    :param data:
    :param is_dumps: 是否dumps，否则loads
    :param default: 默认值（如果入参data为空，优先返回给定的默认值）
    :param args:
    :param kwargs:
    :return:
    """
    if not data:
        return default or data
    if is_dumps is True:
        return dumps(data, *args, **kwargs)
    return loads(data, *args, **kwargs)


def read_by_block(file_path: str, block_size: int = 10240, mode: str = 'rb', **kwargs) -> t.Generator:
    """
    分块读取

    e.g.::

        data = utils.read_by_block('foo.txt')

        +++++[更多详见参数或源码]+++++

    :param file_path: 文件路径
    :param block_size: 块大小
    :param mode: 模式
    :param kwargs: open其他参数
    :return:
    """
    with open(file_path, mode=mode, **kwargs) as fp:
        while True:
            block = fp.read(block_size)
            if block:
                yield block
            else:
                break


def gen_tmp_file(file_data: t.Union[bytes, str], file_suffix: str, **kwargs) -> str:
    """
    生成临时文件

    e.g.::

        file_path = utils.gen_tmp_file(file_data)

        +++++[更多详见参数或源码]+++++

    :param file_data: 文件内容
    :param file_suffix: 文件后缀
    :param kwargs: kwargs
    :return:
    """
    with tempfile.NamedTemporaryFile(
            suffix=file_suffix,
            mode="w+b" if isinstance(file_data, bytes) else "w+",
            delete=False,
            **kwargs,
    ) as tmp_file:
        tmp_file.write(file_data)
        return tmp_file.name


def listfile(
        src: t.Union[str, Path],
        pattern: str = '*',
        is_str: bool = False,
        is_name: bool = False,
        is_r: bool = False,
) -> t.Generator:
    """
    文件列表

    e.g.::

        # 比如获取某目录下的.py文件
        src_dir = 'D:/tmp'
        flist = utils.listfile(src_dir, pattern='*.py')

        +++++[更多详见参数或源码]+++++

    :param src: 源目录
    :param pattern: 匹配模式
    :param is_str: 是否返回字符串（True: 若为路径返回字符串，False: 若为路径返回Path类型）
    :param is_name: 是否获取文件名（True: 返回文件路径，False: 返回文件名）
    :param is_r: 是否递规查找
    :return:
    """
    src_dir = Path(src).absolute()
    if not src_dir.is_dir():
        raise FileNotFoundError(f'{src} directory does not exist')
    src_files = src_dir.rglob(pattern) if is_r is True else src_dir.glob(pattern)
    for f in src_files:
        if f.is_file():
            if is_name is True:
                yield f.name
            else:
                if is_str is True:
                    yield f.as_posix()
                else:
                    yield f


def decompress(
        src: t.Union[str, Path],
        dst: t.Union[str, Path] = None,
        pattern: str = '*[.pzr2]',
        is_r: bool = False,
        is_raise: bool = True,
) -> int:
    """
    解压文件

    e.g.::

        # 比如解压某目录下的.zip文件
        src = 'D:/tmp'
        count = utils.decompress(src, pattern='*.zip')

        +++++[更多详见参数或源码]+++++

    :param src: 源目录或文件
    :param dst: 目标目录
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
    if not dst:
        dst_dir = src.absolute() if src_is_dir else src.absolute().parent
    else:
        dst_dir = Path(dst).absolute()
        dst_dir.mkdir(parents=True, exist_ok=True)
    dst_dir.chmod(stat.S_IRWXU)
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
                    zip_file.extract(f, dst_dir)
                zip_file.close()
            elif file_type == '.rar':
                rar_file = rarfile.RarFile(src_file)
                rar_file.extractall(dst_dir)
                rar_file.close()
            else:
                tar_file = tarfile.open(src_file)
                for name in tar_file.getnames():
                    tar_file.extract(name, dst_dir)
                tar_file.close()
        except:
            if is_raise is True:
                raise
            else:
                traceback.print_exc()
        else:
            count += 1
    return count
