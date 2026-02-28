"""
SQLAlchemy 异步 CRUD 工具库（支持 PostgreSQL、MySQL、SQLite），其中 CRUDMixin 可集成到模型类

e.g.::

    from sqlalchemy.ext.asyncio import AsyncSession
    from mymodels import User

    async def example(session: AsyncSession):

        # 查询
        user = await fetch_one(session, User, where={"id": 1})
        users = await fetch_all(session, User, limit=10)

        # 创建
        created = await create(session, User, values={"name": "Tom"})

        # 删除
        deleted = await delete(session, User, where={"id": 1})        

        # 更新
        updated = await update(session, User, values={"name": "New"}, where={"id": 1})

        # ...

    +++++[更多详见参数或源码]+++++
"""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, Any, Callable

from sqlalchemy import (
    select,
    func,
    text,
    update as sa_update,
    delete as sa_delete,
    inspect,
    ColumnElement,
)
from sqlalchemy.engine import Result
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = [
    "Created",
    "Updated",
    "Deleted",
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


# -----------------------------------------------------------------------------
# 返回类型定义
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Created:
    """创建操作结果"""

    ok: bool  # 是否成功
    rowcount: int = 0  # 影响行数
    data: dict[str, Any] | None = None  # 相关数据：创建成功时为新建数据，冲突时为已存在的数据

    def __bool__(self) -> bool:
        return self.ok


@dataclass(frozen=True, slots=True)
class Deleted:
    """删除操作结果"""

    ok: bool  # 是否成功
    rowcount: int = 0  # 删除行数

    def __bool__(self) -> bool:
        return self.ok


@dataclass(frozen=True, slots=True)
class Updated:
    """更新操作结果"""

    ok: bool  # 是否成功
    rowcount: int = 0  # 影响行数
    data: dict[str, Any] | None = None  # 更新后的数据（可选）

    def __bool__(self) -> bool:
        return self.ok


@dataclass(frozen=True, slots=True)
class Upserted:
    """更新插入操作结果"""

    data: Any  # 数据对象
    action: Literal["insert", "update", "noop"] = "insert"

    def __bool__(self) -> bool:
        return self.action != "noop"

    @property
    def inserted(self) -> bool:
        return self.action == "insert"

    @property
    def updated(self) -> bool:
        return self.action == "update"


@dataclass(frozen=True, slots=True)
class BatchCreated:
    """批量创建结果"""

    ok: bool  # 是否全部成功
    rowcount: int = 0  # 创建数量
    data: list[dict[str, Any]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok


@dataclass(frozen=True, slots=True)
class BulkInserted:
    """高性能批量插入结果"""

    ok: bool  # 是否成功
    rowcount: int = 0  # 插入数量
    data: list[dict[str, Any]] = field(
        default_factory=list
    )  # 插入的数据（可能包含默认值）

    def __bool__(self) -> bool:
        return self.ok


# -----------------------------------------------------------------------------
# 内部工具函数
# -----------------------------------------------------------------------------


def _dialect(session: AsyncSession) -> str:
    """获取数据库方言名称"""
    return session.bind.dialect.name if session.bind else "unknown"


def _build_where_clauses(
        model, where: dict[str, Any]
        | ColumnElement[Any]
        | Sequence[ColumnElement[Any]]
        | None = None
) -> list[ColumnElement[Any]]:
    """构建 where 条件列表

    支持多种 where 格式：
    - None: 返回空列表
    - dict: {"name": "Tom", "age": 18} -> [User.name == "Tom", User.age == 18]
    - ColumnElement: User.age > 18 -> [User.age > 18]
    - Sequence[ColumnElement]: [User.age > 18, User.status == 1] -> [User.age > 18, User.status == 1]
    """
    if where is None:
        return []

    # 情况1：字典 → 转成等值条件
    if isinstance(where, Mapping):
        conditions = []
        for key, value in where.items():
            if not hasattr(model, key):
                raise ValueError(f"Invalid column '{key}' for model {model.__name__}")
            column = getattr(model, key)
            conditions.append(column == value)
        return conditions

    # 情况2：单个 ColumnElement
    if isinstance(where, ColumnElement):
        return [where]

    # 情况3：列表或元组（多个 ColumnElement）
    if isinstance(where, (list, tuple)):
        for i, expr in enumerate(where):
            if not isinstance(expr, ColumnElement):
                raise TypeError(f"where[{i}] is not a SQLAlchemy ColumnElement: {expr!r}")
        return list(where)

    raise TypeError(f"Unsupported where type: {type(where)}")


def _columns(model) -> list[str]:
    """获取模型所有列名"""
    return [column.name for column in inspect(model).mapper.columns]


def _to_dict(model, columns: Sequence[str] | None = None) -> dict[str, Any]:
    """模型实例转字典"""
    if not model:
        return {}
    if columns is None:
        columns = _columns(model)
    return {col: getattr(model, col) for col in columns if hasattr(model, col)}


def _parse_order_by(model, order_by: str | Sequence[str]) -> list[ColumnElement[Any]]:
    """解析排序字段

    支持格式:
    - "name" -> name ASC
    - "-created_at" -> created_at DESC
    - ("name", "-created_at") -> name ASC, created_at DESC
    - ["name", "-created_at"] -> name ASC, created_at DESC
    """
    if isinstance(order_by, str):
        order_by = (order_by,)

    result = []
    for order_column in order_by:
        if order_column.startswith("-"):
            column_name = order_column[1:]
            desc = True
        else:
            column_name = order_column
            desc = False

        if not hasattr(model, column_name):
            raise ValueError(f"Invalid order_by column '{column_name}' for model {model.__name__}")
        column = getattr(model, column_name)
        result.append(column.desc() if desc else column.asc())

    return result


# -----------------------------------------------------------------------------
# 格式化操作
# -----------------------------------------------------------------------------


def format_row(
        row,
        columns: Sequence[str],
        converters: dict[str, Callable] | None = None,
) -> dict[str, Any]:
    """格式化单行结果

    Args:
        row: 数据库结果行
        columns: 列名列表
        converters: 字段转换器

    Returns:
        字典格式的单行数据
    """
    if not row:
        return {}
    data = row._asdict() if hasattr(row, "_asdict") else dict(zip(columns, row))
    if converters:
        for key, converter in converters.items():
            if key in data:
                data[key] = converter(data[key])
    return data


def format_rows(
        rows,
        columns: Sequence[str],
        converters: dict[str, Callable] | None = None,
) -> list[dict[str, Any]]:
    """格式化多行结果

    Args:
        rows: 数据库结果行列表
        columns: 列名列表
        converters: 字段转换器

    Returns:
        字典列表格式的多行数据
    """
    if not rows:
        return []
    return [
        format_row(row, columns, converters)
        for row in rows
    ]


# -----------------------------------------------------------------------------
# 查询操作
# -----------------------------------------------------------------------------


async def fetch_one(
        session: AsyncSession,
        model,
        *,
        columns: Sequence[str] | None = None,
        where: dict[str, Any]
        | ColumnElement[Any]
        | Sequence[ColumnElement[Any]]
        | None = None,
        order_by: str | Sequence[str] | None = None,
        converters: dict[str, Callable] | None = None,
) -> dict[str, Any] | None:
    """查询单条记录

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        columns: 指定返回列，None 返回所有列
        where: 过滤条件，支持：
            - None: 无过滤条件
            - dict: {"name": "Tom", "age": 18}
            - ColumnElement: User.age > 18
            - Sequence[ColumnElement]: [User.age > 18, User.status == 1]
        order_by: 排序字段，支持多字段。字符串前面加 "-" 表示降序
        converters: 字段转换器，{"column": func}

    Returns:
        单条记录字典

    e.g.::

        # 单字段排序
        user = await fetch_one(session, User, order_by="-created_at")

        # 字段转换
        user = await fetch_one(
            session, User,
            where={"id": 1},
            converters={"created_at": lambda x: x.isoformat(), "status": bool}
        )

        +++++[更多详见参数或源码]+++++
    """
    model_columns = _columns(model)
    if columns:
        invalid_cols = [col for col in columns if col not in model_columns]
        if invalid_cols:
            raise ValueError(f"Invalid columns {invalid_cols} for model {model.__name__}")
        selected_columns = tuple(getattr(model, col) for col in columns)
    else:
        selected_columns = tuple(getattr(model, col) for col in model_columns)

    stmt = select(*selected_columns).select_from(model)

    if where:
        stmt = stmt.where(*_build_where_clauses(model, where))
    if order_by:
        stmt = stmt.order_by(*_parse_order_by(model, order_by))

    result = await session.execute(stmt.limit(1))
    return format_row(result.fetchone(), columns or model_columns, converters)


async def fetch_all(
        session: AsyncSession,
        model,
        *,
        columns: Sequence[str] | None = None,
        where: dict[str, Any]
        | ColumnElement[Any]
        | Sequence[ColumnElement[Any]]
        | None = None,
        order_by: str | Sequence[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        converters: dict[str, Callable] | None = None,
) -> list[dict[str, Any]]:
    """查询多条记录

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        columns: 指定返回列
        where: 过滤条件，支持：
            - None: 无过滤条件
            - dict: {"name": "Tom", "age": 18}
            - ColumnElement: User.age > 18
            - Sequence[ColumnElement]: [User.age > 18, User.status == 1]
        order_by: 排序字段，支持 "-column" 降序
        offset: 分页偏移
        limit: 分页限制
        converters: 字段转换器，{"column": func}

    Returns:
        记录字典列表

    e.g.::

        # 基础查询
        users = await fetch_all(session, User, order_by="-created_at", limit=10)

        # 字段转换
        users = await fetch_all(
            session, User,
            where={"status": 1},
            converters={"created_at": lambda x: x.isoformat()}
        )

        +++++[更多详见参数或源码]+++++
    """
    model_columns = _columns(model)
    if columns:
        invalid_cols = [col for col in columns if col not in model_columns]
        if invalid_cols:
            raise ValueError(f"Invalid columns {invalid_cols} for model {model.__name__}")
        selected_columns = tuple(getattr(model, col) for col in columns)
    else:
        selected_columns = tuple(getattr(model, col) for col in model_columns)

    stmt = select(*selected_columns).select_from(model)

    if where:
        stmt = stmt.where(*_build_where_clauses(model, where))
    if order_by:
        stmt = stmt.order_by(*_parse_order_by(model, order_by))
    if offset is not None:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return format_rows(result.fetchall(), columns or model_columns, converters)


async def count(
        session: AsyncSession,
        model,
        *,
        where: dict[str, Any]
        | ColumnElement[Any]
        | Sequence[ColumnElement[Any]]
        | None = None,
) -> int:
    """统计记录数

    返回符合条件的记录总数，用于分页等场景。

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        where: 过滤条件，支持：
            - dict: {"name": "Tom", "age": 18}
            - ColumnElement: User.age > 18
            - Sequence[ColumnElement]: [User.age > 18, User.status == 1]
            - None: 统计全部记录

    Returns:
        记录数量

    e.g.::

        # 统计所有用户
        total = await count(session, User)

        # 统计正常用户
        active_count = await count(session, User, where={"status": 1})

        # 使用表达式
        adult_count = await count(session, User, where=User.age >= 18)

        # 使用多个条件
        count = await count(session, User, where=[User.age >= 18, User.status == 1])

        +++++[更多详见参数或源码]+++++
    """
    stmt = select(func.count()).select_from(model)
    if where:
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
        values: dict[str, Any],
        on_conflict: dict[str, Any] | None = None,
        returning: bool = True,
        flush: bool = False,
) -> Created:
    """创建单条记录

    根据提供的值创建新记录，如果 on_conflict 指定的条件已存在，
    则返回冲突记录而不创建新记录。

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        values: 要创建的数据字典
        on_conflict: 唯一性冲突检查，如果存在则返回 False。
                    如 {"email": "user@test.com"} 会检查邮箱是否已存在。
        returning: 是否返回创建后的数据字典，False 时只返回 success 状态。
        flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

    Returns:
        Created: 创建操作结果
            - ok: True 表示创建成功，False 表示记录已存在
            - rowcount: 影响行数，成功为1，冲突为0
            - data: 创建后的数据字典（returning=True 时）

    e.g.::

        # 创建新用户
        created = await create(
            session,
            User,
            values={"name": "Tom", "email": "tom@test.com"}
        )
        if created:
            print(f"创建成功: {created.data}, 行数: {created.rowcount}")

        # 唯一冲突检查
        created = await create(
            session,
            User,
            values={"email": "existing@test.com", "name": "Bob"},
            on_conflict={"email": "existing@test.com"}
        )
        if not created:
            print(f"记录已存在，行数: {created.rowcount}")

        +++++[更多详见参数或源码]+++++
    """
    if on_conflict:
        if existing := await fetch_one(session, model, where=on_conflict):
            return Created(ok=False, rowcount=0, data=existing)

    obj = model(**values)
    session.add(obj)
    if flush:
        await session.flush()

    return Created(
        ok=True,
        rowcount=1,
        data=_to_dict(obj) if returning else None,
    )


async def delete(
        session: AsyncSession,
        model,
        *,
        where: dict[str, Any]
        | ColumnElement[Any]
        | Sequence[ColumnElement[Any]]
        | None = None,
        allow_all: bool = False,
        flush: bool = False,
) -> Deleted:
    """删除记录

    根据条件删除记录。默认情况下需要提供 where 条件，防止误删全表。
    如需删除全部记录，请设置 allow_all=True。

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        where: 过滤条件，支持：
            - None: 删除全部记录（需 allow_all=True）
            - dict: {"id": 1}
            - ColumnElement: User.id == 1
            - Sequence[ColumnElement]: [User.age < 18, User.status == 0]
        allow_all: 是否允许无条件删除（全表删除），默认 False
        flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

    Returns:
        Deleted: 删除操作结果
            - ok: True 表示删除成功（rowcount > 0），False 表示未找到匹配记录
            - rowcount: 删除的行数

    e.g.::

        # 删除单个用户
        deleted = await delete(
            session,
            User,
            where={"id": 1}
        )
        if deleted:
            print(f"已删除 {deleted.rowcount} 条记录")

        # 批量删除
        deleted = await delete(
            session,
            User,
            where={"status": 2}
        )
        print(f"已清理 {deleted.rowcount} 条失效记录")

        # 使用表达式
        deleted = await delete(
            session,
            User,
            where=User.age < 18
        )

        # 使用多个条件
        deleted = await delete(
            session,
            User,
            where=[User.age < 18, User.status == 0]
        )

        # 全表删除（需显式声明）
        deleted = await delete(session, User, allow_all=True)
        print(f"已清空 {deleted.rowcount} 条记录")

        +++++[更多详见参数或源码]+++++
    """
    clauses = _build_where_clauses(model, where)
    if not clauses and not allow_all:
        raise ValueError("'where' is required, or set allow_all=True for full-table delete")

    stmt = sa_delete(model)
    if clauses:
        stmt = stmt.where(*clauses)
    result = await session.execute(stmt)
    if flush:
        await session.flush()

    rowcount = result.rowcount or 0
    return Deleted(ok=rowcount > 0, rowcount=rowcount)


async def update(
        session: AsyncSession,
        model,
        *,
        values: dict[str, Any],
        where: dict[str, Any]
        | ColumnElement[Any]
        | Sequence[ColumnElement[Any]]
        | None = None,
        allow_all: bool = False,
        exclude_none: bool = True,
        returning: bool = False,
        flush: bool = False,
) -> Updated:
    """更新记录

    根据条件更新符合条件的记录。默认情况下需要提供 where 条件，防止误更新全表。
    如需更新全部记录，请设置 allow_all=True。

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        values: 要更新的数据字典
        where: 过滤条件，支持：
            - None: 更新全部记录（需 allow_all=True）
            - dict: {"id": 1}
            - ColumnElement: User.id == 1
            - Sequence[ColumnElement]: [User.age < 18, User.status == 0]
        allow_all: 是否允许无条件更新（全表更新），默认 False
        exclude_none: 是否自动排除值为 None 的字段，True 时跳过 None 值
        returning: 是否返回更新后的数据字典（不支持全表更新）。需要额外查询。
        flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

    Returns:
        Updated: 更新操作结果
            - ok: True 表示更新成功（rowcount > 0），False 表示未找到匹配记录
            - rowcount: 受影响的行数
            - data: 更新后的数据字典（returning=True 时，不支持全表更新）

    e.g.::

        # 更新单个用户
        updated = await update(
            session,
            User,
            values={"name": "New Name", "email": "new@test.com"},
            where={"id": 1}
        )
        if updated:
            print(f"更新了 {updated.rowcount} 条记录")

        # 获取更新后的数据
        updated = await update(
            session,
            User,
            values={"name": "New Name"},
            where={"id": 1},
            returning=True
        )
        print(updated.data)  # 更新后的完整记录

        # 使用表达式
        updated = await update(
            session,
            User,
            values={"status": 0},
            where=User.last_login < datetime(2025, 1, 1)
        )

        # 使用多个条件
        updated = await update(
            session,
            User,
            values={"status": 0},
            where=[User.age < 18, User.status == 1]
        )

        # 全表更新（需显式声明）
        updated = await update(
            session,
            User,
            values={"status": 0},
            allow_all=True
        )

        +++++[更多详见参数或源码]+++++
    """
    clauses = _build_where_clauses(model, where)
    if not clauses and not allow_all:
        raise ValueError("'where' is required, or set allow_all=True for full-table update")

    # 全表更新不支持 returning
    if not clauses and returning:
        raise ValueError("'returning' is not supported for full-table update")

    data = (
        {k: v for k, v in values.items() if v is not None} if exclude_none else values
    )
    if not data:
        return Updated(ok=False, rowcount=0)

    stmt = sa_update(model).values(**data)
    if clauses:
        stmt = stmt.where(*clauses)
    result = await session.execute(stmt)
    if flush:
        await session.flush()

    rowcount = result.rowcount or 0
    updated_data = (
        await fetch_one(session, model, where=where)
        if (returning and rowcount > 0 and clauses)
        else None
    )

    return Updated(ok=rowcount > 0, rowcount=rowcount, data=updated_data)


async def upsert(
        session: AsyncSession,
        model,
        *,
        values: dict[str, Any],
        keys: Sequence[str],
        updates: Sequence[str] | None = None,
        flush: bool = False,
) -> Upserted:
    """存在则更新，不存在则创建（Upsert）

    根据唯一键判断记录是否存在，不存在则创建，存在则更新。
    自动根据数据库方言选择最优实现：
    - PostgreSQL/SQLite: INSERT ... ON CONFLICT DO UPDATE
    - MySQL: INSERT ... ON DUPLICATE KEY UPDATE
    - 其他: 先查后改（fallback）

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        values: 完整数据字典
        keys: 唯一键字段列表，用于判断记录是否存在，如 ("id",), ("email",)
        updates: 指定更新时的字段列表，None 表示更新除 keys 外的所有字段
        flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

    Returns:
        Upserted: Upsert 操作结果
            - data: 数据对象（SQLAlchemy 模型实例）
            - action: 操作类型 - "insert"(新建) / "update"(更新) / "noop"(无变化)

    e.g.::

        # 按 id upsert
        upserted = await upsert(
            session,
            User,
            values={"id": 1, "name": "Tom", "email": "tom@test.com"},
            keys=("id",)
        )
        if upserted.inserted:
            print("新建用户")
        elif upserted.updated:
            print("更新用户")

        # 只更新特定字段
        upserted = await upsert(
            session,
            User,
            values={"id": 1, "name": "Updated", "email": "new@test.com"},
            keys=("id",),
            updates=("name",)  # 只更新 name，email 不变
        )

        +++++[更多详见参数或源码]+++++
    """
    if not keys or not all(key in values for key in keys):
        raise ValueError("'keys' must be non-empty and exist in values")

    dialect = _dialect(session)

    if dialect in ("postgresql", "mysql", "sqlite"):
        return await _upsert_native(
            session, model, values, keys, updates, dialect, flush
        )
    return await _upsert_fallback(session, model, values, keys, updates, flush)


async def _upsert_native(
        session: AsyncSession,
        model,
        values: dict[str, Any],
        keys: Sequence[str],
        updates: Sequence[str] | None,
        dialect: str,
        flush: bool = False,
) -> Upserted:
    """使用数据库原生 upsert 语法实现

    根据数据库方言使用对应的 upsert 语法。
    """
    update_cols = updates if updates is not None else tuple(col for col in values if col not in keys)
    update_data = {col: values[col] for col in update_cols if col in values}

    # 选择 insert 构造器
    insert_map = {
        "postgresql": pg_insert,
        "mysql": mysql_insert,
        "sqlite": sqlite_insert,
    }
    insert_func = insert_map.get(dialect, pg_insert)

    stmt = insert_func(model).values(**values)

    if update_data:
        if dialect == "mysql":
            stmt = stmt.on_duplicate_key_update(**update_data)
        else:
            stmt = stmt.on_conflict_do_update(index_elements=keys, set_=update_data)
    else:
        if dialect == "mysql":
            stmt = stmt.prefix_with("IGNORE")
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=keys)

    result = await session.execute(stmt)
    if flush:
        await session.flush()

    # 查询获取完整对象
    where = {k: values[k] for k in keys if k in values}
    obj_data = await fetch_one(session, model, where=where)
    obj = model(**obj_data) if obj_data else model(**values)

    # 判断操作类型
    rowcount = getattr(result, "rowcount", 1)
    if dialect == "mysql":
        # MySQL ON DUPLICATE KEY UPDATE 返回值：
        # - 0: 新插入行
        # - 1: 行已存在但数据未变化
        # - 2: 行已存在且已更新
        if rowcount == 0:
            action = "insert"
        elif rowcount == 2:
            action = "update"
        else:
            action = "noop"
    else:
        # PostgreSQL/SQLite ON CONFLICT 返回值：
        # - 1: 新插入行
        # - 0: 冲突但未更新（ON CONFLICT DO NOTHING）
        if rowcount == 0:
            action = "noop"
        elif update_data:
            action = "update"
        else:
            action = "insert"

    return Upserted(data=obj, action=action)


async def _upsert_fallback(
        session: AsyncSession,
        model,
        values: dict[str, Any],
        keys: Sequence[str],
        updates: Sequence[str] | None,
        flush: bool = False,
) -> Upserted:
    """Upsert 的通用 fallback 实现（先查后改）

    先查询记录是否存在，存在则更新，不存在则创建。
    用于不支持原生 upsert 语法的数据库。
    """
    where = {k: values[k] for k in keys if k in values}
    existing = await fetch_one(session, model, where=where)

    if existing:
        update_cols = updates if updates is not None else tuple(col for col in values if col not in keys)
        update_data = {col: values[col] for col in update_cols if col in values}
        if update_data:
            stmt = sa_update(model).where(
                *_build_where_clauses(model, where)
            ).values(**update_data)
            await session.execute(stmt)
            if flush:
                await session.flush()
            updated_data = await fetch_one(session, model, where=where)
            return Upserted(data=model(**updated_data), action="update")
        return Upserted(data=model(**existing), action="noop")

    obj = model(**values)
    session.add(obj)
    if flush:
        await session.flush()
    return Upserted(data=obj, action="insert")


async def batch_create(
        session: AsyncSession,
        model,
        *,
        values: list[dict[str, Any]],
        returning: bool = True,
        flush: bool = False,
) -> BatchCreated:
    """批量创建多条记录

    一次性创建多条记录，性能优于循环调用 create()。

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        values: 数据字典列表，每个字典创建一条记录
        returning: 是否返回创建后的数据字典列表，False 时只返回 count。
        flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

    Returns:
        BatchCreated: 批量创建结果
            - ok: 总是 True
            - rowcount: 实际创建的记录数
            - data: 创建后的数据列表（returning=True 时）

    e.g.::

        # 批量创建用户
        batch = await batch_create(
            session,
            User,
            values=[
                {"name": "Alice", "email": "alice@test.com"},
                {"name": "Bob", "email": "bob@test.com"},
            ]
        )
        print(f"成功创建 {batch.rowcount} 条记录")
        for user in batch.data:
            print(user["name"])

        +++++[更多详见参数或源码]+++++
    """
    if not values:
        return BatchCreated(ok=True, rowcount=0)

    objs = [model(**value) for value in values]
    session.add_all(objs)
    if flush:
        await session.flush()

    return BatchCreated(
        ok=True,
        rowcount=len(objs),
        data=[_to_dict(obj) for obj in objs] if returning else [],
    )


async def bulk_insert(
        session: AsyncSession,
        model,
        *,
        values: list[dict[str, Any]],
        return_defaults: bool = False,
        flush: bool = False,
) -> BulkInserted:
    """高性能批量插入记录

    使用 SQLAlchemy 的 bulk_insert_mappings 实现，跳过 ORM 的事件监听和关系处理，
    性能显著优于 batch_create()，适合大数据量导入场景。

    注意：此方法不会触发 ORM 事件（如 @event.listens_for）、不会处理关系关联、
    不会自动处理关联对象的级联操作。如需完整 ORM 功能，请使用 batch_create()。

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        values: 数据字典列表，每个字典插入一条记录
        return_defaults: 是否获取数据库生成的默认值（如自增主键）。
                        True 时会在返回结果中包含这些值，但会有轻微性能损耗。
        flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

    Returns:
        BulkInserted: 批量插入结果
            - ok: 总是 True（除非发生异常）
            - rowcount: 实际插入的记录数
            - data: 插入的数据列表（return_defaults=True 时包含生成的默认值）

    e.g.::

        # 基础用法 - 高性能批量插入
        result = await bulk_insert(
            session,
            User,
            values=[
                {"name": "Alice", "email": "alice@test.com"},
                {"name": "Bob", "email": "bob@test.com"},
            ]
        )
        print(f"成功插入 {result.rowcount} 条")

        # 获取自增主键
        result = await bulk_insert(
            session,
            User,
            values=[{"name": "Charlie"}],
            return_defaults=True
        )
        print(result.data[0].get("id"))  # 获取生成的 ID

        # 大数据量导入（如数据迁移）
        batch_size = 1000
        for i in range(0, len(all_data), batch_size):
            batch = all_data[i:i + batch_size]
            await bulk_insert(session, User, values=batch, flush=True)

        +++++[更多详见参数或源码]+++++
    """
    if not values:
        return BulkInserted(ok=True, rowcount=0)

    def _bulk_insert(sync_session):
        return sync_session.bulk_insert_mappings(
            model, values, return_defaults=return_defaults
        )

    await session.run_sync(_bulk_insert)

    if flush:
        await session.flush()

    return BulkInserted(
        ok=True, rowcount=len(values), data=values if return_defaults else []
    )


# -----------------------------------------------------------------------------
# 原生 SQL 执行
# -----------------------------------------------------------------------------


async def raw(
        session: AsyncSession,
        sql: str,
        params: dict[str, Any] | None = None,
        *,
        autocommit: bool = False,
        flush: bool = False,
) -> Result:
    """执行原生 SQL 语句

    Args:
        session: 数据库会话
        sql: SQL 语句，支持命名参数占位符 :name
        params: 参数字典
        autocommit: 自动提交事务（非查询语句）
        flush: 刷入数据库但不提交

    Returns:
        SQLAlchemy Result 对象，常用方法：
            - fetchall() / fetchone() 获取结果
            - rowcount 影响行数
            - returns_rows 是否返回数据
            - async for row in result 流式遍历

    e.g.::

        # SELECT
        result = await raw(session, "SELECT * FROM users WHERE id = :id", {"id": 1})
        users = [r._asdict() for r in result.fetchall()]

        # 流式查询
        result = await raw(session, "SELECT * FROM large_table")
        async for row in result:
            process(row._asdict())

        # INSERT/UPDATE/DELETE
        result = await raw(session, "DELETE FROM users WHERE id = :id", {"id": 1}, autocommit=True)
        print(f"删除 {result.rowcount} 条")
    """
    if not sql or not sql.strip():
        raise ValueError("SQL statement cannot be empty")

    if params is not None and not isinstance(params, dict):
        raise TypeError(f"params must be dict or None, got {type(params).__name__}")

    result = await session.execute(text(sql), params)

    if autocommit:
        await session.commit()
    elif flush:
        await session.flush()

    return result


# -----------------------------------------------------------------------------
# CRUD Mixin - 供 DeclarativeBase 继承，使模型自带 CRUD 方法
# -----------------------------------------------------------------------------


class CRUDMixin:
    """CRUD Mixin 类，供 SQLAlchemy DeclarativeBase 继承

    使模型类自带异步 CRUD 操作方法，无需显式传递 model 参数

    e.g.::

        from sqlalchemy import BigInteger, String
        from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
        from toollib.sqlacrud import CRUDMixin

        class DeclBase(DeclarativeBase, CRUDMixin):
            pass


        class User(DeclBase):
            __tablename__ = "users"

            id = mapped_column(BigInteger, primary_key=True, comment="主键")
            name = mapped_column(String(50), nullable=True, comment="名称")


        # 使用
        async def example(session: AsyncSession):
            # 查询
            user = await User.fetch_one(session, where={"id": 1})
            users = await User.fetch_all(session, limit=10)

            # 创建
            created = await User.create(session, values={"name": "Tom"})

            # 删除
            deleted = await User.delete(session, where={"id": 1})

            # 更新
            updated = await User.update(session, values={"name": "New"}, where={"id": 1})

            # ...

        +++++[更多详见参数或源码]+++++
    """

    @staticmethod
    def format_row(
            row,
            columns: Sequence[str],
            converters: dict[str, Callable] | None = None,
    ) -> dict[str, Any]:
        """格式化单行结果

        Args:
            row: 数据库结果行
            columns: 列名列表
            converters: 字段转换器

        Returns:
            字典格式的单行数据
        """
        return format_row(row, columns, converters)

    @staticmethod
    def format_rows(
            rows,
            columns: Sequence[str],
            converters: dict[str, Callable] | None = None,
    ) -> list[dict[str, Any]]:
        """格式化多行结果

        Args:
            rows: 数据库结果行列表
            columns: 列名列表
            converters: 字段转换器

        Returns:
            字典列表格式的多行数据
        """
        return format_rows(rows, columns, converters)

    @classmethod
    async def fetch_one(
            cls,
            session: AsyncSession,
            *,
            columns: Sequence[str] | None = None,
            where: dict[str, Any]
            | ColumnElement[Any]
            | Sequence[ColumnElement[Any]]
            | None = None,
            order_by: str | Sequence[str] | None = None,
            converters: dict[str, Callable] | None = None,
    ) -> dict[str, Any] | None:
        """查询单条记录

        Args:
            session: 数据库会话
            columns: 指定返回列，None 返回所有列
            where: 过滤条件，支持：
                - None: 无过滤条件
                - dict: {"name": "Tom", "age": 18}
                - ColumnElement: User.age > 18
                - Sequence[ColumnElement]: [User.age > 18, User.status == 1]
            order_by: 排序字段，支持多字段。字符串前面加 "-" 表示降序
            converters: 字段转换器，{"column": func}

        Returns:
            单条记录字典
        """
        return await fetch_one(
            session, cls, columns=columns, where=where, order_by=order_by, converters=converters
        )

    @classmethod
    async def fetch_all(
            cls,
            session: AsyncSession,
            *,
            columns: Sequence[str] | None = None,
            where: dict[str, Any]
            | ColumnElement[Any]
            | Sequence[ColumnElement[Any]]
            | None = None,
            order_by: str | Sequence[str] | None = None,
            offset: int | None = None,
            limit: int | None = None,
            converters: dict[str, Callable] | None = None,
    ) -> list[dict[str, Any]]:
        """查询多条记录

        Args:
            session: 数据库会话
            columns: 指定返回列
            where: 过滤条件，支持：
                - None: 无过滤条件
                - dict: {"name": "Tom", "age": 18}
                - ColumnElement: User.age > 18
                - Sequence[ColumnElement]: [User.age > 18, User.status == 1]
            order_by: 排序字段，支持 "-column" 降序
            offset: 分页偏移
            limit: 分页限制
            converters: 字段转换器，{"column": func}

        Returns:
            记录字典列表
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
            where: dict[str, Any]
            | ColumnElement[Any]
            | Sequence[ColumnElement[Any]]
            | None = None,
    ) -> int:
        """统计记录数

        返回符合条件的记录总数，用于分页等场景。

        Args:
            session: 数据库会话
            where: 过滤条件，支持：
                - dict: {"name": "Tom", "age": 18}
                - ColumnElement: User.age > 18
                - Sequence[ColumnElement]: [User.age > 18, User.status == 1]
                - None: 统计全部记录

        Returns:
            记录数量
        """
        return await count(session, cls, where=where)

    @classmethod
    async def create(
            cls,
            session: AsyncSession,
            *,
            values: dict[str, Any],
            on_conflict: dict[str, Any] | None = None,
            returning: bool = True,
            flush: bool = False,
    ) -> Created:
        """创建单条记录

        根据提供的值创建新记录，如果 on_conflict 指定的条件已存在，
        则返回冲突记录而不创建新记录。

        Args:
            session: 数据库会话
            values: 要创建的数据字典
            on_conflict: 唯一性冲突检查，如果存在则返回 False。
                        如 {"email": "user@test.com"} 会检查邮箱是否已存在。
            returning: 是否返回创建后的数据字典，False 时只返回 success 状态。
            flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

        Returns:
            Created: 创建操作结果
                - ok: True 表示创建成功，False 表示记录已存在
                - rowcount: 影响行数，成功为1，冲突为0
                - data: 创建后的数据字典（returning=True 时）
        """
        return await create(
            session,
            cls,
            values=values,
            on_conflict=on_conflict,
            returning=returning,
            flush=flush,
        )

    @classmethod
    async def delete(
            cls,
            session: AsyncSession,
            *,
            where: dict[str, Any]
            | ColumnElement[Any]
            | Sequence[ColumnElement[Any]]
            | None = None,
            allow_all: bool = False,
            flush: bool = False,
    ) -> Deleted:
        """删除记录

        根据条件删除记录。默认情况下需要提供 where 条件，防止误删全表。
        如需删除全部记录，请设置 allow_all=True。

        Args:
            session: 数据库会话
            where: 过滤条件，支持：
                - None: 删除全部记录（需 allow_all=True）
                - dict: {"id": 1}
                - ColumnElement: User.id == 1
                - Sequence[ColumnElement]: [User.age < 18, User.status == 0]
            allow_all: 是否允许无条件删除（全表删除），默认 False
            flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

        Returns:
            Deleted: 删除操作结果
                - ok: True 表示删除成功（rowcount > 0），False 表示未找到匹配记录
                - rowcount: 删除的行数
        """
        return await delete(session, cls, where=where, allow_all=allow_all, flush=flush)

    @classmethod
    async def update(
            cls,
            session: AsyncSession,
            *,
            values: dict[str, Any],
            where: dict[str, Any]
            | ColumnElement[Any]
            | Sequence[ColumnElement[Any]]
            | None = None,
            allow_all: bool = False,
            exclude_none: bool = True,
            returning: bool = False,
            flush: bool = False,
    ) -> Updated:
        """更新记录

        根据条件更新符合条件的记录。默认情况下需要提供 where 条件，防止误更新全表。
        如需更新全部记录，请设置 allow_all=True。

        Args:
            session: 数据库会话
            values: 要更新的数据字典
            where: 过滤条件，支持：
                - None: 更新全部记录（需 allow_all=True）
                - dict: {"id": 1}
                - ColumnElement: User.id == 1
                - Sequence[ColumnElement]: [User.age < 18, User.status == 0]
            allow_all: 是否允许无条件更新（全表更新），默认 False
            exclude_none: 是否自动排除值为 None 的字段，True 时跳过 None 值
            returning: 是否返回更新后的数据字典（不支持全表更新）。需要额外查询。
            flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

        Returns:
            Updated: 更新操作结果
                - ok: True 表示更新成功（rowcount > 0），False 表示未找到匹配记录
                - rowcount: 受影响的行数
                - data: 更新后的数据字典（returning=True 时，不支持全表更新）
        """
        return await update(
            session,
            cls,
            values=values,
            where=where,
            allow_all=allow_all,
            exclude_none=exclude_none,
            returning=returning,
            flush=flush,
        )

    @classmethod
    async def upsert(
            cls,
            session: AsyncSession,
            *,
            values: dict[str, Any],
            keys: Sequence[str],
            updates: Sequence[str] | None = None,
            flush: bool = False,
    ) -> Upserted:
        """存在则更新，不存在则创建（Upsert）

        根据唯一键判断记录是否存在，不存在则创建，存在则更新。
        自动根据数据库方言选择最优实现：
        - PostgreSQL/SQLite: INSERT ... ON CONFLICT DO UPDATE
        - MySQL: INSERT ... ON DUPLICATE KEY UPDATE
        - 其他: 先查后改（fallback）

        Args:
            session: 数据库会话
            values: 完整数据字典
            keys: 唯一键字段列表，用于判断记录是否存在，如 ("id",), ("email",)
            updates: 指定更新时的字段列表，None 表示更新除 keys 外的所有字段
            flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

        Returns:
            Upserted: Upsert 操作结果
                - data: 数据对象（SQLAlchemy 模型实例）
                - action: 操作类型 - "insert"(新建) / "update"(更新) / "noop"(无变化)
        """
        return await upsert(
            session, cls, values=values, keys=keys, updates=updates, flush=flush
        )

    @classmethod
    async def batch_create(
            cls,
            session: AsyncSession,
            *,
            values: list[dict[str, Any]],
            returning: bool = True,
            flush: bool = False,
    ) -> BatchCreated:
        """批量创建多条记录

        一次性创建多条记录，性能优于循环调用 create()。

        Args:
            session: 数据库会话
            values: 数据字典列表，每个字典创建一条记录
            returning: 是否返回创建后的数据字典列表，False 时只返回 count。
            flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

        Returns:
            BatchCreated: 批量创建结果
                - ok: 总是 True
                - rowcount: 实际创建的记录数
                - data: 创建后的数据列表（returning=True 时）
        """
        return await batch_create(
            session, cls, values=values, returning=returning, flush=flush
        )

    @classmethod
    async def bulk_insert(
            cls,
            session: AsyncSession,
            *,
            values: list[dict[str, Any]],
            return_defaults: bool = False,
            flush: bool = False,
    ) -> BulkInserted:
        """高性能批量插入记录

        使用 SQLAlchemy 的 bulk_insert_mappings 实现，跳过 ORM 的事件监听和关系处理，
        性能显著优于 batch_create()，适合大数据量导入场景。

        注意：此方法不会触发 ORM 事件（如 @event.listens_for）、不会处理关系关联、
        不会自动处理关联对象的级联操作。如需完整 ORM 功能，请使用 batch_create()。

        Args:
            session: 数据库会话
            values: 数据字典列表，每个字典插入一条记录
            return_defaults: 是否获取数据库生成的默认值（如自增主键）。
                            True 时会在返回结果中包含这些值，但会有轻微性能损耗。
            flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

        Returns:
            BulkInserted: 批量插入结果
                - ok: 总是 True（除非发生异常）
                - rowcount: 实际插入的记录数
                - data: 插入的数据列表（return_defaults=True 时包含生成的默认值）
        """
        return await bulk_insert(
            session, cls, values=values, return_defaults=return_defaults, flush=flush
        )

    @classmethod
    async def raw(
            cls,
            session: AsyncSession,
            sql: str,
            params: dict[str, Any] | None = None,
            *,
            autocommit: bool = False,
            flush: bool = False,
    ) -> Result:
        """执行原生 SQL 语句

        Args:
            session: 数据库会话
            sql: SQL 语句，支持命名参数占位符 :name
            params: 参数字典
            autocommit: 自动提交事务（非查询语句）
            flush: 刷入数据库但不提交

        Returns:
            SQLAlchemy Result 对象，常用方法：
                - fetchall() / fetchone() 获取结果
                - rowcount 影响行数
                - returns_rows 是否返回数据
                - async for row in result 流式遍历
        """
        return await raw(session, sql, params, autocommit=autocommit, flush=flush)
