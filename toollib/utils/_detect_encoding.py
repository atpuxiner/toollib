from pathlib import Path

import chardet


def detect_encoding(
        data_or_path: bytes | str | Path,
        size: int = 8192,
        retry_size: int = 32768,
        confidence: float = 0.8,
        default: str = 'utf-8'
) -> str:
    """
    检测编码

    e.g.::

        encoding = utils.detect_encoding('中中中文'.encode('gbk'))

        +++++[更多详见参数或源码]+++++

    :param data_or_path: 数据或路径
    :param size: 大小
    :param retry_size: 重试大小
    :param confidence: 置信度
    :param default: 默认值
    :return:
    """

    def _read_bytes(n: int | None) -> bytes:
        if isinstance(data_or_path, bytes):
            return data_or_path if n is None else data_or_path[:n]
        elif isinstance(data_or_path, (str, Path)):
            if not Path(data_or_path).is_file():
                return b''
            with open(data_or_path, 'rb') as f:
                return f.read() if n is None else f.read(n)
        return b''

    def _detect_from_bytes(b: bytes) -> str | None:
        if not b:
            return None
        res = chardet.detect(b)
        if res.get('encoding') and res.get('confidence', 0) >= confidence:
            return res['encoding']
        return None

    if encoding := _detect_from_bytes(_read_bytes(size)):
        return encoding
    if retry_size is not None and retry_size <= size:
        return default
    return _detect_from_bytes(_read_bytes(retry_size)) or default
