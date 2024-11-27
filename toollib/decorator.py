"""
@author axiner
@version v1.0.0
@created 2021/12/14 20:28
@abstract 装饰器
@description
@history
"""
import asyncio
import os
import re
import sys
import time
import traceback
import typing as t
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps

from toollib.utils import sysname

__all__ = [
    'catch_exception',
    'timer',
    'sys_required',
    'to_async',
]


def catch_exception(
        is_raise: bool = True,
        default_result: t.Any = None,
        exception: t.Type[Exception] = None,
        errmsg: str = None,
):
    """
    捕获异常

    e.g.::

        @decorator.catch_exception()
        def foo():
            pass

        +++++[更多详见参数或源码]+++++

    :param is_raise: 是否raise
    :param default_result: 默认结果
    :param exception: 异常类
    :param errmsg: 异常信息
    :return:
    """

    def wrapper(func: t.Callable):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if is_raise is True:
                    if exception is not None:
                        raise exception(errmsg or str(e))
                    raise
                else:
                    traceback.print_exc()
                    return default_result

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
        print('[{0}]starting...'.format(func.__name__))
        start_time = time.time()
        result = func(*args, **kwargs)
        print('[{0}]completed({1:.2f}s)'.format(func.__name__, time.time() - start_time))
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
                    sys.stderr.write(errmsg + '\n')
                    sys.exit(1)
            return func(*args, **kwargs)

        return inner

    return wrapper


def to_async(
        pool_type: t.Literal['thread', 'process'] = 'thread',
        max_workers: int = None
):
    """
    转为异步函数

    e.g.::

        @decorator.to_async()
        def foo():
            pass

        +++++[更多详见参数或源码]+++++

    :param pool_type: 池的类型（['thread', 'process']）
    :param max_workers: 池的最大工作数
    :return:
    """

    def wrapper(func: t.Callable):
        if pool_type == 'thread':
            executor = ThreadPoolExecutor(max_workers=max_workers)
        elif pool_type == 'process':
            executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            raise ValueError("pool_type only supported: ['thread', 'process']")

        @wraps(func)
        async def inner(*args, **kwargs) -> t.Any:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(executor, lambda: func(*args, **kwargs))
            return result

        return inner

    return wrapper
