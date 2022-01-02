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

from ._exception import ToolException
from ._singleton import ToolSingleton
from ._utils import ToolUtils


class ExpireError(ToolException):
    """expire error"""


class ToolG(metaclass=ToolSingleton):
    """global variable"""

    __support_types = {"str": str, "list": list, "dict": dict,
                       "int": int, "float": float, "bool": bool}

    def __init__(self, gfile: str, gtable: str = "g", *args, **kwargs):
        self.__gfile = gfile
        self.__gtable = gtable
        self.__new_db()
        super(ToolG, self).__init__(*args, **kwargs)

    def __conn(self):
        return sqlite3.connect(self.__gfile)

    def get(self, key: str, check_expire: bool = True):
        sql = "select v, expire from {tb} where k=?".format(tb=self.__gtable)
        parameters = (key,)
        value, expire = self.__queryone(sql, parameters)
        if value:
            if isinstance(check_expire, bool):
                if check_expire:
                    if expire > 0:
                        is_expire = expire - time.time()
                        if is_expire < 0:
                            raise ExpireError("'{}' has expired!".format(key))
            else:
                raise KeyError("'check_expire' only supported: bool!")
            value = ToolUtils.json(value)
        return value

    def set(self, key: str, value, expire=0) -> None:
        sql = "replace into {tb} (k, v, expire) values(?, ?, ?)".format(tb=self.__gtable)
        parameters = self.__check_parameters(key, value, expire)
        self.__execute(sql, parameters)

    def __check_parameters(self, key, value, expire):
        if isinstance(key, str):
            if not key:
                raise ValueError("'key' cannot be empty!")
        else:
            raise TypeError("'key' only supported: str!")
        if not isinstance(value, tuple(self.__support_types.values())):
            raise TypeError("'value' only supported: {}!".format(
                list(self.__support_types.keys())))
        else:
            value = ToolUtils.json(value, "dumps")
        if isinstance(expire, (int, float)):
            if expire < 0:
                raise ValueError("'expire' greater than or equal to 0!")
            elif expire > 0:
                expire = round(time.time() + expire, 7)
        else:
            raise TypeError("'expire' only supported: int or float!")
        parameters = (key, value, expire)
        return parameters

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
        sql = "create table if not exists {tb}(" \
              "k text not null primary key, " \
              "v text, " \
              "expire real)".format(tb=self.__gtable)
        self.__execute(sql)

    def __queryone(self, sql: str, parameters: t.Iterable):
        conn = self.__conn()
        cursor = conn.cursor()
        cursor.execute(sql, parameters)
        value, expire = cursor.fetchone()
        self.__close(cursor, conn)
        return value, expire

    def has_key(self, key: str) -> bool:
        conn = self.__conn()
        cursor = conn.cursor()
        sql = "select k from {tb} where k=?".format(tb=self.__gtable)
        parameters = (key,)
        cursor.execute(sql, parameters)
        result = cursor.fetchone()
        self.__close(cursor, conn)
        if not result:
            return False
        return True

    def delete(self, key: str) -> None:
        sql = "delete from {tb} where k=?".format(tb=self.__gtable)
        parameters = (key,)
        self.__execute(sql, parameters)

    def clean(self) -> None:
        sql = "delete from {tb}".format(tb=self.__gtable)
        self.__execute(sql)
