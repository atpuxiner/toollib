"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:21
@abstract key-value容器（基于sqlite3）
@description
@history
"""
import os
import sqlite3
import time
import typing as t
from pathlib import Path

from toollib.common.error import ExpireError
from toollib.utils import json, Singleton

__all__ = ['KV']


class KV(metaclass=Singleton):
    """

    key-value容器

    e.g.::

        # 创建一个kv实例
        kv = kvalue.KV(kvfile='D:/tmp/kv.db')

        # 增改查删操作
        kv.set(key='name', value='xxx')
        kv.expire(key='name', ex=60)  # 过期时间
        kv.get(key='name')
        kv.exists(key='name')
        kv.delete(key='name')

        +++++[更多详见参数或源码]+++++
    """

    __support_types = (str, list,  dict, int, float, bool, type(None))

    def __init__(self, kvfile: t.Union[str, Path], kvtable: str = 'kvalues', *args, **kwargs):
        self.__kvfile, self.__kvtable = self.__check_g(kvfile, kvtable)
        self.__new_db()
        super(KV, self).__init__(*args, **kwargs)

    def __check_g(self, kvfile, kvtable):
        if isinstance(kvfile, (str, Path)):
            if not kvfile:
                raise ValueError('"kvfile" cannot be empty')
            kvfile = str(kvfile)
        else:
            raise TypeError('"kvfile" only supported: str or Path')
        if isinstance(kvtable, str):
            if not kvtable:
                raise ValueError('"kvtable" cannot be empty')
        else:
            raise TypeError('"kvtable" only supported: str')
        return kvfile, kvtable

    def __conn(self):
        return sqlite3.connect(self.__kvfile)

    def get(self, key: str, check_expire: bool = True, get_expire: bool = False):
        """
        获取key的value
        :param key:
        :param check_expire: 是否检测过期（True: 若过期则会raise）
        :param get_expire: 是否返回过期时间（True: 返回格式为元组(value, expire)）
        :return:
        """
        sql = 'select v, expire from {tb} where k=?'.format(tb=self.__kvtable)
        parameters = (key,)
        value, expire = self.__queryone(sql, parameters)
        if isinstance(check_expire, bool):
            if check_expire is True:
                if expire > 0:
                    is_expire = expire - time.time()
                    if is_expire < 0:
                        raise ExpireError('"%s" has expired' % key)
        else:
            raise TypeError('"check_expire" only supported: bool')
        if value:
            value = json(value)
        if get_expire is True:
            return value, expire
        return value

    def set(self, key: str, value, expire: t.Union[int, float] = 0) -> None:
        """
        设置kye-value
        :param key:
        :param value:
        :param expire: 默认为0（表不设置过期时间）
        :return:
        """
        parameters = self.__check_parameters(key, value, expire)
        sql = 'replace into {tb} (k, v, expire) values(?, ?, ?)'.format(tb=self.__kvtable)
        self.__execute(sql, parameters)

    def expire(self, key: str, ex: t.Union[int, float] = 0):
        """
        设置key的过期时间
        :param key:
        :param ex: 默认为0（表不设置过期时间）
        :return:
        """
        key, _, ex = self.__check_parameters(key=key, expire=ex)
        parameters = (ex, key)
        sql = 'update {tb} set expire=? where k=?'.format(tb=self.__kvtable)
        self.__execute(sql, parameters)

    def __check_parameters(self, key, value=None, expire=None):
        if isinstance(key, str):
            if not key:
                raise ValueError('"key" cannot be empty')
        else:
            raise TypeError('"key" only supported: str')
        if value is not None:
            if not isinstance(value, self.__support_types):
                raise TypeError('"value" only supported: %s' % [
                    _t.__name__ for _t in self.__support_types])
            else:
                value = json(value, 'dumps')
        if expire is not None:
            if isinstance(expire, (int, float)):
                if expire < 0:
                    raise ValueError('"expire" greater than or equal to 0')
                elif expire > 0:
                    expire = round(time.time() + expire, 7)
            else:
                raise TypeError('"expire" only supported: int or float')
        return key, value, expire

    def __execute(self, sql: str, parameters: t.Iterable = None) -> None:
        conn = self.__conn()
        cursor = conn.cursor()
        if parameters:
            cursor.execute(sql, parameters)
        else:
            cursor.execute(sql)
        conn.commit()
        self.__close(cursor, conn)

    def __close(self, cursor, conn) -> None:
        cursor.close()
        conn.close()

    def __new_db(self) -> None:
        sql = 'create table if not exists {tb}(' \
              'k text not null primary key, ' \
              'v text, ' \
              'expire real)'.format(tb=self.__kvtable)
        self.__execute(sql)

    def __queryone(self, sql: str, parameters: t.Iterable):
        conn = self.__conn()
        cursor = conn.cursor()
        cursor.execute(sql, parameters)
        one = cursor.fetchone()
        value, expire = one if one else (None, 0)
        self.__close(cursor, conn)
        return value, expire

    def exists(self, key: str) -> bool:
        """
        检测key是否存在
        :param key:
        :return:
        """
        conn = self.__conn()
        cursor = conn.cursor()
        sql = 'select k from {tb} where k=?'.format(tb=self.__kvtable)
        parameters = (key,)
        cursor.execute(sql, parameters)
        result = cursor.fetchone()
        self.__close(cursor, conn)
        if not result:
            return False
        return True

    def delete(self, key: str) -> None:
        """
        删除key
        :param key:
        :return:
        """
        sql = 'delete from {tb} where k=?'.format(tb=self.__kvtable)
        parameters = (key,)
        self.__execute(sql, parameters)

    def clear(self) -> None:
        """
        清除所有key-value
        :return:
        """
        sql = 'delete from {tb}'.format(tb=self.__kvtable)
        self.__execute(sql)

    def remove(self) -> None:
        """
        移除KV实例的kvfile文件
        :return:
        """
        os.remove(self.__kvfile)
