import csv
import warnings
from typing import Generator

from toollib.utils import detect_encoding


def read_csv(
        filepath: str,
        column_names: list[str] = None,
        min_rows: int = None,
        max_rows: int = None,
        encoding: str = None,
) -> Generator[tuple[int, dict], None, None]:
    """
    读取 csv 文件

    e.g.::

        for idx, row in utils.read_csv(r'E:\tmp.csv'):
            print(idx, row)

        +++++[更多详见参数或源码]+++++

    :param filepath: 文件路径
    :param column_names: 列名称
    :param min_rows: 最小行
    :param max_rows: 最大行
    :param encoding: 编码
    :return:
    """
    encoding = encoding or detect_encoding(filepath)
    with open(filepath, 'r', encoding=encoding, newline='') as file:
        reader = csv.DictReader(file)
        actual_headers = reader.fieldnames
        if actual_headers is None:
            warnings.warn("No rows found in the file.")
            return
        final_columns: list[str] = column_names if column_names is not None else actual_headers
        for idx, row_dict in enumerate(reader):
            if idx < (min_rows or 0) - 1:
                continue
            if max_rows is not None and idx >= max_rows:
                break
            output_row = {}
            for col_name in final_columns:
                if col_name in actual_headers:
                    output_row[col_name] = row_dict.get(col_name)
                else:
                    output_row[col_name] = None
            yield idx, output_row
