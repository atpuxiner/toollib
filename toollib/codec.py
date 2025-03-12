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
    "utf_8",
    "utf_8_sig",
    "utf_16",
    "utf_16_le",
    "utf_16_be",
    "utf_32",
    "utf_32_le",
    "utf_32_be",
    "gbk",  # 中
    "gb18030",
    "gb2312",
    "big5",
    "ascii",  # 西欧
    "latin_1",
    "cp1252",
    "mac_roman",
    "shift_jis",  # 日
    "euc_jp",
    "iso2022_jp",
    "euc_kr",  # 韩
    "cp949",
]

# 生成全量编码列表
EXTRA_ENCODINGS = list({enc for enc in encodings.aliases.aliases.values() if enc not in COMMON_ENCODINGS})
ALL_ENCODINGS = COMMON_ENCODINGS + EXTRA_ENCODINGS

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
    # 候选编码
    candidates = _get_candidate_encodings(data)
    if candidates:
        # 优选结果
        best_enc, max_score = max(candidates, key=lambda x: x[1])
        if max_score > 30:  # 最低置信度阈值
            return best_enc
    # 智能回退
    fallback_enc = _final_fallback(data, default)
    return fallback_enc


def _read_data_source(
        source: t.Union[bytes, str],
        sample_size: int
) -> bytes:
    """优化采样策略"""
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
                # 采样比例默认：头部50%，中间30%，尾部20%
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


def _get_candidate_encodings(data: bytes) -> t.List[t.Tuple[str, int]]:
    """获取候选编码"""
    candidates = []
    _data_head = data[:10]
    for enc in ALL_ENCODINGS:
        if enc == 'utf_8_sig' and not _data_head.startswith(b'\xef\xbb\xbf'):
            continue
        if enc == 'utf_16' and not (_data_head.startswith(b'\xff\xfe') or _data_head.startswith(b'\xfe\xff')):
            continue
        if enc == 'utf_16_le' and not _data_head.startswith(b'\xff\xfe'):
            continue
        if enc == 'utf_16_be' and not _data_head.startswith(b'\xfe\xff'):
            continue
        if enc == 'utf_32' and not (_data_head.startswith(b'\xff\xfe\x00\x00') or _data_head.startswith(b'\x00\x00\xfe\xff')):
            continue
        if enc == 'utf_32_le' and not _data_head.startswith(b'\xff\xfe\x00\x00'):
            continue
        if enc == 'utf_32_be' and not _data_head.startswith(b'\x00\x00\xfe\xff'):
            continue
        try:
            text = data.decode(enc)
            valid, stats = _validate_and_collect(text, enc)
            if valid:
                score = _calculate_confidence(stats, text, enc, data=data)
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
    if encoding == 'utf_8':
        errors = _has_gb_errors(text)
        valid = (has_chinese or has_symbols) and not errors
        stats['errors'] = errors
    elif encoding in ('gbk', 'gb18030', 'gb2312'):
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


def _calculate_confidence(stats: dict, text: str, encoding: str, data: bytes) -> int:
    """计算置信度"""
    score = 0
    # 长度奖励
    score += min(len(text) // 10, 20)
    # 中文特征
    score += min(stats['hanzi'] * 2, 30)
    # 符号奖励
    score += stats['symbols'] * 3
    # 编码特性
    if encoding == 'utf_8':
        score += 20
        # Unicode 特殊符号（如 emoji、数学符号等）
        unicode_symbols = sum(0x2000 <= ord(c) <= 0x2BFF for c in text)
        score += unicode_symbols * 15
        # UTF-8 中文字符的字节分布（通常以 0xE0 到 0xEF 开头）
        byte_distribution = _get_byte_distribution(data)
        utf8_hanzi_bytes = sum(count for byte, count in byte_distribution.items() if 0xE0 <= byte <= 0xEF)
        score += utf8_hanzi_bytes * 10
        # 检测 BOM（字节顺序标记）
        if data.startswith(b'\xef\xbb\xbf'):
            score += 50
    elif encoding.startswith('gb'):
        if encoding == 'gbk':
            score += 10
        # 中文符号（如 ·、—、…）
        chinese_symbols = sum(c in {'·', '—', '…'} for c in text)
        score += chinese_symbols * 8
        # GB 中文字符的字节分布（通常以 0x81 到 0xFE 开头）
        byte_distribution = _get_byte_distribution(data)
        gb_hanzi_bytes = sum(count for byte, count in byte_distribution.items() if 0x81 <= byte <= 0xFE)
        score += gb_hanzi_bytes * 3
    elif encoding == 'shift_jis':
        # 日文假名（如 あ、ア）
        jp_chars = sum(0x3040 <= ord(c) <= 0x30FF for c in text)
        score += jp_chars * 3
    elif encoding == 'euc_kr':
        # 韩文字符（如 가、나）
        ko_chars = sum(0xAC00 <= ord(c) <= 0xD7A3 for c in text)
        score += ko_chars * 3
    # 错误惩罚
    score -= len(stats['errors']) * 20
    return max(score, 0)


def _get_byte_distribution(data: bytes) -> dict:
    """获取字节分布"""
    distribution = {}
    for byte in data:
        distribution[byte] = distribution.get(byte, 0) + 1
    return distribution


def _has_gb_errors(text: str) -> set:
    """扩展GB系列错误字符"""
    return {c for c in text if c in {'脗', '脙', '脛', '驴', '脌', 'Ã', 'Â', 'Å', '˜'}}


def _has_utf8_errors(text: str) -> set:
    """扩展UTF-8错误字符"""
    return {c for c in text if c in {'ï', '¿', '»', 'â', '¬', '©', '®'}}


def _final_fallback(data: bytes, default: str) -> str:
    """增强回退策略"""
    # 尝试常见单字节编码
    for enc in ['utf_8', 'latin_1', 'cp1252', 'gbk', 'big5']:
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return default if all(b < 128 for b in data) else 'latin_1'
