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
import socket
import stat
import subprocess
import tarfile
import tempfile
import traceback
import urllib.request as request
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
    'now2timestr',
    'timestr2time',
    'now2timestamp',
    'timestamp2time',
    'timerange',
    'home',
    'sysname',
    'RedirectStd12ToNull',
    "VersionCmper",
    'json',
    'readblock',
    'listfile',
    'decompress',
    'writetemp',
    'gen_leveldirs',
    'map_jsontype',
    'pkg_lver',
    'localip',
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
        lowercases = utils.Chars.lowercases

        +++++[更多详见参数或源码]+++++
    """
    lowercases = 'abcdefghijklmnopqrstuvwxyz'
    uppercases = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    punctuation = r"""~`!@#$%^&*()_-+={[}]|\:;"'<,>.?/"""
    whitespace = ' \t\n\r\v\f'


def now2timestr(
        fmt: str = "%Y-%m-%d %H:%M:%S",
        tzname="Asia/Shanghai",
) -> str:
    """
    获取当前时间字符串

    e.g.::

        now = utils.now2timestr()

        +++++[更多详见参数或源码]+++++

    :param fmt: 格式化
    :param tzname: 时区名称
    :return:
    """
    return datetime.now(timezone.utc).astimezone(ZoneInfo(tzname)).strftime(fmt)


def timestr2time(
        timestr: str,
        fmt: str = None,
        unit: t.Literal['fs', 's', 'ms', 'us', 'ns'] = None,
        tzname: str = None,
) -> t.Union[datetime, int, float]:
    """
    时间字符串转时间对象或时间戳(unit若存在)

    e.g.::

        dt = utils.timestr2time('2021-12-12')

        +++++[更多详见参数或源码]+++++

    :param timestr: 时间字符串
    :param fmt: 格式化
    :param unit: 单位（fs-浮点型秒, s-秒，ms-毫秒，us-微秒，ns-纳秒）
    :param tzname: 时区名称
    :return:
    """
    if "T" in timestr:
        timestr = timestr.replace("Z", "+00:00")
    if not fmt:
        dt = datetime.fromisoformat(timestr)
    else:
        dt = datetime.strptime(timestr, fmt)
    if unit:
        if tzname:
            dt = dt.replace(tzinfo=ZoneInfo(tzname))
        if unit == "fs":
            return dt.timestamp()
        return int(dt.timestamp() * {"s": 1, "ms": 1000, "us": 1000000, "ns": 1000000000}.get(unit, 1000))
    if tzname:
        return dt.astimezone(ZoneInfo(tzname))
    return dt


def now2timestamp(
        unit: t.Literal['fs', 's', 'ms', 'us', 'ns'] = "ms",
        tzname: str = "Asia/Shanghai",
) -> t.Union[int, float]:
    """
    获取当前时间戳

    e.g.::

        timestamp = utils.now2timestamp()

        +++++[更多详见参数或源码]+++++

    :param unit: 单位（fs-浮点型秒, s-秒，ms-毫秒，us-微秒，ns-纳秒）
    :param tzname: 时区名称
    :return:
    """
    zinfo = ZoneInfo(tzname)
    timestamp = datetime.utcnow().timestamp() + zinfo.utcoffset(datetime.now().astimezone(zinfo)).total_seconds()
    if unit == "fs":
        return timestamp
    return int(timestamp * {"s": 1, "ms": 1000, "us": 1000000, "ns": 1000000000}.get(unit, 1000))


def timestamp2time(
        timestamp: t.Union[int, float],
        unit: t.Literal['s', 'ms', 'us', 'ns'] = "ms",
        fmt: str = None,
        tzname: str = None,
) -> t.Union[datetime, str]:
    """
    时间戳转时间对象或时间字符串(fmt若存在)

    e.g.::

        dt = utils.timestamp2time()

        +++++[更多详见参数或源码]+++++

    :param timestamp: 时间戳
    :param unit: 单位（s-秒，ms-毫秒，us-微秒，ns-纳秒）
    :param fmt: 格式化
    :param tzname: 时区名称
    :return:
    """
    if unit == "ms":
        timestamp = timestamp / 1000.0
    elif unit == "s":
        pass
    elif unit == "us":
        timestamp = timestamp / 1000000.0
    elif unit == "ns":
        timestamp = timestamp / 1000000000.0
    dt = datetime.fromtimestamp(timestamp)
    if tzname:
        dt = dt.astimezone(ZoneInfo(tzname))
    if fmt:
        return dt.strftime(fmt)
    return dt


def timerange(
        start: str,
        end: str = None,
        fmt: str = None,
        unit: t.Literal['fs', 's', 'ms', 'us', 'ns'] = None,
) -> tuple:
    """
    时间范围
        - fmt存在，返回时间字符串
        - fmt不存在 & unit存在，返回时间戳
        - fmt不存在 & unit不存在，返回时间对象

    e.g.::

        tr = utils.timerange('2021-12-12')

        +++++[更多详见参数或源码]+++++

    :param start: 开始
    :param end: 结束
    :param fmt: 格式化
    :param unit: 单位（fs-浮点型秒, s-秒，ms-毫秒，us-微秒，ns-纳秒）
    :return:
    """
    start_time = timestr2time(start)
    end_time = timestr2time(end or start)
    if not end or len(end) == 10:
        end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)
    if fmt:
        return start_time.strftime(fmt), end_time.strftime(fmt)
    if unit:
        if unit == "fs":
            return start_time.timestamp(), end_time.timestamp()
        units = {"s": 1, "ms": 1000, "us": 1000000, "ns": 1000000000}
        return int(start_time.timestamp() * units.get(unit, 1000)), int(end_time.timestamp() * units.get(unit, 1000))
    return start_time, end_time


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


def readblock(filepath: str, block: int = 8192, mode: str = 'rb', **kwargs) -> t.Generator:
    """
    分块读取

    e.g.::

        content = utils.readblock('foo.txt')

        +++++[更多详见参数或源码]+++++

    :param filepath: 文件路径
    :param block: 块
    :param mode: 模式
    :param kwargs: open其他参数
    :return:
    """
    with open(filepath, mode=mode, **kwargs) as fp:
        while True:
            content = fp.read(block)
            if content:
                yield content
            else:
                break


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
    _support_types = [
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
        if src.suffix not in _support_types:
            raise ValueError('only supported: %s' % _support_types)
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
            if file_type not in _support_types:
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


def writetemp(content: t.Union[bytes, str], suffix: str, **kwargs) -> str:
    """
    写入临时文件

    e.g.::

        filepath = utils.writetemp(content)

        +++++[更多详见参数或源码]+++++

    :param content: 内容
    :param suffix: 后缀
    :param kwargs: kwargs
    :return:
    """
    with tempfile.NamedTemporaryFile(
            suffix=suffix,
            mode="w+b" if isinstance(content, bytes) else "w+",
            delete=False,
            **kwargs,
    ) as f:
        f.write(content)
        return f.name


def gen_leveldirs(
        tag: str,
        number: int = 3,
        length: int = 2,
        is_keep_extra: bool = False,
        prefix: str = None,
        sep: str = os.sep,
) -> str:
    """
    生成层级目录

    e.g.::

        tag = "abcdef"
        dirs = utils.gen_leveldirs(tag)

        +++++[更多详见参数或源码]+++++

    :param tag: 目标
    :param number: 数量
    :param length: 长度
    :param is_keep_extra: 是否保留额外的
    :param prefix: 前级
    :param sep: 分隔符
    :return:
    """
    dirs = [d for i in range(0, number * length, length) if (d := tag[i:i + length])]
    if is_keep_extra:
        dirs.append(tag[len(''.join(dirs)):])
    if prefix:
        dirs.insert(0, prefix)
    return sep.join(filter(bool, dirs))


def map_jsontype(
        typename: str,
        is_title: bool = False,
        is_keep_integer: bool = False,
) -> str:
    """
    映射json类型

    e.g.::

        typename = "str"
        mt = utils.map_jsontype(typename)

        +++++[更多详见参数或源码]+++++

    :param typename: 类型名称
    :param is_title: 是否首字母大写
    :param is_keep_integer: 是否保留integer
    :return:
    """
    maps = {
        'NoneType': 'null',
        'None': 'null',
        'bool': 'boolean',
        'str': 'string',
        'int': 'number',
        'float': 'number',
        'list': 'array',
        'tuple': 'array',
        'dict': 'object',
    }
    if is_keep_integer:
        maps['int'] = 'integer'
    if jt := maps.get(typename):
        if is_title:
            return jt.title()
        return jt
    return typename


def pkg_lver(pkg_name: str) -> str:
    """
    包的最新版本

    e.g.::

        v = utils.pkg_lver("toollib")

        +++++[更多详见参数或源码]+++++

    :param pkg_name: 包名
    :return:
    """
    try:
        with request.urlopen(f"https://pypi.org/pypi/{pkg_name}/json") as resp:
            if resp.status == 200:
                data = loads(resp.read().decode("utf-8"))
                return data["info"]["version"]
            else:
                raise Exception(f"Failed to fetch data. Status code: {resp.status}")
    except Exception:
        raise


def localip(dns_servers: list[str] = None) -> str:
    """
    本地ip

    e.g.::

        ip = utils.localip()
        ip = utils.localip(["8.8.4.4", "1.1.1.1"])  # 使用自定义DNS

        +++++[更多详见参数或源码]+++++

    :param dns_servers: dns服务
    :return:
    """
    default_dns = [
        "223.5.5.5",  # 阿里云DNS
        "180.76.76.76",  # 百度DNS
        "119.29.29.29",  # 腾讯DNS
        "114.114.114.114",  # 114DNS
        "8.8.8.8",  # 谷歌DNS
    ]
    for dns in dns_servers if dns_servers else default_dns:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(2)
                s.connect((dns, 80))
                return s.getsockname()[0]
        except (socket.timeout, OSError, Exception):
            continue
        finally:
            if isinstance(s, socket.socket):
                s.close()
    return ""
