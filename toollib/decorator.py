"""
@author axiner
@version v1.0.0
@created 2021/12/14 20:28
@abstract 装饰器
@description
@history
"""
import os
import re
import sys
import time
import traceback
import typing as t
from functools import wraps

from toollib.utils import sysname

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

    e.g.::

        @decorator.print_return()
        def foo():
            return 'this is toollib'

        +++++[更多详见参数或源码]+++++

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

    e.g.::

        @decorator.catch_exception()
        def foo():
            pass

        +++++[更多详见参数或源码]+++++

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

    e.g.::

        @decorator.timer()
        def foo():
            pass

        +++++[更多详见参数或源码]+++++

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


def sys_required(supported_sys: str = None, errmsg: str = None, is_raise: bool = False):
    """
    系统要求

    e.g.::

        @decorator.sys_required()
        def foo():
            pass

        +++++[更多详见参数或源码]+++++

    注：当前系统名称：优先从环境变量获取，其次自动获取（以防自动获取不精确，则可手动设置）

    :param supported_sys: 支持的系统（正则表达式）
    :param errmsg: 匹配失败信息
    :param is_raise: 是否raise
    :return:
    """
    errmsg = errmsg or 'System only supported: %s' % supported_sys

    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            curr_sysname = os.environ.get('sysname') or sysname()
            if supported_sys and not re.search(supported_sys, curr_sysname, re.I):
                if is_raise is True:
                    raise TypeError(errmsg)
                else:
                    sys.stderr.write(errmsg+'\n')
                    sys.exit(1)
            return func(*args, **kwargs)
        return inner
    return wrapper
