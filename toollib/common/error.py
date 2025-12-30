"""
@author axiner
@version v1.0.0
@created 2022/1/2 14:49
@abstract
@description
@history
"""


class ExpireError(Exception):
    """过期异常"""


class SystemClockError(Exception):
    """系统时钟异常"""


class DriverError(Exception):
    """驱动异常"""


class ConfFileError(OSError):
    """配置文件异常"""
