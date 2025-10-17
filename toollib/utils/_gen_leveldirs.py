import os


def gen_leveldirs(
        tag: str,
        number: int = 3,
        length: int = 2,
        is_keep_extra: bool = False,
        prefix: str = None,
        sep: str = os.sep,
) -> str:
    """
    生成层级目录

    e.g.::

        tag = "abcdef"
        dirs = utils.gen_leveldirs(tag)

        +++++[更多详见参数或源码]+++++

    :param tag: 目标
    :param number: 数量
    :param length: 长度
    :param is_keep_extra: 是否保留额外的
    :param prefix: 前级
    :param sep: 分隔符
    :return:
    """
    dirs = [d for i in range(0, number * length, length) if (d := tag[i:i + length])]
    if is_keep_extra:
        dirs.append(tag[len(''.join(dirs)):])
    if prefix:
        dirs.insert(0, prefix)
    return sep.join(filter(bool, dirs))
