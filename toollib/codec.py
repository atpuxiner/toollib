"""
@author axiner
@version v1.0.0
@created 2024/2/28 10:20
@abstract 编码
@description
@history
"""
import encodings
import re
import typing as t

__all__ = ["detect_encoding"]

# 常见编码配置
COMMON_ENCODINGS = [
    "utf-8",  # 无BOM的UTF-8编码，支持全球大多数语言的字符，常用于国际化和跨平台应用。
    "utf-8-sig",  # 带有BOM（字节顺序标记）的UTF-8编码，通常用于Windows系统中，确保文件以UTF-8格式打开。
    "utf-16",  # UTF-16编码，使用16位编码表示字符，支持全球大多数语言的字符，常用于Windows系统和某些应用程序。
    "utf-32",  # UTF-32编码，使用32位编码表示字符，支持全球大多数语言的字符，但文件体积较大，使用较少。
    "gb18030",  # 中文扩展编码，支持简体中文、繁体中文以及少数民族文字，是中国国家标准。
    "gbk",  # 中文扩展编码，支持简体中文和繁体中文，是GB2312的扩展。
    "gb2312",  # 简体中文编码，支持简体中文字符，是中国早期的国家标准。
    "big5",  # 繁体中文编码，主要用于台湾、香港和澳门地区，支持繁体中文字符。
    "iso-8859-1",  # 西欧编码，支持英语、法语、德语等西欧语言的字符，常用于早期的Web页面。
    "shift_jis",  # 日文编码，支持日文字符，常用于日本地区的系统和应用程序。
    "euc-kr",  # 韩文编码，支持韩文字符，常用于韩国地区的系统和应用程序。
    "ks_c_5601-1987",  # 韩文编码，也称为CP949，是韩国的标准编码，支持韩文字符。
    "cp1252",  # Windows-1252编码，支持西欧语言的字符，是Windows系统默认的ANSI编码。
    "ascii",  # ASCII编码，支持基本的英文字符、数字和符号，是最早的字符编码标准。
]

# 常见BOM映射
BOM_MAP = {
    b'\xef\xbb\xbf': 'utf-8-sig',  # UTF-8 BOM
    b'\xff\xfe': 'utf-16-le',  # UTF-16 LE
    b'\xfe\xff': 'utf-16-be',  # UTF-16 BE
    b'\xff\xfe\x00\x00': 'utf-32-le',  # UTF-32 LE
    b'\x00\x00\xfe\xff': 'utf-32-be',  # UTF-32 BE
}

# 生成全量编码列表
_EXTRA_ENCODINGS = sorted(
    {enc for enc in encodings.aliases.aliases.values() if enc not in COMMON_ENCODINGS},
    key=lambda x: (not x.startswith('iso-8859'), x)
)
ALL_ENCODINGS = COMMON_ENCODINGS + _EXTRA_ENCODINGS

# 预编译正则表达式（用于快速检测汉字）
HANZI_PATTERN = re.compile(
    r'[\u4E00-\u9FFF\u3400-\u4DBF\U00020000-\U0002A6DF\U0002A700-\U0002B739\U0002B740-\U0002B81D]'
)

# 常见中文符号
COMMON_SYMBOLS = {'，', '。', '？', '！', '、', '；', '：', '“', '”', '（', '）', '【', '】', '《', '》'}


def detect_encoding(
        data_or_path: t.Union[bytes, str],
        default: str = "utf-8",
        sample_size: int = 8192
) -> str:
    """
    编码检测

    e.g.::

        enc = detect_encoding('foo.txt')

        +++++[更多详见参数或源码]+++++

    :param data_or_path: 数据或路径
    :param default: 默认值
    :param sample_size: 采样大小
    :return:
    """
    data = _read_data_source(data_or_path, sample_size)
    if not data:
        return default
    # 阶段1：BOM检测
    if bom_enc := _detect_bom(data):
        return bom_enc
    # 阶段2：候选编码
    candidates = _get_candidate_encodings(data)
    if candidates:
        # 阶段3：优选结果
        best_enc, max_score = max(candidates, key=lambda x: x[1])
        if max_score > 30:  # 最低置信度阈值
            return best_enc
    # 阶段4：智能回退
    fallback_enc = _final_fallback(data, default)
    return fallback_enc


