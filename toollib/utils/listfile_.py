from pathlib import Path
from typing import Union, Generator


def listfile(
        src: Union[str, Path],
        pattern: str = '*',
        is_str: bool = False,
        is_name: bool = False,
        is_r: bool = False,
) -> Generator:
    """
    文件列表

    e.g.::

        # 比如获取某目录下的.py文件
        src_dir = 'D:/tmp'
        flist = utils.listfile(src_dir, pattern='*.py')

        +++++[更多详见参数或源码]+++++

    :param src: 源目录
    :param pattern: 匹配模式
    :param is_str: 是否返回字符串（True: 若为路径返回字符串，False: 若为路径返回Path类型）
    :param is_name: 是否获取文件名（True: 返回文件路径，False: 返回文件名）
    :param is_r: 是否递规查找
    :return:
    """
    src_dir = Path(src).absolute()
    if not src_dir.is_dir():
        raise FileNotFoundError(f'{src} directory does not exist')
    src_files = src_dir.rglob(pattern) if is_r is True else src_dir.glob(pattern)
    for f in src_files:
        if f.is_file():
            if is_name is True:
                yield f.name
            else:
                if is_str is True:
                    yield f.as_posix()
                else:
                    yield f
