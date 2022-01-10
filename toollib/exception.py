"""
@author axiner
@version v1.0.0
@created 2022/1/2 14:49
@abstract
@description
@history
"""


class ToolException(Exception):
    """异常基类"""

    def __init__(self, msg="Raise exception", code=1):
        self.msg = msg
        self.code = code
        self.error = {"code": self.code, "msg": self.msg}

    def __str__(self):
        return self.msg


class ExpireError(ToolException):
    """expire error"""
