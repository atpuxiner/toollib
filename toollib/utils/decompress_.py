import stat
import tarfile
import traceback
from pathlib import Path
from typing import Union

from toollib.common import rarfile, zipfile

from toollib.utils import listfile


def decompress(
        src: Union[str, Path],
        dst: Union[str, Path] = None,
        pattern: str = '*[.pzr2]',
        is_r: bool = False,
        is_raise: bool = True,
) -> int:
    """
    解压文件

    e.g.::

        # 比如解压某目录下的.zip文件
        src = 'D:/tmp'
        count = utils.decompress(src, pattern='*.zip')

        +++++[更多详见参数或源码]+++++

    :param src: 源目录或文件
    :param dst: 目标目录
    :param pattern: 匹配模式（当src为目录时生效，默认匹配所有支持的压缩包）
    :param is_r: 是否递规查找（当src为目录时生效）
    :param is_raise: 是否抛异常
    :return: count（解压数量）
    """
    _support_types = [
        '.zip',
        '.rar',
        '.tar',
        '.gz', '.tgz',
        '.xz', '.txz',
        '.bz2', '.tbz', '.tbz2', '.tb2',
    ]
    src = Path(src).absolute()
    src_is_dir = False
    if src.is_dir():
        src_is_dir = True
        src_files = listfile(src, pattern=pattern, is_r=is_r)
    else:
        if src.suffix not in _support_types:
            raise ValueError('only supported: %s' % _support_types)
        src_files = [src]
    if not dst:
        dst_dir = src.absolute() if src_is_dir else src.absolute().parent
    else:
        dst_dir = Path(dst).absolute()
        dst_dir.mkdir(parents=True, exist_ok=True)
    dst_dir.chmod(stat.S_IRWXU)
    count = 0
    for src_file in src_files:
        file_name, file_type = src_file.name, src_file.suffix
        if file_type:
            file_type = file_type.lower()
            if file_type not in _support_types:
                continue
        else:
            continue
        try:
            if file_type == '.zip':
                zip_file = zipfile.ZipFile(src_file)
                for f in zip_file.namelist():
                    zip_file.extract(f, dst_dir)
                zip_file.close()
            elif file_type == '.rar':
                rar_file = rarfile.RarFile(src_file)
                rar_file.extractall(dst_dir)
                rar_file.close()
            else:
                tar_file = tarfile.open(src_file)
                for name in tar_file.getnames():
                    tar_file.extract(name, dst_dir)
                tar_file.close()
        except Exception:
            if is_raise is True:
                raise
            else:
                traceback.print_exc()
        else:
            count += 1
    return count
