"""
@author axiner
@version v1.0.0
@created 2024/2/28 10:20
@abstract 编解码
@description
@history
"""
import encodings
import typing as t

__all__ = [
    "common_encodings",
    "all_encodings",
    "detect_encoding",
]

common_encodings = [
    "utf-8",
    "ascii",
    "gbk",
    "gb2312",
    "big5",
    "iso-8859-1",
    "utf-16",
    "utf-32",
    "cp1252",
    "shift_jis",
    "euc-jp",
    "euc-kr",
    "iso-2022-jp",
    "koi8-r",
    "macroman",
    "iso-8859-2",
    "iso-8859-5",
    "iso-8859-15",
    "cp1251",
    "cp1250",
    "windows-1253",
    "windows-1254",
    "windows-1257",
    "iso-8859-3",
    "iso-8859-4",
    "iso-8859-7",
]

all_encodings = common_encodings + sorted(set(encodings.aliases.aliases.values()) - set(common_encodings))


def detect_encoding(data: t.Union[bytes, str], default: str = "utf-8"):
    """
    检测编码

    e.g.::

        encoding = utils.detect_encoding(data)

        +++++[更多详见参数或源码]+++++

    :param data: 数据
    :param default: 默认编码
    :return:
    """
    if isinstance(data, str):
        return default
    for e in all_encodings:
        try:
            data[:1024].decode(e)
            return e
        except:
            try:
                data.decode(e)
                return e
            except:
                pass
    return default
