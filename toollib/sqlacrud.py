"""
@author axiner
@version v1.1.0
@created 2026/2/8 10:00
@abstract SQLAlchemy 异步 CRUD 工具库（支持 PostgreSQL、MySQL、SQLite）
@description
- 提供查询、统计、增删改、upsert、批量插入与原生 SQL 执行的异步函数
- CRUDMixin 可集成到模型类
@history
- v1.1.0 生产级加固：原子冲突处理、显式事务语义、SQLAlchemy 2.x 批量插入、列映射兼容与唯一键约束校验
- v1.0.0 初始版本
"""

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, TypeAlias

from sqlalchemy import (
    ClauseElement,
    ColumnElement,
    UniqueConstraint,
    func,
    inspect,
    select,
    text,
)
from sqlalchemy import (
    delete as sa_delete,
)
from sqlalchemy import (
    insert as sa_insert,
)
from sqlalchemy import (
    update as sa_update,
)
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = [
    "Created",
    "Deleted",
    "Updated",
    "Upserted",
    "BatchCreated",
    "BulkInserted",
    "format_row",
    "format_rows",
    "fetch_one",
    "fetch_all",
    "count",
    "create",
    "delete",
    "update",
    "upsert",
    "batch_create",
    "bulk_insert",
    "raw",
    "CRUDMixin",
]

WhereClause: TypeAlias = Mapping[str, Any] | ClauseElement | Iterable[ClauseElement] | None
OrderBy: TypeAlias = str | ClauseElement | Iterable[str | ClauseElement] | None

_NATIVE_INSERT_DIALECTS = frozenset({"postgresql", "mysql", "sqlite"})


# -----------------------------------------------------------------------------
# 返回类型定义
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Created:
    """`create()` 的返回结果。

    Attributes:
        ok: 是否创建成功；`on_conflict` 命中时为 False。
        rowcount: 创建结果计数，成功为 1，冲突为 0；回退路径未 flush 时表示计划创建数，
            不等同于数据库实际 affected rows。
        data: 成功时为新建数据；冲突时为已存在数据；`returning=False` 且成功时为 None。

    可用 `if result:` 直接判断，语义等价于 `if result.ok:`。
    """

    ok: bool
    rowcount: int = 0
    data: dict[str, Any] | None = None

    def __bool__(self) -> bool:
        return self.ok


@dataclass(frozen=True, slots=True)
class Deleted:
    """`delete()` 的返回结果。

    Attributes:
        ok: 是否实际删除了记录，等价于 `rowcount > 0`。
        rowcount: 删除的行数；未命中记录时为 0。
    """

    ok: bool
    rowcount: int = 0

    def __bool__(self) -> bool:
        return self.ok


@dataclass(frozen=True, slots=True)
class Updated:
    """`update()` 的返回结果。

    Attributes:
        ok: 是否实际更新了记录，等价于 `rowcount > 0`。
        rowcount: 受影响的行数；没有可更新字段或未命中记录时为 0。
            MySQL 默认不统计“值未变化”的更新，此时可能为 0，而 PostgreSQL/SQLite 通常为 1。
        data: `returning=True` 且命中记录时为更新后的数据，否则为 None。
    """

    ok: bool
    rowcount: int = 0
    data: dict[str, Any] | None = None

    def __bool__(self) -> bool:
        return self.ok


@dataclass(frozen=True, slots=True)
class Upserted:
    """`upsert()` 的返回结果。

    Attributes:
        ok: 是否实际写入或更新了记录，等价于 `rowcount > 0`。
        rowcount: 受影响行数；方言对“无变化更新”的计数可能不同。
        data: `returning=True` 时为操作后的数据，否则为 None。
    """

    ok: bool
    rowcount: int = 0
    data: dict[str, Any] | None = None

    def __bool__(self) -> bool:
        return self.ok


