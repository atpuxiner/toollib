import csv
import itertools
import warnings
from pathlib import Path
from typing import Generator, Literal
from toollib.utils import detect_encoding


def split_csv(
        filepath: str,
        max_rows: int,
        max_files: int = None,
        output_dir: str = None,
        part_sep: str = "_",
        part_prefix: str = "",
        part_zfill: int = 3,
        part_pos: Literal["after", "before"] = "after",
        encoding: str = None,
) -> Generator[str, None, None]:
    """
    分割 csv 文件

    e.g.::

        for p in utils.split_csv(r'E:\tmp.csv'):
            print(p)

        +++++[更多详见参数或源码]+++++

    :param filepath: 文件路径
    :param max_rows: 最大行数
    :param max_files: 最大文件数
    :param output_dir: 输出目录
    :param part_sep: part分隔符
    :param part_prefix: part前缀
    :param part_zfill: part补零数
    :param part_pos: part编号位置
    :param encoding: 编码
    :yields:
    """
    if max_rows <= 0:
        raise ValueError("max_rows must be a positive integer.")
    if max_files is not None and max_files <= 0:
        raise ValueError("max_files must be a positive integer or None.")

    src_path = Path(filepath)
    if not src_path.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")

    output_dir = Path(output_dir) if output_dir else src_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    encoding = encoding or detect_encoding(str(src_path))
    with open(src_path, 'r', encoding=encoding, newline='') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            warnings.warn("No rows found in the file.")
            return

        file_index = 0
        while True:
            if max_files is not None and file_index >= max_files:
                break
            part_name = f"{part_prefix}{str(file_index + 1).zfill(part_zfill)}"
            if part_pos == "after":
                file_name = f"{src_path.stem}{part_sep}{part_name}{src_path.suffix}"
            else:
                file_name = f"{part_name}{part_sep}{src_path.stem}{src_path.suffix}"
            out_path = output_dir / file_name
            written_rows = 0
            with open(out_path, 'w', encoding=encoding, newline='') as out_f:
                writer = csv.writer(out_f)
                writer.writerow(header)
                for row in itertools.islice(reader, max_rows):
                    writer.writerow(row)
                    written_rows += 1
            if written_rows == 0:
                break
            yield str(out_path)
            file_index += 1
