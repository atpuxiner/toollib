"""
@author axiner
@version v1.0.0
@created 2022/1/2 14:49
@abstract
@description
@history
"""


class Error(Exception):
    """Error基类"""

    def __init__(self, msg='Raise error', code=1):
        self.msg = msg
        self.code = code
        self.error = {'code': self.code, 'msg': self.msg}

    def __str__(self):
        return self.msg


class ExpireError(Error):
    """过期异常"""


class SystemClockError(Error):
    """系统时钟异常"""


class DriverError(Error):
    """驱动异常"""
