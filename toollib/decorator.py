"""
@author axiner
@version v1.0.0
@created 2021/12/14 20:28
@abstract 装饰器
@description
@history
"""
import time
import traceback
import typing as t
from functools import wraps

from toollib.validator import sysn

__all__ = [
    'print_return',
    'catch_exception',
    'timer',
    'sys_required',
]

# config of print
FLWIDTH = 66
FLCHAR = '-'


def print_return(is_print: bool = True):
    """
    打印返回结果
    使用示例：
        @decorator.print_return()
        def foo():
            return 'this is toollib'
    :param is_print: 是否打印
    :return:
    """
    def wrapper(func: t.Callable):
        @wraps(func)
        def inner(*args, **kwargs):
            result = func(*args, **kwargs)
            if is_print is True:
                print('func: "{0}", return: {1}\t【@type: {2}】'.format(
                    func.__name__, result, type(result)).center(FLWIDTH, FLCHAR))
            return result
        return inner
    return wrapper


def catch_exception(is_raise: bool = True):
    """
    捕获异常
    使用示例：
        @decorator.catch_exception()
        def foo():
            pass
    :param is_raise: 是否raise
    :return:
    """
    def wrapper(func: t.Callable):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                if is_raise is True:
                    raise
                else:
                    traceback.print_exc()
        return inner
    return wrapper


def timer(func: t.Callable):
    """
    计时器
    使用示例：
        @decorator.timer()
        def foo():
            pass
    :param func:
    :return:
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        print('func: "{0}", start.....'.format(func.__name__).center(FLWIDTH, FLCHAR))
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print('func: "{0}" finished, spent time: {1:.2f}s'.format(
            func.__name__, end_time - start_time).center(FLWIDTH, FLCHAR))
        return result
    return wrapper


def sys_required(supported_sys: str = '.*', errmsg: str = None):
    """
    系统要求
    使用示例：
        @decorator.sys_required()
        def foo():
            pass
    :param supported_sys: 支持的系统（正则表达示）
    :param errmsg: 匹配失败信息
    :return:
    """
    errmsg = errmsg or 'system only supported: %s' % supported_sys

    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if not sysn(supported_sys):
                raise TypeError(errmsg)
            return func(*args, **kwargs)
        return inner
    return wrapper
