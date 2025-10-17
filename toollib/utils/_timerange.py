from typing import Literal

from toollib.utils import timestr2time


def timerange(
        start: str,
        end: str = None,
        fmt: str = None,
        unit: Literal['fs', 's', 'ms', 'us', 'ns'] = None,
) -> tuple:
    """
    时间范围
        - fmt存在，返回时间字符串
        - fmt不存在 & unit存在，返回时间戳
        - fmt不存在 & unit不存在，返回时间对象

    e.g.::

        tr = utils.timerange('2021-12-12')

        +++++[更多详见参数或源码]+++++

    :param start: 开始
    :param end: 结束
    :param fmt: 格式化
    :param unit: 单位（fs-浮点型秒, s-秒，ms-毫秒，us-微秒，ns-纳秒）
    :return:
    """
    start_time = timestr2time(start)
    end_time = timestr2time(end or start)
    if not end or len(end) == 10:
        end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)
    if fmt:
        return start_time.strftime(fmt), end_time.strftime(fmt)
    if unit:
        if unit == "fs":
            return start_time.timestamp(), end_time.timestamp()
        units = {"s": 1, "ms": 1000, "us": 1000000, "ns": 1000000000}
        return int(start_time.timestamp() * units.get(unit, 1000)), int(end_time.timestamp() * units.get(unit, 1000))
    return start_time, end_time