@dataclass(frozen=True, slots=True)
class BatchCreated:
    """`batch_create()` 的返回结果。

    Attributes:
        ok: 是否全部创建成功；成功时为 True。
        rowcount: 实际创建的记录数。
        data: `returning=True` 时的创建结果列表，否则为空列表。
    """

    ok: bool
    rowcount: int = 0
    data: list[dict[str, Any]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok


@dataclass(frozen=True, slots=True)
class BulkInserted:
    """`bulk_insert()` 的返回结果。

    Attributes:
        ok: 是否成功执行批量插入；成功时为 True。
        rowcount: 实际插入的行数。
        data: `return_defaults=True` 时包含数据库生成值的数据列表，否则为空列表。
            PostgreSQL/SQLite 返回完整行；MySQL 等方言只保证补充主键。
    """

    ok: bool
    rowcount: int = 0
    data: list[dict[str, Any]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok


# -----------------------------------------------------------------------------
# 内部工具函数
# -----------------------------------------------------------------------------


def _mapper(model: Any):
    inspected = inspect(model, raiseerr=False)
    mapper = getattr(inspected, "mapper", None)
    if mapper is None:
        raise TypeError(f"{model!r} is not a mapped class or instance")
    return mapper


def _model_name(model: Any) -> str:
    return getattr(model, "__name__", type(model).__name__)


def _dialect(session: AsyncSession, model: Any | None = None) -> str:
    bind = session.get_bind(mapper=model) if model is not None else session.get_bind()
    return getattr(getattr(bind, "dialect", None), "name", "unknown")


def _rowcount(result: Any) -> int:
    return max(getattr(result, "rowcount", 0) or 0, 0)


def _column_keys(model: Any) -> list[str]:
    return list(_mapper(model).columns.keys())


def _resolve_column_key(model: Any, name: str) -> str:
    mapper = _mapper(model)
    if not isinstance(name, str):
        raise TypeError(f"Column name must be str, got {type(name).__name__}")
    if name in mapper.columns:
        return name
    for key, column in mapper.columns.items():
        if column.name == name:
            return key
    raise ValueError(f"Invalid column '{name}' for model {_model_name(model)}")


def _resolve_column_keys(model: Any, names: Iterable[str], label: str) -> tuple[str, ...]:
    if isinstance(names, (str, bytes)):
        names = (names,)
    return tuple(_resolve_column_key(model, name) for name in names)


def _normalize_values(model: Any, values: Mapping[str, Any], label: str = "values") -> dict[str, Any]:
    if not isinstance(values, Mapping):
        raise TypeError(f"'{label}' must be a mapping, got {type(values).__name__}")

    normalized: dict[str, Any] = {}
    for key, value in values.items():
        column_key = _resolve_column_key(model, key)
        if column_key in normalized:
            raise ValueError(f"'{label}' contains duplicate column: {column_key}")
        normalized[column_key] = value
    return normalized


def _db_column_key_map(model: Any) -> dict[str, str]:
    return {key: column.key for key, column in _mapper(model).columns.items()}


def _normalize_db_values(model: Any, values: Mapping[str, Any], label: str = "values") -> dict[str, Any]:
    key_map = _db_column_key_map(model)
    return {key_map[key]: value for key, value in _normalize_values(model, values, label).items()}


def _normalize_db_value_rows(model: Any, values: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"'values' must be a sequence of mappings, got {type(values).__name__}")

    rows: list[dict[str, Any]] = []
    for index, row in enumerate(values):
        normalized = _normalize_db_values(model, row, f"values[{index}]")
        if not normalized:
            raise ValueError(f"'values[{index}]' must contain at least one column")
        rows.append(normalized)
    return rows


def _normalize_value_rows(model: Any, values: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"'values' must be a sequence of mappings, got {type(values).__name__}")
    return [_normalize_values(model, row, f"values[{index}]") for index, row in enumerate(values)]


def _select_columns(model: Any, columns: Sequence[str] | None) -> tuple[tuple[ColumnElement[Any], ...], list[str]]:
    keys = _column_keys(model)
    if not columns:
        selected = tuple(getattr(model, key).label(key) for key in keys)
        return selected, keys

    if isinstance(columns, (str, bytes)):
        raise TypeError("'columns' must be a sequence of column names")

    selected = []
    labels: list[str] = []
    seen: set[str] = set()
    for column in columns:
        key = _resolve_column_key(model, column)
        if key in seen:
            raise ValueError(f"'columns' contains duplicate column: {key}")
        seen.add(key)
        selected.append(getattr(model, key).label(column))
        labels.append(column)
    return tuple(selected), labels


def _build_where_clauses(model: Any, where: WhereClause) -> list[ClauseElement]:
    if where is None:
        return []

    if isinstance(where, Mapping):
        conditions: list[ClauseElement] = []
        seen: set[str] = set()
        for key, value in where.items():
            column_key = _resolve_column_key(model, key)
            if column_key in seen:
                raise ValueError(f"'where' contains duplicate column: {column_key}")
            seen.add(column_key)
            conditions.append(getattr(model, column_key) == value)
        return conditions

    if isinstance(where, ClauseElement):
        return [where]

    if not isinstance(where, (str, bytes)) and isinstance(where, Iterable):
        conditions = list(where)
        for index, expr in enumerate(conditions):
            if not isinstance(expr, ClauseElement):
                raise TypeError(f"where[{index}] is not a SQLAlchemy ClauseElement: {expr!r}")
        return conditions

    raise TypeError(f"Unsupported where type: {type(where).__name__}")


def _to_dict(model: Any, columns: Sequence[str] | None = None) -> dict[str, Any]:
    if model is None:
        return {}
    keys = _resolve_column_keys(model, columns, "columns") if columns else _column_keys(model)
    return {key: getattr(model, key) for key in keys if hasattr(model, key)}


def _parse_order_by(model: Any, order_by: OrderBy) -> list[ClauseElement]:
    if order_by is None:
        return []

    if isinstance(order_by, ClauseElement):
        return [order_by]

    if isinstance(order_by, str):
        items: Iterable[str | ClauseElement] = (order_by,)
    elif not isinstance(order_by, (str, bytes)) and isinstance(order_by, Iterable):
        items = order_by
    else:
        raise TypeError(f"Unsupported order_by type: {type(order_by).__name__}")

    result: list[ClauseElement] = []
    for item in items:
        if isinstance(item, ClauseElement):
            result.append(item)
            continue
        if not isinstance(item, str):
            raise TypeError(f"order_by item must be str or ClauseElement, got {type(item).__name__}")

        descending = item.startswith("-")
        name = item[1:] if descending else item
        if not name:
            raise ValueError("order_by column name cannot be empty")
        column = getattr(model, _resolve_column_key(model, name))
        result.append(column.desc() if descending else column.asc())
    return result


def _column_key_map(model: Any) -> dict[int, str]:
    return {id(column): key for key, column in _mapper(model).columns.items()}


def _mapped_key_list(model: Any, columns: Iterable[Any]) -> tuple[str, ...]:
    key_map = _column_key_map(model)
    return tuple(key_map[id(column)] for column in columns if id(column) in key_map)


def _mapped_keys(model: Any, columns: Iterable[Any]) -> set[str]:
    return set(_mapped_key_list(model, columns))


def _primary_key_keys(model: Any) -> tuple[str, ...]:
    return _mapped_key_list(model, _mapper(model).primary_key)


def _unique_key_sets(model: Any) -> list[frozenset[str]]:
    mapper = _mapper(model)
    sets: list[frozenset[str]] = []

    primary_keys = _primary_key_keys(model)
    if primary_keys:
        sets.append(frozenset(primary_keys))

    for key, column in mapper.columns.items():
        if column.unique:
            sets.append(frozenset({key}))

    for constraint in mapper.local_table.constraints:
        if not isinstance(constraint, UniqueConstraint):
            continue
        keys = _mapped_keys(model, constraint.columns)
        if keys:
            sets.append(frozenset(keys))

    for index in mapper.local_table.indexes:
        if not index.unique:
            continue
        keys = _mapped_keys(model, index.columns)
        if keys:
            sets.append(frozenset(keys))
    return sets


def _is_unique_key_set(model: Any, keys: Sequence[str]) -> bool:
    key_set = frozenset(keys)
    return any(unique_keys <= key_set for unique_keys in _unique_key_sets(model))


def _matches_unique_key(model: Any, keys: Sequence[str]) -> bool:
    return frozenset(keys) in _unique_key_sets(model)


def _create_conflict_stmt(
    model: Any,
    values: Mapping[str, Any],
    keys: Sequence[str],
    dialect: str,
):
    if dialect == "mysql":
        return mysql_insert(model).values(**values).prefix_with("IGNORE")
    stmt = pg_insert(model) if dialect == "postgresql" else sqlite_insert(model)
    return stmt.values(**values).on_conflict_do_nothing(index_elements=[getattr(model, key) for key in keys])


def _upsert_stmt(
    model: Any,
    values: Mapping[str, Any],
    keys: Sequence[str],
    update_data: Mapping[str, Any],
    dialect: str,
):
    if dialect == "mysql":
        stmt = mysql_insert(model).values(**values)
        if update_data:
            return stmt.on_duplicate_key_update(**update_data)
        noop_key = next(iter(values))
        return stmt.on_duplicate_key_update(**{noop_key: values[noop_key]})

    stmt = pg_insert(model) if dialect == "postgresql" else sqlite_insert(model)
    stmt = stmt.values(**values)
    index_elements = [getattr(model, key) for key in keys]
    if update_data:
        return stmt.on_conflict_do_update(index_elements=index_elements, set_=dict(update_data))
    return stmt.on_conflict_do_nothing(index_elements=index_elements)


# -----------------------------------------------------------------------------
# 格式化操作
# -----------------------------------------------------------------------------


def format_row(
    row: Any,
    columns: Sequence[str],
    converters: dict[str, Callable[..., Any]] | None = None,
) -> dict[str, Any]:
    """把一行 SQLAlchemy 结果格式化为 dict。

    Args:
        row: `fetchone()` 返回的行；支持 `_mapping`、`_asdict()` 或按 `columns` 顺序解包的可迭代对象。
             None 时返回空 dict。
        columns: 列名顺序，用作回退解包顺序及结果键名。可传 ORM 属性名或数据库列名。
        converters: 字段转换函数，如 `{"created_at": lambda v: v.isoformat()}`；仅转换结果中存在的键。

    Returns:
        单行数据 dict；`row is None` 时为 `{}`。

    e.g.::

        row = await session.execute(select(User.id))
        format_row(row.fetchone(), ["id"], {"id": str})
    """
    if row is None:
        return {}
    if hasattr(row, "_mapping"):
        data = dict(row._mapping)
    elif hasattr(row, "_asdict"):
        data = row._asdict()
    else:
        data = dict(zip(columns, row, strict=False))
    if converters:
        for key, converter in converters.items():
            if key in data:
                data[key] = converter(data[key])
    return data


def format_rows(
    rows: Iterable[Any] | None,
    columns: Sequence[str],
    converters: dict[str, Callable[..., Any]] | None = None,
) -> list[dict[str, Any]]:
    """把多行 SQLAlchemy 结果格式化为 dict 列表。

    Args:
        rows: `fetchall()` 返回的行序列；None 时返回空列表。
        columns: 列名顺序，决定每行 dict 的键名；行对象支持 `_mapping` 时以行对象键名为准。
        converters: 字段转换函数，如 `{"created_at": lambda v: v.isoformat()}`；逐行应用，仅转换存在的键。

    Returns:
        dict 列表；空输入返回空列表。

    e.g.::

        rows = await session.execute(select(User.id, User.name))
        format_rows(rows.fetchall(), ["id", "name"])
    """
    if rows is None:
        return []
    return [format_row(row, columns, converters) for row in rows]


# -----------------------------------------------------------------------------
# 查询操作
# -----------------------------------------------------------------------------


async def fetch_one(
    session: AsyncSession,
    model,
    *,
    columns: Sequence[str] | None = None,
    where: WhereClause = None,
    order_by: OrderBy = None,
    converters: dict[str, Callable[..., Any]] | None = None,
) -> dict[str, Any] | None:
    """查询单条记录并格式化为 dict。

    Args:
        session: 异步会话。
        model: SQLAlchemy 映射类。
        columns: 指定返回列；None 或空序列表示全部列。元素可为 ORM 属性名或数据库列名。
        where: 过滤条件，支持：
            - dict：`{"name": "Tom", "age": 18}`，值为 None 时生成 IS NULL；
            - ClauseElement：`User.age >= 18`、`text("name = :n")`；
            - ClauseElement 可迭代对象：`[User.age >= 18, User.status == 1]`。
        order_by: 排序，支持 `"name"`、`"-created_at"`、`User.created_at.desc()` 或混合序列；
            不传时 LIMIT 1 的结果顺序不保证，需要确定性首行请显式排序。
        converters: 字段转换函数，如 `{"created_at": lambda v: v.isoformat()}`。

    Returns:
        单行 dict；无匹配记录时为 None。

    Raises:
        ValueError: 列名或排序字段不属于模型。
        TypeError: where/order_by 类型不受支持。

    e.g.::

        user = await fetch_one(session, User, where={"id": 1})
        user = await fetch_one(
            session, User,
            columns=["name", "created_at"],
            where=User.status == 1,
            order_by="-created_at",
            converters={"created_at": lambda value: value.isoformat()},
        )
    """
    selected, output_columns = _select_columns(model, columns)
    stmt = select(*selected).select_from(model)
    if where is not None:
        stmt = stmt.where(*_build_where_clauses(model, where))
    if order_by is not None:
        stmt = stmt.order_by(*_parse_order_by(model, order_by))

    result = await session.execute(stmt.limit(1))
    row = result.fetchone()
    return None if row is None else format_row(row, output_columns, converters)


async def fetch_all(
    session: AsyncSession,
    model,
    *,
    columns: Sequence[str] | None = None,
    where: WhereClause = None,
    order_by: OrderBy = None,
    offset: int | None = None,
    limit: int | None = None,
    converters: dict[str, Callable[..., Any]] | None = None,
) -> list[dict[str, Any]]:
    """查询多条记录并格式化为 dict 列表。

    Args:
        session: 异步会话。
        model: SQLAlchemy 映射类。
        columns: 指定返回列；None 或空序列表示全部列。元素可为 ORM 属性名或数据库列名。
        where: 过滤条件，支持：
            - dict：`{"name": "Tom", "age": 18}`，值为 None 时生成 IS NULL；
            - ClauseElement：`User.age >= 18`、`text("name = :n")`；
            - ClauseElement 可迭代对象：`[User.age >= 18, User.status == 1]`；
            - None：不过滤。
        order_by: 排序，支持 `"name"` 升序、`"-created_at"` 降序、`User.created_at.desc()`
            等 ClauseElement，或由字符串与 ClauseElement 混合组成的序列；None 表示不排序。
        offset: 分页偏移；None 时不生成 OFFSET。
        limit: 分页上限；None 时不生成 LIMIT。
        converters: 字段转换函数，如 `{"created_at": lambda v: v.isoformat()}`；仅转换结果中存在的键。

    Returns:
        行 dict 列表；无匹配记录时为空列表。

    Raises:
        ValueError: 列名或排序字段不属于模型。
        TypeError: where/order_by 类型不受支持。

    e.g.::

        users = await fetch_all(session, User, where={"status": 1}, order_by="-id", offset=20, limit=10)
    """
    selected, output_columns = _select_columns(model, columns)
    stmt = select(*selected).select_from(model)
    if where is not None:
        stmt = stmt.where(*_build_where_clauses(model, where))
    if order_by is not None:
        stmt = stmt.order_by(*_parse_order_by(model, order_by))
    if offset is not None:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return format_rows(result.fetchall(), output_columns, converters)


async def count(
    session: AsyncSession,
    model,
    *,
    where: WhereClause = None,
) -> int:
    """按条件统计记录数，常用于分页总数。

    Args:
        session: 异步会话。
        model: SQLAlchemy 映射类。
        where: 过滤条件，支持 dict（如 `{"status": 1}`，值为 None 时生成 IS NULL）、
            ClauseElement（如 `User.age >= 18` 或 `text("status = 1")`）、
            ClauseElement 可迭代对象（如 `[User.age >= 18, User.status == 1]`）；
            None 表示统计全表。

    Returns:
        符合条件的行数；数据库返回 NULL 时按 0 处理。

    Raises:
        TypeError: where 类型不受支持。
        ValueError: where dict 中的字段不属于模型。

    e.g.::

        total = await count(session, User, where={"status": 1})
    """
    stmt = select(func.count()).select_from(model)
    if where is not None:
        stmt = stmt.where(*_build_where_clauses(model, where))
    result = await session.execute(stmt)
    return result.scalar() or 0


# -----------------------------------------------------------------------------
# 增删改操作
# -----------------------------------------------------------------------------


async def create(
    session: AsyncSession,
    model,
    *,
    values: Mapping[str, Any],
    on_conflict: dict[str, Any] | None = None,
    returning: bool = True,
) -> Created:
    """创建单条记录，可选唯一键冲突时返回已存在记录。

    `on_conflict` 是“是否已存在”的等值查询条件，不是写入值，且必须等于模型声明的主键或唯一键集合。
    仅当 `values` 中对应字段与条件值一致时，PostgreSQL/SQLite 走原生 `ON CONFLICT DO NOTHING`，
    MySQL 走 `INSERT IGNORE` 以规避竞态；不一致或其他方言回退为先查后插，保持“条件是条件、值是值”的语义。
    MySQL 的 `INSERT IGNORE` 会把部分数据错误（如 NOT NULL、截断）降级为 warning，调用方应确保输入已校验。

    Args:
        session: 异步会话。
        model: SQLAlchemy 映射类。
        values: 创建数据；键可为 ORM 属性名或数据库列名。
        on_conflict: 非空唯一键等值条件，如 `{"email": "a@b.com"}`；不能包含 NULL，None 表示不做冲突检查。
        returning: 是否在成功创建时返回数据。True 时会先 flush，以便取得自增主键和服务端默认值；
            False 时成功分支不返回数据。无 `on_conflict` 时只加入会话；`on_conflict` 走原生路径时立即执行，
            回退路径只加入会话，可能延迟到调用方 flush/commit。冲突分支无论 returning 取值都会返回已存在数据。

    Returns:
        `Created`：成功时 `ok=True`、`rowcount=1`，`data` 为新建数据；
        冲突时 `ok=False`、`rowcount=0`，`data` 为已存在数据。

    Raises:
        TypeError: `values` 或 `on_conflict` 不是映射类型。
        ValueError: `on_conflict` 为空、含 NULL、字段不属于模型，或未精确匹配主键/唯一键集合。
        RuntimeError: 原生插入被其他唯一约束忽略，无法按 `on_conflict` 找到对应记录。

    e.g.::

        result = await create(session, User, values={"name": "Tom"})
        if result:
            print(result.data["id"])

        result = await create(
            session, User,
            values={"email": "a@b.com", "name": "Tom"},
            on_conflict={"email": "a@b.com"},
        )
    """
    values = _normalize_values(model, values)

    if on_conflict is not None:
        if not isinstance(on_conflict, Mapping):
            raise TypeError(f"'on_conflict' must be a mapping, got {type(on_conflict).__name__}")
        if not on_conflict:
            raise ValueError("'on_conflict' must not be empty")
        conflict = dict(on_conflict)
        conflict_keys = _resolve_column_keys(model, conflict, "on_conflict")
        conflict_values = _normalize_values(model, conflict, "on_conflict")
        if not _matches_unique_key(model, conflict_keys):
            raise ValueError("'on_conflict' must match a primary key or unique key declared on the model")
        if any(value is None for value in conflict_values.values()):
            raise ValueError("'on_conflict' values cannot be NULL")
        conflict_matches_values = all(
            key in values and values[key] == value for key, value in conflict_values.items()
        )
        dialect = _dialect(session, model)

        if dialect in _NATIVE_INSERT_DIALECTS and conflict_matches_values:
            insert_db_values = _normalize_db_values(model, values)
            result = await session.execute(_create_conflict_stmt(model, insert_db_values, conflict_keys, dialect))
            if _rowcount(result) > 0:
                row = await fetch_one(session, model, where=conflict_values) if returning else None
                return Created(ok=True, rowcount=1, data=row)

            existing = await fetch_one(session, model, where=conflict_values)
            if existing is None:
                raise RuntimeError("create was ignored by another unique constraint")
            return Created(ok=False, rowcount=0, data=existing)

        existing = await fetch_one(session, model, where=conflict_values)
        if existing is not None:
            return Created(ok=False, rowcount=0, data=existing)

    obj = model(**values)
    session.add(obj)
    if returning:
        await session.flush()
    return Created(ok=True, rowcount=1, data=_to_dict(obj) if returning else None)


async def delete(
    session: AsyncSession,
    model,
    *,
    where: WhereClause = None,
    allow_all: bool = False,
) -> Deleted:
    """按条件删除记录，默认拒绝无条件的全表删除。

    Args:
        session: 异步会话。
        model: SQLAlchemy 映射类。
        where: 过滤条件，支持 dict（如 `{"id": 1}`，值为 None 时生成 IS NULL）、
            ClauseElement（如 `User.age < 18` 或 `text("status = 0")`）、
            ClauseElement 可迭代对象（如 `[User.age < 18, User.status == 0]`）；
            None 表示全表，需配合 `allow_all=True`。
        allow_all: 是否允许无条件全表删除；为 False 且 where 为空时抛错。

    Returns:
        `Deleted`：`ok` 等价于 `rowcount > 0`；未命中记录时 rowcount 为 0。

    Raises:
        TypeError: where 类型不受支持。
        ValueError: 无 where 且未设置 `allow_all=True`，或 where dict 中的字段不属于模型。

    e.g.::

        await delete(session, User, where={"id": 1})
        await delete(session, User, where=[User.age < 18, User.status == 0])
        await delete(session, User, allow_all=True)
    """
    clauses = _build_where_clauses(model, where)
    if not clauses and not allow_all:
        raise ValueError("'where' is required, or set allow_all=True for full-table delete")

    stmt = sa_delete(model)
    if clauses:
        stmt = stmt.where(*clauses)
    rowcount = _rowcount(await session.execute(stmt))
    return Deleted(ok=rowcount > 0, rowcount=rowcount)


async def update(
    session: AsyncSession,
    model,
    *,
    values: Mapping[str, Any],
    where: WhereClause = None,
    allow_all: bool = False,
    exclude_none: bool = True,
    null_columns: Sequence[str] | None = None,
    returning: bool = False,
) -> Updated:
    """按条件更新记录，默认拒绝无条件的全表更新。

    `exclude_none=True` 会跳过值为 None 的字段；若要显式置 NULL，请设置 `exclude_none=False`
    或用 `null_columns` 指定允许置空的字段。`returning=True` 要求 `where` 为 dict，且覆盖模型声明
    的主键或唯一键（值不能为 NULL），避免多行命中时返回歧义数据；不能同时更新主键，但可以更新
    `where` 中用到的其他唯一键，返回数据会按更新前的主键重新查询。

    Args:
        session: 异步会话。
        model: SQLAlchemy 映射类。
        values: 待更新字段；键可为 ORM 属性名或数据库列名。
        where: 过滤条件，支持 dict（如 `{"id": 1}`，值为 None 时生成 IS NULL）、
            ClauseElement（如 `User.last_login < cutoff` 或 `text("status = 1")`）、
            ClauseElement 可迭代对象（如 `[User.age < 18, User.status == 1]`）；
            None 表示全表，需配合 `allow_all=True`。
        allow_all: 是否允许无条件全表更新。
        exclude_none: 是否跳过值为 None 的字段。
        null_columns: 即使 `exclude_none=True` 也允许写入 NULL 的字段名列表。
        returning: 是否查询并返回更新后的数据；不能与更新主键同时使用。

    Returns:
        `Updated`：`ok` 等价于 `rowcount > 0`；`data` 仅在 `returning=True` 且命中时有值。
        若过滤掉所有字段后无可更新内容，返回 `Updated(ok=False, rowcount=0)`。
        MySQL 默认不统计“值未变化”的更新，此时 `rowcount` 可能为 0，而 PostgreSQL/SQLite 通常为 1。

    Raises:
        TypeError: `values` 不是映射类型。
        ValueError: 无 where 且未设置 `allow_all`；returning 条件不满足；字段、null_columns 或主键更新非法。

    e.g.::

        await update(session, User, values={"name": "New"}, where={"id": 1})
        await update(
            session, User,
            values={"note": None},
            where={"id": 1},
            null_columns=["note"],
            returning=True,
        )
    """
    clauses = _build_where_clauses(model, where)
    if not clauses and not allow_all:
        raise ValueError("'where' is required, or set allow_all=True for full-table update")
    if not clauses and returning:
        raise ValueError("'returning' is not supported for full-table update")
    if returning and clauses:
        if not isinstance(where, Mapping):
            raise ValueError("'returning' requires 'where' to be a dict covering a primary key or unique key")
        lookup_keys = _resolve_column_keys(model, where, "where")
        if not _is_unique_key_set(model, lookup_keys):
            raise ValueError("'returning' requires 'where' to cover a primary key or unique key")
        if any(value is None for value in where.values()):
            raise ValueError("'returning' lookup values cannot be NULL")

    data = _normalize_values(model, values)
    null_keys = set(_resolve_column_keys(model, null_columns, "null_columns")) if null_columns else set()
    extra_null_keys = null_keys - data.keys()
    if extra_null_keys:
        raise ValueError(f"'null_columns' must be present in values: {sorted(extra_null_keys)}")
    if exclude_none:
        data = {key: value for key, value in data.items() if key in null_keys or value is not None}
    if not data:
        return Updated(ok=False, rowcount=0)

    returning_where: dict[str, Any] | None = None
    if returning:
        primary_keys = _primary_key_keys(model)
        if not primary_keys:
            raise ValueError("'returning' requires the model to declare a primary key")
        updated_primary_keys = [key for key in primary_keys if key in data]
        if updated_primary_keys:
            raise ValueError(f"'returning' cannot update primary key columns: {updated_primary_keys}")
        current = await fetch_one(session, model, where=where, columns=primary_keys)
        if current is None:
            return Updated(ok=False, rowcount=0)
        returning_where = {key: current[key] for key in primary_keys}

    stmt = sa_update(model).values(**data)
    if clauses:
        stmt = stmt.where(*clauses)
    rowcount = _rowcount(await session.execute(stmt))
    updated_data = (
        await fetch_one(session, model, where=returning_where) if returning and returning_where and rowcount > 0 else None
    )
    return Updated(ok=rowcount > 0, rowcount=rowcount, data=updated_data)


async def upsert(
    session: AsyncSession,
    model,
    *,
    values: Mapping[str, Any],
    keys: Sequence[str],
    updates: Sequence[str] | None = None,
    returning: bool = False,
) -> Upserted:
    """按唯一键执行 upsert：存在则更新，不存在则创建。

    PostgreSQL/SQLite 使用 `ON CONFLICT`，MySQL 使用 `ON DUPLICATE KEY UPDATE`（无更新字段时执行无操作更新），
    其他方言回退为先查后改。`keys` 必须存在于 `values`，且必须等于模型声明的主键或唯一键集合；
    `updates` 中若包含 `keys` 会被忽略，避免修改冲突目标列；`updates` 中的其他字段必须存在于
    `values`，且不能是主键。`rowcount` 表示
    受影响行数，方言对“无变化更新”的计数可能不同（MySQL 的 2 会归一化为 1）。

    Args:
        session: 异步会话。
        model: SQLAlchemy 映射类。
        values: 完整数据；键可为 ORM 属性名或数据库列名。
        keys: 唯一键字段名，如 `("id",)` 或 `["email"]`。
        updates: 冲突时更新的字段，必须同时存在于 values；None 表示更新除 keys 和主键外的所有字段。
        returning: 是否查询并返回操作后的数据；True 时回退路径会先 flush 以获取生成值。

    Returns:
        `Upserted`：`ok` 等价于 `rowcount > 0`；`data` 仅在 `returning=True` 时有值。

    Raises:
        TypeError: `values` 不是映射类型。
        ValueError: `keys` 为空、不在 values 中或未精确匹配主键/唯一键集合；
            `updates` 含非法列、缺失于 values 或包含主键。
        RuntimeError: 插入/更新命中了其他唯一键，无法按 `keys` 找到对应记录。

    e.g.::

        result = await upsert(
            session, User,
            values={"id": 1, "name": "Tom", "email": "tom@test.com"},
            keys=("id",),
            updates=("name",),
            returning=True,
        )
    """
    normalized = _normalize_values(model, values)
    key_columns = _resolve_column_keys(model, keys, "keys")
    if not key_columns:
        raise ValueError("'keys' must be non-empty")
    missing_keys = [key for key in key_columns if key not in normalized]
    if missing_keys:
        raise ValueError(f"'keys' must exist in values: {missing_keys}")
    if not _matches_unique_key(model, key_columns):
        raise ValueError("'keys' must match a primary key or unique key declared on the model")

    primary_keys = set(_primary_key_keys(model))
    if updates is None:
        update_columns = tuple(
            key for key in normalized if key not in key_columns and key not in primary_keys
        )
    else:
        requested_updates = _resolve_column_keys(model, updates, "updates")
        missing_updates = [key for key in requested_updates if key not in normalized]
        if missing_updates:
            raise ValueError(f"'updates' must exist in values: {missing_updates}")
        primary_updates = [key for key in requested_updates if key in primary_keys and key not in key_columns]
        if primary_updates:
            raise ValueError(f"'updates' cannot include primary key columns: {primary_updates}")
        update_columns = tuple(key for key in requested_updates if key not in key_columns)
    update_data = {key: normalized[key] for key in update_columns}

    dialect = _dialect(session, model)
    if dialect in _NATIVE_INSERT_DIALECTS:
        key_map = _db_column_key_map(model)
        normalized_db = {key_map[key]: value for key, value in normalized.items()}
        update_data_db = {key_map[key]: value for key, value in update_data.items()}
        return await _upsert_native(session, model, normalized_db, key_columns, update_data_db, dialect, returning)
    return await _upsert_fallback(session, model, normalized, key_columns, update_data, returning)


async def _upsert_native(
    session: AsyncSession,
    model,
    values: Mapping[str, Any],
    keys: tuple[str, ...],
    update_data: dict[str, Any],
    dialect: str,
    returning: bool,
) -> Upserted:
    result = await session.execute(_upsert_stmt(model, values, keys, update_data, dialect))
    rowcount = _rowcount(result)
    if dialect == "mysql" and rowcount > 1:
        rowcount = 1

    data = None
    if returning or rowcount == 0 or dialect == "mysql":
        key_map = _db_column_key_map(model)
        where = {key_map[key]: values[key_map[key]] for key in keys}
        current = await fetch_one(session, model, where=where)
        if current is None:
            raise RuntimeError("upsert did not match keys; another unique constraint may have matched")
        if returning:
            data = current
    return Upserted(ok=rowcount > 0, rowcount=rowcount, data=data)


async def _upsert_fallback(
    session: AsyncSession,
    model,
    values: Mapping[str, Any],
    keys: tuple[str, ...],
    update_data: dict[str, Any],
    returning: bool,
) -> Upserted:
    where = {key: values[key] for key in keys}
    existing = await fetch_one(session, model, where=where)

    if existing is not None:
        if not update_data:
            return Upserted(ok=False, rowcount=0, data=existing if returning else None)
        stmt = sa_update(model).where(*_build_where_clauses(model, where)).values(**update_data)
        rowcount = _rowcount(await session.execute(stmt))
        data = await fetch_one(session, model, where=where) if returning and rowcount > 0 else None
        return Upserted(ok=rowcount > 0, rowcount=rowcount, data=data)

    obj = model(**values)
    session.add(obj)
    if returning:
        await session.flush()
    data = await fetch_one(session, model, where=where) if returning else None
    return Upserted(ok=True, rowcount=1, data=data)


async def batch_create(
    session: AsyncSession,
    model,
    *,
    values: Sequence[Mapping[str, Any]],
    returning: bool = True,
) -> BatchCreated:
    """通过 ORM `add_all()` 批量创建多条记录，会触发 ORM 事件与关系级联。

    Args:
        session: 异步会话。
        model: SQLAlchemy 映射类。
        values: 每行数据的映射列表；键可为 ORM 属性名或数据库列名。
        returning: 是否返回创建结果。True 时会先 flush，以便取得自增主键和服务端默认值；
            False 时只加入会话，由调用方控制后续 flush/commit。

    Returns:
        `BatchCreated`：`ok=True`，`rowcount` 为创建数量，`data` 为结果列表或空列表。

    Raises:
        TypeError: values 不是映射序列。
        ValueError: 某行含不属于模型的字段。

    e.g.::

        batch = await batch_create(session, User, values=[{"name": "Alice"}, {"name": "Bob"}])
        print(batch.rowcount, batch.data[0]["id"])
    """
    rows = _normalize_value_rows(model, values)
    if not rows:
        return BatchCreated(ok=True, rowcount=0)

    objects = [model(**row) for row in rows]
    session.add_all(objects)
    if returning:
        await session.flush()
    return BatchCreated(
        ok=True,
        rowcount=len(objects),
        data=[_to_dict(obj) for obj in objects] if returning else [],
    )


async def bulk_insert(
    session: AsyncSession,
    model,
    *,
    values: Sequence[Mapping[str, Any]],
    return_defaults: bool = False,
) -> BulkInserted:
    """高性能批量插入记录，跳过 ORM 事件、关系处理和级联。

    使用 SQLAlchemy 2.x 的 `insert(model).values(rows)`。`return_defaults=True` 时，
    PostgreSQL/SQLite 通过 `RETURNING` 返回完整数据；MySQL 等方言逐行插入并读取
    `inserted_primary_key` 补充主键，其他服务端默认值不保证返回。MySQL 逐行路径若中途失败，
    已执行的行仍留在当前事务中，调用方应回滚事务。

    Args:
        session: 异步会话。
        model: SQLAlchemy 映射类。
        values: 每行数据的映射列表；键可为 ORM 属性名或数据库列名。建议各行键集合一致；
            缺失列会按 NULL 绑定，可能绕过 `server_default`。
        return_defaults: 是否返回数据库生成值；开启后可能有额外开销。

    Returns:
        `BulkInserted`：`ok=True`，`rowcount` 为插入行数；`data` 仅在 `return_defaults=True` 时有值。
        PostgreSQL/SQLite 返回完整行，MySQL 等方言只补充主键，其他服务端默认值不保证返回。

    Raises:
        TypeError: values 不是映射序列。
        ValueError: 某行含不属于模型的字段。

    e.g.::

        result = await bulk_insert(session, User, values=[{"name": "A"}, {"name": "B"}])
        result = await bulk_insert(session, User, values=[{"name": "C"}], return_defaults=True)
        print(result.data[0]["id"])
    """
    rows = _normalize_db_value_rows(model, values)
    if not rows:
        return BulkInserted(ok=True, rowcount=0)

    reverse_key_map = {db_key: attr_key for attr_key, db_key in _db_column_key_map(model).items()}
    primary_keys = _primary_key_keys(model)
    dialect_obj = session.get_bind(mapper=model).dialect
    use_returning = return_defaults and bool(getattr(dialect_obj, "insert_returning", False))

    if return_defaults and not use_returning:
        data: list[dict[str, Any]] = []
        rowcount = 0
        for row in rows:
            result = await session.execute(sa_insert(model).values(**row))
            rowcount += _rowcount(result)
            item = {reverse_key_map.get(key, key): value for key, value in row.items()}
            primary_key = getattr(result, "inserted_primary_key", None)
            if primary_keys and primary_key:
                for key, value in zip(primary_keys, primary_key, strict=False):
                    if value is not None:
                        item[key] = value
            data.append(item)
        return BulkInserted(ok=True, rowcount=rowcount, data=data)

    stmt = sa_insert(model).values(rows)
    if use_returning:
        selected, _ = _select_columns(model, None)
        stmt = stmt.returning(*selected)

    result = await session.execute(stmt)
    rowcount = _rowcount(result) or len(rows)
    data = [dict(row) for row in result.mappings().all()] if use_returning else []
    return BulkInserted(ok=True, rowcount=rowcount, data=data)


# -----------------------------------------------------------------------------
# 原生 SQL 执行
# -----------------------------------------------------------------------------


async def raw(
    session: AsyncSession,
    sql: str,
    params: Mapping[str, Any] | None = None,
    *,
    autocommit: bool = False,
    commit: bool | None = None,
) -> Result:
    """执行原生 SQL 语句，使用命名参数占位符 `:name` 防止 SQL 注入。

    `commit=True`（或兼容参数 `autocommit=True`）会提交当前会话中所有未提交的更改，
    而不只是本条语句；事务边界仍由调用方显式控制。

    Args:
        session: 异步会话。
        sql: SQL 文本，不能为空或全空白。
        params: 命名参数字典；None 表示无参数。
        autocommit: 兼容参数，等价于 `commit`；当 `commit` 显式传入时以 `commit` 为准。
        commit: 是否在 execute 后调用 `session.commit()`。

    Returns:
        SQLAlchemy `Result`。常用方法：`fetchall()`、`fetchone()`、`scalar()`、`rowcount`、`mappings()`；
        `commit=True` 后仍可继续读取已缓冲的结果行。

    Raises:
        ValueError: SQL 为空。
        TypeError: params 不是 dict/Mapping/None。

    e.g.::

        result = await raw(session, "SELECT * FROM users WHERE id = :id", {"id": 1})
        users = [dict(row._mapping) for row in result.fetchall()]

        await raw(session, "DELETE FROM users WHERE id = :id", {"id": 1}, commit=True)
    """
    if not sql or not sql.strip():
        raise ValueError("SQL statement cannot be empty")
    if params is not None and not isinstance(params, Mapping):
        raise TypeError(f"params must be dict or None, got {type(params).__name__}")

    result = await session.execute(text(sql), params)
    should_commit = autocommit if commit is None else commit
    if should_commit:
        await session.commit()
    return result


# -----------------------------------------------------------------------------
# CRUD Mixin - 显式类方法，保证 IDE 静态可见签名和文档
# -----------------------------------------------------------------------------


class CRUDMixin:
    """把模块级 CRUD 函数绑定为模型类方法的 Mixin。

    继承本类后，模型可直接调用 `format_row()`、`format_rows()`、`fetch_one()`、`fetch_all()`、
    `count()`、`create()`、`delete()`、`update()`、`upsert()`、`batch_create()`、`bulk_insert()` 和 `raw()`。
    类方法/静态方法与独立函数使用相同签名和文档；类方法调用时无需传 `model`，当前模型类会作为 `cls` 自动传入。

    e.g.::

        from sqlalchemy import Integer, String
        from sqlalchemy.orm import DeclarativeBase, mapped_column
        from toollib.sqlacrud import CRUDMixin

        class Base(CRUDMixin, DeclarativeBase):
            pass

        class User(Base):
            __tablename__ = "users"
            id = mapped_column(Integer, primary_key=True)
            name = mapped_column(String(50))

        user = await User.fetch_one(session, where={"id": 1})
        created = await User.create(session, values={"name": "Tom"})
        await User.update(session, values={"name": "Jerry"}, where={"id": 1})
    """

    @staticmethod
    def format_row(
        row: Any,
        columns: Sequence[str],
        converters: dict[str, Callable[..., Any]] | None = None,
    ) -> dict[str, Any]:
        """把一行 SQLAlchemy 结果格式化为 dict。

        Args:
            row: `fetchone()` 返回的行；支持 `_mapping`、`_asdict()` 或按 `columns` 顺序解包的可迭代对象。
                 None 时返回空 dict。
            columns: 列名顺序，用作回退解包顺序及结果键名。可传 ORM 属性名或数据库列名。
            converters: 字段转换函数，如 `{"created_at": lambda v: v.isoformat()}`；仅转换结果中存在的键。

        Returns:
            单行数据 dict；`row is None` 时为 `{}`。

        e.g.::

            row = await session.execute(select(User.id))
            User.format_row(row.fetchone(), ["id"], {"id": str})
        """
        return format_row(row, columns, converters)

    @staticmethod
    def format_rows(
        rows: Iterable[Any] | None,
        columns: Sequence[str],
        converters: dict[str, Callable[..., Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """把多行 SQLAlchemy 结果格式化为 dict 列表。

        Args:
            rows: `fetchall()` 返回的行序列；None 时返回空列表。
            columns: 列名顺序，决定每行 dict 的键名；行对象支持 `_mapping` 时以行对象键名为准。
            converters: 字段转换函数，如 `{"created_at": lambda v: v.isoformat()}`；逐行应用，仅转换存在的键。

        Returns:
            dict 列表；空输入返回空列表。

        e.g.::

            rows = await session.execute(select(User.id, User.name))
            User.format_rows(rows.fetchall(), ["id", "name"])
        """
        return format_rows(rows, columns, converters)

    @classmethod
    async def fetch_one(
        cls,
        session: AsyncSession,
        *,
        columns: Sequence[str] | None = None,
        where: WhereClause = None,
        order_by: OrderBy = None,
        converters: dict[str, Callable[..., Any]] | None = None,
    ) -> dict[str, Any] | None:
        """查询单条记录并格式化为 dict。

        Args:
            session: 异步会话。
            columns: 指定返回列；None 或空序列表示全部列。元素可为 ORM 属性名或数据库列名。
            where: 过滤条件，支持：
                - dict：`{"name": "Tom", "age": 18}`，值为 None 时生成 IS NULL；
                - ClauseElement：`User.age >= 18`、`text("name = :n")`；
                - ClauseElement 可迭代对象：`[User.age >= 18, User.status == 1]`。
            order_by: 排序，支持 `"name"`、`"-created_at"`、`User.created_at.desc()` 或混合序列；
                不传时 LIMIT 1 的结果顺序不保证，需要确定性首行请显式排序。
            converters: 字段转换函数，如 `{"created_at": lambda v: v.isoformat()}`。

        Returns:
            单行 dict；无匹配记录时为 None。

        Raises:
            ValueError: 列名或排序字段不属于模型。
            TypeError: where/order_by 类型不受支持。

        e.g.::

            user = await User.fetch_one(session, where={"id": 1})
            user = await User.fetch_one(
                session,
                columns=["name", "created_at"],
                where=User.status == 1,
                order_by="-created_at",
                converters={"created_at": lambda value: value.isoformat()},
            )
        """
        return await fetch_one(session, cls, columns=columns, where=where, order_by=order_by, converters=converters)

    @classmethod
    async def fetch_all(
        cls,
        session: AsyncSession,
        *,
        columns: Sequence[str] | None = None,
        where: WhereClause = None,
        order_by: OrderBy = None,
        offset: int | None = None,
        limit: int | None = None,
        converters: dict[str, Callable[..., Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """查询多条记录并格式化为 dict 列表。

        Args:
            session: 异步会话。
            columns: 指定返回列；None 或空序列表示全部列。元素可为 ORM 属性名或数据库列名。
            where: 过滤条件，支持：
                - dict：`{"name": "Tom", "age": 18}`，值为 None 时生成 IS NULL；
                - ClauseElement：`User.age >= 18`、`text("name = :n")`；
                - ClauseElement 可迭代对象：`[User.age >= 18, User.status == 1]`；
                - None：不过滤。
            order_by: 排序，支持 `"name"` 升序、`"-created_at"` 降序、`User.created_at.desc()`
                等 ClauseElement，或由字符串与 ClauseElement 混合组成的序列；None 表示不排序。
            offset: 分页偏移；None 时不生成 OFFSET。
            limit: 分页上限；None 时不生成 LIMIT。
            converters: 字段转换函数，如 `{"created_at": lambda v: v.isoformat()}`；仅转换结果中存在的键。

        Returns:
            行 dict 列表；无匹配记录时为空列表。

        Raises:
            ValueError: 列名或排序字段不属于模型。
            TypeError: where/order_by 类型不受支持。

        e.g.::

            users = await User.fetch_all(session, where={"status": 1}, order_by="-id", offset=20, limit=10)
        """
        return await fetch_all(
            session,
            cls,
            columns=columns,
            where=where,
            order_by=order_by,
            offset=offset,
            limit=limit,
            converters=converters,
        )

    @classmethod
    async def count(
        cls,
        session: AsyncSession,
        *,
        where: WhereClause = None,
    ) -> int:
        """按条件统计记录数，常用于分页总数。

        Args:
            session: 异步会话。
            where: 过滤条件，支持 dict（如 `{"status": 1}`，值为 None 时生成 IS NULL）、
                ClauseElement（如 `User.age >= 18` 或 `text("status = 1")`）、
                ClauseElement 可迭代对象（如 `[User.age >= 18, User.status == 1]`）；
                None 表示统计全表。

        Returns:
            符合条件的行数；数据库返回 NULL 时按 0 处理。

        Raises:
            TypeError: where 类型不受支持。
            ValueError: where dict 中的字段不属于模型。

        e.g.::

            total = await User.count(session, where={"status": 1})
        """
        return await count(session, cls, where=where)

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        *,
        values: Mapping[str, Any],
        on_conflict: dict[str, Any] | None = None,
        returning: bool = True,
    ) -> Created:
        """创建单条记录，可选唯一键冲突时返回已存在记录。

        `on_conflict` 是“是否已存在”的等值查询条件，不是写入值，且必须等于模型声明的主键或唯一键集合。
        仅当 `values` 中对应字段与条件值一致时，PostgreSQL/SQLite 走原生 `ON CONFLICT DO NOTHING`，
        MySQL 走 `INSERT IGNORE` 以规避竞态；不一致或其他方言回退为先查后插，保持“条件是条件、值是值”的语义。
        MySQL 的 `INSERT IGNORE` 会把部分数据错误（如 NOT NULL、截断）降级为 warning，调用方应确保输入已校验。

        Args:
            session: 异步会话。
            values: 创建数据；键可为 ORM 属性名或数据库列名。
            on_conflict: 非空唯一键等值条件，如 `{"email": "a@b.com"}`；不能包含 NULL，None 表示不做冲突检查。
            returning: 是否在成功创建时返回数据。True 时会先 flush，以便取得自增主键和服务端默认值；
                False 时成功分支不返回数据。无 `on_conflict` 时只加入会话；`on_conflict` 走原生路径时立即执行，
                回退路径只加入会话，可能延迟到调用方 flush/commit。冲突分支无论 returning 取值都会返回已存在数据。

        Returns:
            `Created`：成功时 `ok=True`、`rowcount=1`，`data` 为新建数据；
            冲突时 `ok=False`、`rowcount=0`，`data` 为已存在数据。

        Raises:
            TypeError: `values` 或 `on_conflict` 不是映射类型。
            ValueError: `on_conflict` 为空、含 NULL、字段不属于模型，或未精确匹配主键/唯一键集合。
            RuntimeError: 原生插入被其他唯一约束忽略，无法按 `on_conflict` 找到对应记录。

        e.g.::

            result = await User.create(session, values={"name": "Tom"})
            if result:
                print(result.data["id"])

            result = await User.create(
                session,
                values={"email": "a@b.com", "name": "Tom"},
                on_conflict={"email": "a@b.com"},
            )
        """
        return await create(session, cls, values=values, on_conflict=on_conflict, returning=returning)

    @classmethod
    async def delete(
        cls,
        session: AsyncSession,
        *,
        where: WhereClause = None,
        allow_all: bool = False,
    ) -> Deleted:
        """按条件删除记录，默认拒绝无条件的全表删除。

        Args:
            session: 异步会话。
            where: 过滤条件，支持 dict（如 `{"id": 1}`，值为 None 时生成 IS NULL）、
                ClauseElement（如 `User.age < 18` 或 `text("status = 0")`）、
                ClauseElement 可迭代对象（如 `[User.age < 18, User.status == 0]`）；
                None 表示全表，需配合 `allow_all=True`。
            allow_all: 是否允许无条件全表删除；为 False 且 where 为空时抛错。

        Returns:
            `Deleted`：`ok` 等价于 `rowcount > 0`；未命中记录时 rowcount 为 0。

        Raises:
            TypeError: where 类型不受支持。
            ValueError: 无 where 且未设置 `allow_all=True`，或 where dict 中的字段不属于模型。

        e.g.::

            await User.delete(session, where={"id": 1})
            await User.delete(session, where=[User.age < 18, User.status == 0])
            await User.delete(session, allow_all=True)
        """
        return await delete(session, cls, where=where, allow_all=allow_all)

    @classmethod
    async def update(
        cls,
        session: AsyncSession,
        *,
        values: Mapping[str, Any],
        where: WhereClause = None,
        allow_all: bool = False,
        exclude_none: bool = True,
        null_columns: Sequence[str] | None = None,
        returning: bool = False,
    ) -> Updated:
        """按条件更新记录，默认拒绝无条件的全表更新。

        `exclude_none=True` 会跳过值为 None 的字段；若要显式置 NULL，请设置 `exclude_none=False`
        或用 `null_columns` 指定允许置空的字段。`returning=True` 要求 `where` 为 dict，且覆盖模型声明
        的主键或唯一键（值不能为 NULL），避免多行命中时返回歧义数据；不能同时更新主键，但可以更新
        `where` 中用到的其他唯一键，返回数据会按更新前的主键重新查询。

        Args:
            session: 异步会话。
            values: 待更新字段；键可为 ORM 属性名或数据库列名。
            where: 过滤条件，支持 dict（如 `{"id": 1}`，值为 None 时生成 IS NULL）、
                ClauseElement（如 `User.last_login < cutoff` 或 `text("status = 1")`）、
                ClauseElement 可迭代对象（如 `[User.age < 18, User.status == 1]`）；
                None 表示全表，需配合 `allow_all=True`。
            allow_all: 是否允许无条件全表更新。
            exclude_none: 是否跳过值为 None 的字段。
            null_columns: 即使 `exclude_none=True` 也允许写入 NULL 的字段名列表。
            returning: 是否查询并返回更新后的数据；不能与更新主键同时使用。

        Returns:
            `Updated`：`ok` 等价于 `rowcount > 0`；`data` 仅在 `returning=True` 且命中时有值。
            若过滤掉所有字段后无可更新内容，返回 `Updated(ok=False, rowcount=0)`。
            MySQL 默认不统计“值未变化”的更新，此时 `rowcount` 可能为 0，而 PostgreSQL/SQLite 通常为 1。

        Raises:
            TypeError: `values` 不是映射类型。
            ValueError: 无 where 且未设置 `allow_all`；returning 条件不满足；字段、null_columns 或主键更新非法。

        e.g.::

            await User.update(session, values={"name": "New"}, where={"id": 1})
            await User.update(
                session,
                values={"note": None},
                where={"id": 1},
                null_columns=["note"],
                returning=True,
            )
        """
        return await update(
            session,
            cls,
            values=values,
            where=where,
            allow_all=allow_all,
            exclude_none=exclude_none,
            null_columns=null_columns,
            returning=returning,
        )

    @classmethod
    async def upsert(
        cls,
        session: AsyncSession,
        *,
        values: Mapping[str, Any],
        keys: Sequence[str],
        updates: Sequence[str] | None = None,
        returning: bool = False,
    ) -> Upserted:
        """按唯一键执行 upsert：存在则更新，不存在则创建。

        PostgreSQL/SQLite 使用 `ON CONFLICT`，MySQL 使用 `ON DUPLICATE KEY UPDATE`（无更新字段时执行无操作更新），
        其他方言回退为先查后改。`keys` 必须存在于 `values`，且必须等于模型声明的主键或唯一键集合；
        `updates` 中若包含 `keys` 会被忽略，避免修改冲突目标列；`updates` 中的其他字段必须存在于
        `values`，且不能是主键。`rowcount` 表示
        受影响行数，方言对“无变化更新”的计数可能不同（MySQL 的 2 会归一化为 1）。

        Args:
            session: 异步会话。
            values: 完整数据；键可为 ORM 属性名或数据库列名。
            keys: 唯一键字段名，如 `("id",)` 或 `["email"]`。
            updates: 冲突时更新的字段，必须同时存在于 values；None 表示更新除 keys 和主键外的所有字段。
            returning: 是否查询并返回操作后的数据；True 时回退路径会先 flush 以获取生成值。

        Returns:
            `Upserted`：`ok` 等价于 `rowcount > 0`；`data` 仅在 `returning=True` 时有值。

        Raises:
            TypeError: `values` 不是映射类型。
            ValueError: `keys` 为空、不在 values 中或未精确匹配主键/唯一键集合；
                `updates` 含非法列、缺失于 values 或包含主键。
            RuntimeError: 插入/更新命中了其他唯一键，无法按 `keys` 找到对应记录。

        e.g.::

            result = await User.upsert(
                session,
                values={"id": 1, "name": "Tom", "email": "tom@test.com"},
                keys=("id",),
                updates=("name",),
                returning=True,
            )
        """
        return await upsert(session, cls, values=values, keys=keys, updates=updates, returning=returning)

    @classmethod
    async def batch_create(
        cls,
        session: AsyncSession,
        *,
        values: Sequence[Mapping[str, Any]],
        returning: bool = True,
    ) -> BatchCreated:
        """通过 ORM `add_all()` 批量创建多条记录，会触发 ORM 事件与关系级联。

        Args:
            session: 异步会话。
            values: 每行数据的映射列表；键可为 ORM 属性名或数据库列名。
            returning: 是否返回创建结果。True 时会先 flush，以便取得自增主键和服务端默认值；
                False 时只加入会话，由调用方控制后续 flush/commit。

        Returns:
            `BatchCreated`：`ok=True`，`rowcount` 为创建数量，`data` 为结果列表或空列表。

        Raises:
            TypeError: values 不是映射序列。
            ValueError: 某行含不属于模型的字段。

        e.g.::

            batch = await User.batch_create(session, values=[{"name": "Alice"}, {"name": "Bob"}])
            print(batch.rowcount, batch.data[0]["id"])
        """
        return await batch_create(session, cls, values=values, returning=returning)

    @classmethod
    async def bulk_insert(
        cls,
        session: AsyncSession,
        *,
        values: Sequence[Mapping[str, Any]],
        return_defaults: bool = False,
    ) -> BulkInserted:
        """高性能批量插入记录，跳过 ORM 事件、关系处理和级联。

        使用 SQLAlchemy 2.x 的 `insert(model).values(rows)`。`return_defaults=True` 时，
        PostgreSQL/SQLite 通过 `RETURNING` 返回完整数据；MySQL 等方言逐行插入并读取
        `inserted_primary_key` 补充主键，其他服务端默认值不保证返回。MySQL 逐行路径若中途失败，
        已执行的行仍留在当前事务中，调用方应回滚事务。

        Args:
            session: 异步会话。
            values: 每行数据的映射列表；键可为 ORM 属性名或数据库列名。建议各行键集合一致；
                缺失列会按 NULL 绑定，可能绕过 `server_default`。
            return_defaults: 是否返回数据库生成值；开启后可能有额外开销。

        Returns:
            `BulkInserted`：`ok=True`，`rowcount` 为插入行数；`data` 仅在 `return_defaults=True` 时有值。
            PostgreSQL/SQLite 返回完整行，MySQL 等方言只补充主键，其他服务端默认值不保证返回。

        Raises:
            TypeError: values 不是映射序列。
            ValueError: 某行含不属于模型的字段。

        e.g.::

            result = await User.bulk_insert(session, values=[{"name": "A"}, {"name": "B"}])
            result = await User.bulk_insert(session, values=[{"name": "C"}], return_defaults=True)
            print(result.data[0]["id"])
        """
        return await bulk_insert(session, cls, values=values, return_defaults=return_defaults)

    @classmethod
    async def raw(
        cls,
        session: AsyncSession,
        sql: str,
        params: Mapping[str, Any] | None = None,
        *,
        autocommit: bool = False,
        commit: bool | None = None,
    ) -> Result:
        """执行原生 SQL 语句，使用命名参数占位符 `:name` 防止 SQL 注入。

        `commit=True`（或兼容参数 `autocommit=True`）会提交当前会话中所有未提交的更改，
        而不只是本条语句；事务边界仍由调用方显式控制。

        Args:
            session: 异步会话。
            sql: SQL 文本，不能为空或全空白。
            params: 命名参数字典；None 表示无参数。
            autocommit: 兼容参数，等价于 `commit`；当 `commit` 显式传入时以 `commit` 为准。
            commit: 是否在 execute 后调用 `session.commit()`。

        Returns:
            SQLAlchemy `Result`。常用方法：`fetchall()`、`fetchone()`、`scalar()`、`rowcount`、`mappings()`；
            `commit=True` 后仍可继续读取已缓冲的结果行。

        Raises:
            ValueError: SQL 为空。
            TypeError: params 不是 dict/Mapping/None。

        e.g.::

            result = await User.raw(session, "SELECT * FROM users WHERE id = :id", {"id": 1})
            users = [dict(row._mapping) for row in result.fetchall()]

            await User.raw(session, "DELETE FROM users WHERE id = :id", {"id": 1}, commit=True)
        """
        return await raw(session, sql, params, autocommit=autocommit, commit=commit)