def _read_data_source(
        source: t.Union[bytes, str],
        sample_size: int
) -> bytes:
    """优化采样策略（侧重头部）"""
    if isinstance(source, bytes):
        return source[:sample_size]

    if isinstance(source, str) and len(source) <= 4096:
        try:
            with open(source, 'rb') as f:
                f.seek(0, 2)
                file_size = f.tell()
                f.seek(0)
                if file_size <= sample_size:
                    return f.read()
                # 调整采样比例：头部50%，中间30%，尾部20%
                head_size = min(sample_size // 2, 4096)
                mid_size = min(int(sample_size * 0.3), 2048)
                tail_size = sample_size - head_size - mid_size
                head = f.read(head_size)
                f.seek(max(0, (file_size - mid_size) // 2))
                middle = f.read(mid_size)
                f.seek(max(0, file_size - tail_size))
                tail = f.read(tail_size)
                return (head + middle + tail)[:sample_size]
        except (OSError, FileNotFoundError):
            pass
    return b''


def _detect_bom(data: bytes) -> t.Optional[str]:
    """BOM检测"""
    for bom, enc in sorted(BOM_MAP.items(), key=lambda x: (-len(x[0]), x)):
        if data.startswith(bom):
            return enc
    return None


def _get_candidate_encodings(data: bytes) -> t.List[t.Tuple[str, int]]:
    """获取候选编码"""
    candidates = []
    for enc in ALL_ENCODINGS:
        try:
            decoded = data.decode(enc)
            valid, stats = _validate_and_collect(decoded, enc)
            if valid:
                score = _calculate_confidence(stats, decoded, enc)
                candidates.append((enc, score))
        except (UnicodeDecodeError, LookupError):
            continue
    return candidates


def _validate_and_collect(text: str, encoding: str) -> t.Tuple[bool, dict]:
    """验证解码并收集统计信息"""
    stats = {
        'hanzi': 0,
        'symbols': 0,
        'jp_chars': 0,
        'ko_chars': 0,
        'errors': set()
    }
    # 快速检测汉字
    hanzi_matches = HANZI_PATTERN.findall(text)
    stats['hanzi'] = len(hanzi_matches)
    has_chinese = stats['hanzi'] > 0
    # 符号检测
    stats['symbols'] = len(COMMON_SYMBOLS & set(text))
    has_symbols = stats['symbols'] > 0
    # 编码特定检测
    if encoding == 'utf-8':
        errors = _has_gb_errors(text)
        valid = (has_chinese or has_symbols) and not errors
        stats['errors'] = errors
    elif encoding in ('gb18030', 'gbk', 'gb2312'):
        errors = _has_utf8_errors(text)
        valid = (has_chinese or has_symbols) and not errors
        stats['errors'] = errors
    elif encoding == 'shift_jis':
        stats['jp_chars'] = sum(0x3040 <= ord(c) <= 0x30FF for c in text)
        valid = stats['jp_chars'] > 0
    elif encoding == 'utf-16':
        stats['ko_chars'] = sum(0xAC00 <= ord(c) <= 0xD7A3 for c in text)
        valid = stats['ko_chars'] > 0
    else:
        valid = has_chinese or has_symbols or len(text) > 0
    return valid, stats


def _calculate_confidence(stats: dict, text: str, encoding: str) -> int:
    """计算评分"""
    score = 0
    # 长度奖励
    score += min(len(text) // 10, 20)
    # 中文特征
    score += min(stats['hanzi'] * 2, 30)
    # 符号奖励
    score += stats['symbols'] * 3
    # 编码特性
    if encoding == 'utf-8':
        score += len([c for c in text if 0xAC00 <= ord(c) <= 0xD7A3])  # 韩文兼容
    elif encoding.startswith('gb'):
        score += sum(1 for c in text if c in {'·', '—', '…'}) * 5
    elif encoding == 'shift_jis':
        score += stats['jp_chars'] * 3
    # 错误惩罚
    score -= len(stats['errors']) * 10
    return max(score, 0)


def _has_gb_errors(text: str) -> set:
    """扩展GB系列错误字符"""
    return {c for c in text if c in {'脗', '脙', '脛', '驴', '脌', 'Ã', 'Â', 'Å', '˜'}}


def _has_utf8_errors(text: str) -> set:
    """扩展UTF-8错误字符"""
    return {c for c in text if c in {'ï', '¿', '»', 'â', '¬', '©', '®'}}


def _final_fallback(data: bytes, default: str) -> str:
    """增强回退策略"""
    # 尝试常见单字节编码
    for enc in ['utf-8', 'iso-8859-1', 'cp1252', 'gbk', 'big5']:
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return default if all(b < 128 for b in data) else 'iso-8859-1'
