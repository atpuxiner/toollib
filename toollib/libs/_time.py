"""
@author axiner
@version v1.0.0
@created 2021/12/14 20:25
@abstract
@description
@history
"""
from datetime import datetime


class ToolTime(object):
    """time"""

    @staticmethod
    def now2str(fmt: str = "S") -> str:
        """
        now datetime to str
        :param fmt:
        :return:
        """
        _ = {
            "S": "%Y-%m-%d %H:%M:%S",
            "M": "%Y-%m-%d %H:%M",
            "H": "%Y-%m-%d %H",
            "d": "%Y-%m-%d",
            "m": "%Y-%m",
            "Y": "%Y"
        }
        fmt = _.get(fmt, fmt)
        str_now = datetime.now().strftime(fmt)
        return str_now

    @staticmethod
    def str2datetime(time_str: str, fmt: str = None) -> datetime:
        """
        convert str datetime to datetime
        :param time_str:
        :param fmt:
        :return:
        """
        _ = {
            19: "%Y-%m-%d %H:%M:%S",
            16: "%Y-%m-%d %H:%M",
            13: "%Y-%m-%d %H",
            10: "%Y-%m-%d",
            7: "%Y-%m",
            4: "%Y"
        }
        fmt = fmt if fmt else _.get(len(time_str))
        dt = datetime.strptime(time_str, fmt)
        return dt
