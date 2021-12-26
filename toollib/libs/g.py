"""
@author axiner
@version v1.0.0
@created 2021/12/18 22:21
@abstract
@description
@history
"""
import sqlite3
import typing as t

from toollib.libs.utils import SingletonType, Utils


class G(metaclass=SingletonType):
    """global variable"""

    _support_types = (str, list, dict, int, float, bool)

    def __init__(self, gfile: str, *args, **kwargs):
        self._gfile = gfile
        self._new_db()
        super(G, self).__init__(*args, **kwargs)

    @property
    def conn(self):
        conn = sqlite3.connect(self._gfile)
        return conn

    def get(self, key: str):
        sql = "select v from g where k=?"
        parameters = (key,)
        value = self._queryone(sql, parameters)
        return value

    def set(self, key: str, value) -> None:
        sql = "replace into g (k, v) values(?, ?)"
        key = self._check_key(key)
        value = self._check_value(value)
        parameters = (key, value)
        self._execute(sql, parameters)

    def _check_key(self, key: str) -> str:
        if not isinstance(key, str):
            raise TypeError("Only supported: {}!".format(str))
        if not key:
            raise ValueError("Cannot be empty!")
        return key

    def _check_value(self, value):
        if not isinstance(value, self._support_types):
            raise TypeError("Only supported: {}!".format(self._support_types))
        return Utils.json(value, "dumps")

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
              "k text not null primary key , " \
              "v text)"
        self._execute(sql)

    def _queryone(self, sql: str, parameters: t.Iterable):
        conn = self.conn
        cursor = conn.cursor()
        cursor.execute(sql, parameters)
        value = cursor.fetchone()
        if value:
            value = Utils.json(value[0])
        self._close(cursor, conn)
        return value

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
