from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def now2timestr(
        fmt: str = "%Y-%m-%d %H:%M:%S",
        tzname="Asia/Shanghai",
) -> str:
    """
    获取当前时间字符串

    e.g.::

        now = utils.now2timestr()

        +++++[更多详见参数或源码]+++++

    :param fmt: 格式化
    :param tzname: 时区名称
    :return:
    """
    return datetime.now(timezone.utc).astimezone(ZoneInfo(tzname)).strftime(fmt)
