"""
@author axiner
@version v1.0.0
@created 2022/1/23 20:36
@abstract
@description
@history
"""
import typing as t

try:
    from openpyxl.worksheet.worksheet import Worksheet
except ImportError:
    raise

__all__ = [
    "inserts",
    "rows_value",
    "cols_value",
]


def inserts(ws: Worksheet, values: t.List[list], index: int = None,
            mode: str = "r", is_new: bool = True):
    """
    插入数据
    :param ws: Worksheet实例（openpyxl库）
    :param values: 值（eg: [[1, 2, 3], [4, 5, 6]]）
    :param index: 从哪开始插入值，若为None则追加
    :param mode: 插入模式（r: 插入行值，c: 插入列值）
    :param is_new: 是否插入新的行|列（True: 是，False: 否，若有值则会覆盖）
    :return:
    """
    _len = len(values)
    if mode not in ["r", "c"]:
        raise ValueError("'mode' only select from: ['r', 'c']")
    if index is None and mode == "c":
        index = ws.max_column + 1
    if index is not None:
        if isinstance(index, int):
            if index < 1:
                raise ValueError("'index' greater than 0")
        else:
            raise ValueError("'index' only supported: int")
        if is_new is True:
            if mode == "r":
                ws.insert_rows(index, _len)
            else:
                ws.insert_cols(index, _len)
        for r, item in enumerate(values):
            _i = r + index
            for c, v in enumerate(item, 1):
                if mode == "r":
                    _r, _c = _i, c
                else:
                    _r, _c = c, _i
                ws.cell(_r, _c, v)
    else:
        for item in values:
            ws.append(item)


def rows_value(ws: Worksheet):
    """
    所有行的值
    :param ws: Worksheet实例（openpyxl库）
    :return:
    """
    for item in ws.rows:
        yield [r.value for r in item]


def cols_value(ws: Worksheet):
    """
    所有列的值
    :param ws: Worksheet实例（openpyxl库）
    :return:
    """
    for item in ws.columns:
        yield [c.value for c in item]
