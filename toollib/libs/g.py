"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:21
@abstract
@description
@history
"""
import sqlite3
import time
import typing as t

from toollib.libs.utils import SingletonType, Utils, ToolException


class ExpireError(ToolException):
    """expire error"""


class G(metaclass=SingletonType):
    """global variable"""

    _support_types = (str, list, dict, int, float, bool)
    _support_types_str = "str, list, dict, int, float, bool"

    def __init__(self, gfile: str, *args, **kwargs):
        self._gfile = gfile
        self._new_db()
        super(G, self).__init__(*args, **kwargs)

    @property
    def conn(self):
        conn = sqlite3.connect(self._gfile)
        return conn

    def get(self, key: str, check_expire: bool = True):
        sql = "select v, expire from g where k=?"
        parameters = (key,)
        value, expire = self._queryone(sql, parameters)
        if value:
            if isinstance(check_expire, bool):
                if check_expire:
                    is_expire = time.time() - expire
                    if is_expire > 0:
                        raise ExpireError("'{}' has expired!".format(key))
            else:
                raise KeyError("'check_expire' is bool!")
            value = Utils.json(value)
        return value

    def set(self, key: str, value, expire=0) -> None:
        sql = "replace into g (k, v, expire) values(?, ?, ?)"
        parameters = self._check_parameters(key, value, expire)
        self._execute(sql, parameters)

    def _check_parameters(self, key, value, expire):
        if isinstance(key, str):
            if not key:
                raise ValueError("'key' cannot be empty!")
        else:
            raise TypeError("'key' only supported: str!")
        if not isinstance(value, self._support_types):
            raise TypeError("'value' only supported: {}!".format(self._support_types_str))
        else:
            value = Utils.json(value, "dumps")
        if isinstance(expire, (int, float)):
            if expire < 0:
                raise ValueError("'expire' greater than or equal to 0!")
            expire = round(time.time() + expire, 7)
        else:
            raise TypeError("'expire' only supported: int or float!")
        parameters = (key, value, expire)
        return parameters

    def _execute(self, sql: str, parameters: t.Iterable = None) -> None:
        conn = self.conn
        cursor = conn.cursor()
        if parameters:
            cursor.execute(sql, parameters)
        else:
            cursor.execute(sql)
        conn.commit()
        self._close(cursor, conn)

    def _close(self, cursor, conn) -> None:
        cursor.close()
        conn.close()

    def _new_db(self) -> None:
        sql = "create table if not exists g(" \
              "k text not null primary key, " \
              "v text, " \
              "expire real)"
        self._execute(sql)

    def _queryone(self, sql: str, parameters: t.Iterable):
        conn = self.conn
        cursor = conn.cursor()
        cursor.execute(sql, parameters)
        value, expire = cursor.fetchone()
        self._close(cursor, conn)
        return value, expire

    def has_key(self, key: str) -> bool:
        conn = self.conn
        cursor = conn.cursor()
        sql = "select k from g where k=?"
        parameters = (key,)
        cursor.execute(sql, parameters)
        result = cursor.fetchone()
        self._close(cursor, conn)
        if not result:
            return False
        return True

    def delete(self, key: str) -> None:
        sql = "delete from g where k=?"
        parameters = (key,)
        self._execute(sql, parameters)

    def clean(self) -> None:
        sql = "delete from g"
        self._execute(sql)
