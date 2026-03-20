"""
@author axiner
@version v1.0.0
@created 2022/3/5 0:03
@abstract 校验器
@description
@history
"""

import platform
import re

__all__ = [
    "Attr",
    "choicer",
    "pyv",
]


class Attr:
    """
    属性校验（数据描述符）

    e.g.::

        请查看数据描述符中数据校验.....

        +++++[更多详见参数或源码]+++++
    """

    def __init__(
        self,
        key,
        ktype=None,
        required=False,
        enum=None,
        regex=None,
        callback=None,
        error_msg=None,
        empty_msg=None,
    ):
        self.key = key
        self.ktype = ktype
        self.required = required
        self.enum = enum
        self.regex = regex
        self.callback = callback
        self.error_msg = error_msg
        self.empty_msg = empty_msg or f'"{self.key}" cannot be empty'

    def __get__(self, instance, owner):
        return instance.__dict__[self.key]

    def __set__(self, instance, value):
        if not value:
            if self.required is True:
                raise TypeError(self.empty_msg)
        else:
            if self.ktype:
                if not isinstance(value, self.ktype):
                    error_msg = self.error_msg
                    if not error_msg:
                        error_msg = f'"{self.key}" only supported: {self.ktype}'
                    raise TypeError(error_msg)
            elif self.enum is not None:
                if isinstance(self.enum, (list, tuple)):
                    if value not in self.enum:
                        error_msg = self.error_msg
                        if not error_msg:
                            error_msg = f'"{self.key}" only select from: {self.ktype}'
                        raise TypeError(error_msg)
                else:
                    raise TypeError('"enum" only supported: list or tuple')
            elif self.regex is not None and re.match(self.regex, value) is None:
                raise TypeError(f'"{self.key}" only supported: {self.regex}')

            if self.callback is not None:
                self.callback(value)
        instance.__dict__[self.key] = value

    def __delete__(self, instance):
        instance.__dict__.pop(self.key)


def choicer(obj, choices: list, lable: str | None = None, errmsg: str | None = None):
    """
    选择校验（校验通过时返回obj）

    e.g.::

        flag = 1
        flag = validator.choicer(flag, choices=[1,2,3], lable='标识')

        # res: 若校验不通过则报异常

        +++++[更多详见参数或源码]+++++

    :param obj: 对象
    :param choices: 可选范围
    :param lable: 标签
    :param errmsg: 不在可选范围时报错信息
    :return:
    """
    if obj not in choices:
        if not errmsg:
            errmsg = f"only supported: {choices}"
            if lable:
                errmsg = f'"{lable}" {errmsg}'
        raise TypeError(errmsg)
    return obj


def pyv(min_v: str = "3.7", max_v: str | None = None) -> str:
    """
    python版本校验

    e.g.::

        pyv = validator.pyv(min_v='3.7')

        # res: 若校验不通过则报异常

        +++++[更多详见参数或源码]+++++

    :param min_v: 最小版本号（包含）
    :param max_v: 最大版本号（不包含）
    :return:
    """
    _pyv = platform.python_version()
    if _pyv < min_v:
        raise Warning(f"python version required >= {min_v}")
    if max_v and _pyv >= max_v:
        raise Warning(f"python version required < {max_v}")
    return _pyv
