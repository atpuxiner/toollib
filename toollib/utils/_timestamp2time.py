from datetime import datetime
from typing import Literal, Union
from zoneinfo import ZoneInfo


def timestamp2time(
        timestamp: Union[int, float],
        unit: Literal['s', 'ms', 'us', 'ns'] = "ms",
        fmt: str = None,
        tzname: str = None,
) -> Union[datetime, str]:
    """
    时间戳转时间对象或时间字符串(fmt若存在)

    e.g.::

        dt = utils.timestamp2time()

        +++++[更多详见参数或源码]+++++

    :param timestamp: 时间戳
    :param unit: 单位（s-秒，ms-毫秒，us-微秒，ns-纳秒）
    :param fmt: 格式化
    :param tzname: 时区名称
    :return:
    """
    if unit == "ms":
        timestamp = timestamp / 1000.0
    elif unit == "s":
        pass
    elif unit == "us":
        timestamp = timestamp / 1000000.0
    elif unit == "ns":
        timestamp = timestamp / 1000000000.0
    dt = datetime.fromtimestamp(timestamp)
    if tzname:
        dt = dt.astimezone(ZoneInfo(tzname))
    if fmt:
        return dt.strftime(fmt)
    return dt
