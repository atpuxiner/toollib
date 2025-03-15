import tempfile
from typing import Union


def writetemp(content: Union[bytes, str], suffix: str, **kwargs) -> str:
    """
    写入临时文件

    e.g.::

        filepath = utils.writetemp(content)

        +++++[更多详见参数或源码]+++++

    :param content: 内容
    :param suffix: 后缀
    :param kwargs: kwargs
    :return:
    """
    with tempfile.NamedTemporaryFile(
            suffix=suffix,
            mode="w+b" if isinstance(content, bytes) else "w+",
            delete=False,
            **kwargs,
    ) as f:
        f.write(content)
        return f.name
