"""
@author axiner
@version v1.0.0
@created 2022/3/5 0:03
@abstract 验证器
@description
@history
"""
import re

__all__ = [
    'Typer',
    'choicer',
]


class Typer:
    """
    数据描述符类型验证
    """

    def __init__(self, key, ktype=None, required=True, enum=None, regex=None, func=None,
                 error_msg=None, empty_msg=None):
        self.key = key
        self.ktype = ktype
        self.required = required
        self.enum = enum
        self.regex = regex
        self.func = func
        self.error_msg = error_msg
        self.empty_msg = empty_msg or '"%s" cannot be empty' % self.key

    def __get__(self, instance, owner):
        return instance.__dict__[self.key]

    def __set__(self, instance, value):
        if value is None:
            if self.required is True:
                raise TypeError(self.empty_msg)
        else:
            if self.ktype:
                if not isinstance(value, self.ktype):
                    error_msg = self.error_msg
                    if not error_msg:
                        error_msg = f'"%s" only supported: %s' % (self.key, self.ktype)
                    raise TypeError(error_msg)
            elif self.enum is not None:
                if isinstance(self.enum, (list, tuple)):
                    if value not in self.enum:
                        error_msg = self.error_msg
                        if not error_msg:
                            error_msg = '"%s" only select from: %s' % (self.key, self.ktype)
                        raise TypeError(error_msg)
                else:
                    raise TypeError('"enum" only supported: list or tuple')
            elif self.regex is not None:
                if re.match(self.regex, value) is None:
                    raise TypeError('"%s" only supported: %s' % (self.key, self.regex))

            if self.func is not None:
                self.func(value)
        instance.__dict__[self.key] = value

    def __delete__(self, instance):
        instance.__dict__.pop(self.key)


def choicer(obj, choices: list, title: str = None, errmsg: str = None):
    """
    选择验证（校验通过时返回obj）
    :param obj: 对象
    :param choices: 可选范围
    :param title: 标题
    :param errmsg: 不在可选范围时报错信息
    :return:
    """
    try:
        choices.index(obj)
    except ValueError:
        if not errmsg:
            errmsg = 'only supported: %s' % choices
            if title:
                errmsg = '"%s" %s' % (title, errmsg)
        raise TypeError(errmsg)
    return obj
