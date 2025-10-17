from datetime import datetime
from typing import Literal, Union
from zoneinfo import ZoneInfo


def now2timestamp(
        unit: Literal['fs', 's', 'ms', 'us', 'ns'] = "ms",
        tzname: str = "Asia/Shanghai",
) -> Union[int, float]:
    """
    获取当前时间戳

    e.g.::

        timestamp = utils.now2timestamp()

        +++++[更多详见参数或源码]+++++

    :param unit: 单位（fs-浮点型秒, s-秒，ms-毫秒，us-微秒，ns-纳秒）
    :param tzname: 时区名称
    :return:
    """
    zinfo = ZoneInfo(tzname)
    timestamp = datetime.utcnow().timestamp() + zinfo.utcoffset(datetime.now().astimezone(zinfo)).total_seconds()
    if unit == "fs":
        return timestamp
    return int(timestamp * {"s": 1, "ms": 1000, "us": 1000000, "ns": 1000000000}.get(unit, 1000))
