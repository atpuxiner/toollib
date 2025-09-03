"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:21
@abstract key-value容器（基于sqlite3）
@description
@history
"""
import json
import os
import sqlite3
import tempfile
import time
from typing import Generator, Union

from toollib.common.error import ExpireError

__all__ = ['KValue']


class KValue:
    """
    key - value 容器
    - key 支持类型：
        - str
    - value 支持类型：
        - str
        - list
        - dict
        - int
        - float
        - bool
        - NoneType

    e.g.::

        # 创建一个 kvalue 实例
        kv = KValue()

        # 增改查删等操作
        kv.set(key='name', value='xxx')
        kv.get(key='name')
        kv.exists(key='name')
        kv.delete(key='name')
        ...

        +++++[更多详见参数或源码]+++++
    """

    __slots__ = ('file', 'tbname', 'columns', 'conn')
    _support_types = (str, list, dict, int, float, bool, type(None))

    def __init__(self, file: str = None, tbname: str = 'kvalue'):
        if not file:
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.kv', delete=False) as t:
                file = t.name
        self.file = os.path.abspath(file)
        self.tbname = tbname
        self.columns = (('key', 'text'), ('value', 'text'), ('expire', 'real'))
        self.conn = None
        self._new_db()

    def __enter__(self):
        # 连接数据库
        self.conn = sqlite3.connect(self.file)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def _new_db(self):
        if not self.conn:
            self.conn = sqlite3.connect(self.file)
        with self.conn as conn:
            sql = f'create table if not exists {self.tbname}(' \
                  'key text not null primary key, ' \
                  'value text, ' \
                  'expire real)'
            cursor = conn.cursor()
            cursor.execute(sql)

    def _validate_parameters(self, key, value=None, expire=None):
        if isinstance(key, str):
            if not key:
                raise ValueError('"key" cannot be empty')
        else:
            raise TypeError('"key" only supported: str')
        if value is not None:
            if not isinstance(value, self._support_types):
                raise TypeError(f'"value" only supported: {[t.__name__ for t in self._support_types]}')
            value = json.dumps(value)
        if expire is not None:
            if isinstance(expire, (int, float)):
                if expire < 0:
                    raise ValueError('"expire" greater than or equal to 0')
                elif expire > 0:
                    expire = round(time.time() + expire, 7)
            else:
                raise TypeError('"expire" only supported: int or float')
        return key, value, expire

    def get(self, key: str, raise_expire: bool = False, return_expire: bool = False):
        """
        获取 key 的 value
        :param key:
        :param raise_expire: 是否过期异常
        :param return_expire: 是否返回过期时间
        :return:
        """
        with self.conn as conn:
            sql = f'select value, expire from {self.tbname} where key =?'
            cursor = conn.cursor()
            cursor.execute(sql, (key,))
            one = cursor.fetchone()
            value, expire = one if one else (None, None)
            if raise_expire:
                if expire and expire <= time.time():
                    raise ExpireError(f'"{key}" already expired')
            if value:
                value = json.loads(value)
            if return_expire:
                return value, expire
            return value

    def keys(self, reverse: bool = False) -> Generator:
        """
        获取所有 key
        :return:
        """
        order = "desc" if reverse else "asc"
        with self.conn as conn:
            sql = f'select key from {self.tbname} order by key {order}'
            cursor = conn.cursor()
            cursor.execute(sql)
            for row in cursor.fetchall():
                yield row[0]

    def items(self, reverse: bool = False) -> Generator:
        """
        获取所有 item
        :return:
        """
        order = "desc" if reverse else "asc"
        with self.conn as conn:
            sql = f'select key, value, expire from {self.tbname} order by key {order}'
            cursor = conn.cursor()
            cursor.execute(sql)
            for row in cursor.fetchall():
                yield row

    def set(
            self,
            key: str,
            value: Union[str, list, dict, int, float, bool, type(None)],
            expire: Union[int, float] = 0.0,
    ):
        """
        设置 kye - value
        :param key:
        :param value:
        :param expire: 默认为 0.0（表不设置过期时间）
        :return:
        """
        with self.conn as conn:
            key, value, expire = self._validate_parameters(key=key, value=value, expire=expire)
            sql = f'replace into {self.tbname} (key, value, expire) values(?,?,?)'
            cursor = conn.cursor()
            cursor.execute(sql, (key, value, expire))
            return cursor.rowcount

    def expire(self, key: str, expire: Union[int, float] = 0.0):
        """
        设置 key 的过期时间
        :param key:
        :param expire: 默认为 0.0（表不设置过期时间）
        :return:
        """
        with self.conn as conn:
            key, _, expire = self._validate_parameters(key=key, expire=expire)
            sql = f'update {self.tbname} set expire =? where key =?'
            cursor = conn.cursor()
            cursor.execute(sql, (expire, key))
            return cursor.rowcount

    def exists(self, key: str) -> bool:
        """
        检测 key 是否存在
        :param key:
        :return:
        """
        with self.conn as conn:
            sql = f'select exists(select 1 from {self.tbname} where key =?)'
            cursor = conn.cursor()
            cursor.execute(sql, (key,))
            result = cursor.fetchone()[0]
            return bool(result)

    def delete(self, key: str):
        """
        删除 key
        :param key:
        :return:
        """
        with self.conn as conn:
            sql = f'delete from {self.tbname} where key =?'
            cursor = conn.cursor()
            cursor.execute(sql, (key,))
            return cursor.rowcount

    def clear(self):
        """
        清除所有 key - value
        :return:
        """
        with self.conn as conn:
            sql = f'delete from {self.tbname}'
            cursor = conn.cursor()
            cursor.execute(sql)
            return cursor.rowcount

    def clear_expired(self):
        """
        清除已过期的 key - value
        :return:
        """
        with self.conn as conn:
            sql = f'delete from {self.tbname} where expire <= ?'
            cursor = conn.cursor()
            cursor.execute(sql, (time.time(),))
            return cursor.rowcount

    def remove(self):
        """
        移除实例的数据文件
        :return:
        """
        if os.path.isfile(self.file):
            if self.conn:
                self.conn.close()
            os.remove(self.file)
