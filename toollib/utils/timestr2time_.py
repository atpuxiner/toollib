from datetime import datetime
from typing import Literal, Union
from zoneinfo import ZoneInfo


def timestr2time(
        timestr: str,
        fmt: str = None,
        unit: Literal['fs', 's', 'ms', 'us', 'ns'] = None,
        tzname: str = None,
) -> Union[datetime, int, float]:
    """
    时间字符串转时间对象或时间戳(unit若存在)

    e.g.::

        dt = utils.timestr2time('2021-12-12')

        +++++[更多详见参数或源码]+++++

    :param timestr: 时间字符串
    :param fmt: 格式化
    :param unit: 单位（fs-浮点型秒, s-秒，ms-毫秒，us-微秒，ns-纳秒）
    :param tzname: 时区名称
    :return:
    """
    if "T" in timestr:
        timestr = timestr.replace("Z", "+00:00")
    if not fmt:
        dt = datetime.fromisoformat(timestr)
    else:
        dt = datetime.strptime(timestr, fmt)
    if unit:
        if tzname:
            dt = dt.replace(tzinfo=ZoneInfo(tzname))
        if unit == "fs":
            return dt.timestamp()
        return int(dt.timestamp() * {"s": 1, "ms": 1000, "us": 1000000, "ns": 1000000000}.get(unit, 1000))
    if tzname:
        return dt.astimezone(ZoneInfo(tzname))
    return dt
