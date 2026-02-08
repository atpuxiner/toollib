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
from dataclasses import dataclass, field
from typing import Literal, Any

from sqlalchemy import (
    select,
    func,
    text,
    update as sa_update,
    delete as sa_delete,
    inspect,
)
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
    "fetch_one",
    "fetch_all",
    "count",
    "create",
    "delete",
    "update",
    "upsert",
    "batch_create",
    "bulk_insert",
    "fetch_sql_one",
    "fetch_sql_all",
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
    data: dict[str, Any] | None = None  # 创建的数据

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


def _columns(model) -> list[str]:
    """获取模型所有列名"""
    return [column.name for column in inspect(model).mapper.columns]


def _to_dict(
        model, fields: tuple[str, ...] | list[str] | None = None
) -> dict[str, Any]:
    """模型实例转字典"""
    if not model:
        return {}
    if fields is None:
        fields = _columns(model)
    return {field: getattr(model, field) for field in fields if hasattr(model, field)}


def _parse_order_by(model, order_by: str | tuple[str, ...] | list[str]) -> list:
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
    for order_field in order_by:
        if order_field.startswith("-"):
            column_name = order_field[1:]
            desc = True
        else:
            column_name = order_field
            desc = False

        if hasattr(model, column_name):
            column = getattr(model, column_name)
            result.append(column.desc() if desc else column.asc())

    return result


def _format_row(row, fields: tuple[str, ...] | list[str]) -> dict[str, Any]:
    """格式化单行结果"""
    if not row:
        return {}
    return row._asdict() if hasattr(row, "_asdict") else dict(zip(fields, row))


def _format_rows(rows, fields: tuple[str, ...] | list[str]) -> list[dict[str, Any]]:
    """格式化多行结果"""
    if not rows:
        return []
    return [
        row._asdict() if hasattr(row, "_asdict") else dict(zip(fields, row))
        for row in rows
    ]


# -----------------------------------------------------------------------------
# 查询操作
# -----------------------------------------------------------------------------


async def fetch_one(
        session: AsyncSession,
        model,
        *,
        columns: tuple[str, ...] | list[str] | None = None,
        where: dict[str, Any] | None = None,
        order_by: str | tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any] | None:
    """查询单条记录

    Args:
        columns: 指定返回列，None 返回所有列
        where: 过滤条件
        order_by: 排序字段，支持多字段。字符串前面加 "-" 表示降序，
                 如 "-created_at" 或 ("name", "-created_at") 或 ["name", "-created_at"]

    Returns:
        单条记录字典或 None

    e.g.::

        # 单字段排序
        user = await fetch_one(session, User, order_by="-created_at")

        # 多字段排序
        user = await fetch_one(session, User, order_by=("name", "-created_at"))

        +++++[更多详见参数或源码]+++++
    """
    selected_columns = tuple(
        getattr(model, col)
        for col in (columns or _columns(model))
        if hasattr(model, col)
    )
    stmt = select(*selected_columns).select_from(model)

    if where:
        stmt = stmt.filter_by(**where)
    if order_by:
        stmt = stmt.order_by(*_parse_order_by(model, order_by))

    result = await session.execute(stmt.limit(1))
    return _format_row(result.fetchone(), columns or _columns(model))


async def fetch_all(
        session: AsyncSession,
        model,
        *,
        columns: tuple[str, ...] | list[str] | None = None,
        where: dict[str, Any] | None = None,
        order_by: str | tuple[str, ...] | list[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
) -> list[dict[str, Any]]:
    """查询多条记录

    Args:
        columns: 指定返回列
        where: 过滤条件
        order_by: 排序字段，支持多字段。字符串前面加 "-" 表示降序，
                 如 "-created_at" 或 ("name", "-created_at") 或 ["name", "-created_at"]
        offset: 分页偏移
        limit: 分页限制

    e.g.::

        # 单字段降序
        users = await fetch_all(session, User, order_by="-created_at", limit=10)

        # 多字段排序
        users = await fetch_all(session, User, order_by=("name", "-created_at"), offset=0, limit=20)

        +++++[更多详见参数或源码]+++++
    """
    selected_columns = tuple(
        getattr(model, col)
        for col in (columns or _columns(model))
        if hasattr(model, col)
    )
    stmt = select(*selected_columns).select_from(model)

    if where:
        stmt = stmt.filter_by(**where)
    if order_by:
        stmt = stmt.order_by(*_parse_order_by(model, order_by))
    if offset:
        stmt = stmt.offset(offset)
    if limit:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return _format_rows(result.fetchall(), columns or _columns(model))


async def count(
        session: AsyncSession,
        model,
        *,
        where: dict[str, Any] | None = None,
) -> int:
    """统计记录数

    返回符合条件的记录总数，用于分页等场景。

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        where: 过滤条件，None 则统计全部记录

    Returns:
        记录数量

    e.g.::

        # 统计所有用户
        total = await count(session, User)

        # 统计正常用户
        active_count = await count(session, User, where={"status": 1})

        +++++[更多详见参数或源码]+++++
    """
    stmt = select(func.count()).select_from(model)
    if where:
        stmt = stmt.filter_by(**where)
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
        where: dict[str, Any],
        flush: bool = False,
) -> Deleted:
    """删除记录

    根据条件删除记录。where 参数必须提供以防止全表删除。

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        where: 过滤条件（必须），如 {"id": 1}，防止意外全表删除
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

        +++++[更多详见参数或源码]+++++
    """
    if not where:
        raise ValueError("'where' is required to prevent full-table delete")

    result = await session.execute(sa_delete(model).filter_by(**where))
    if flush:
        await session.flush()

    rowcount = result.rowcount or 0
    return Deleted(ok=rowcount > 0, rowcount=rowcount)


async def update(
        session: AsyncSession,
        model,
        *,
        values: dict[str, Any],
        where: dict[str, Any],
        exclude_none: bool = True,
        returning: bool = False,
        flush: bool = False,
) -> Updated:
    """更新记录

    根据条件更新符合条件的记录。where 参数必须提供以防止全表更新。

    Args:
        session: 数据库会话
        model: SQLAlchemy 模型类
        values: 要更新的数据字典
        where: 过滤条件（必须），如 {"id": 1}，防止意外全表更新
        exclude_none: 是否自动排除值为 None 的字段，True 时跳过 None 值
        returning: 是否返回更新后的数据字典，需要额外查询。
        flush: 是否立即刷入数据库，默认 False 由调用方控制事务提交

    Returns:
        Updated: 更新操作结果
            - ok: True 表示更新成功（rowcount > 0），False 表示未找到匹配记录
            - rowcount: 受影响的行数
            - data: 更新后的数据字典（returning=True 时）

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

        +++++[更多详见参数或源码]+++++
    """
    if not where:
        raise ValueError("'where' is required to prevent full-table update")

    data = (
        {k: v for k, v in values.items() if v is not None} if exclude_none else values
    )
    if not data:
        return Updated(ok=False, rowcount=0)

    result = await session.execute(sa_update(model).filter_by(**where).values(**data))
    if flush:
        await session.flush()

    rowcount = result.rowcount or 0
    updated_data = (
        await fetch_one(session, model, where=where)
        if (returning and rowcount > 0)
        else None
    )

    return Updated(ok=rowcount > 0, rowcount=rowcount, data=updated_data)


async def upsert(
        session: AsyncSession,
        model,
        *,
        values: dict[str, Any],
        keys: tuple[str, ...] | list[str],
        update: tuple[str, ...] | list[str] | None = None,
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
        update: 指定更新时的字段列表，None 表示更新除 keys 外的所有字段
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
            update=("name",)  # 只更新 name，email 不变
        )

        +++++[更多详见参数或源码]+++++
    """
    if not keys or not all(key in values for key in keys):
        raise ValueError("'keys' must be non-empty and exist in values")

    dialect = _dialect(session)

    if dialect in ("postgresql", "mysql", "sqlite"):
        return await _upsert_native(
            session, model, values, keys, update, dialect, flush
        )
    return await _upsert_fallback(session, model, values, keys, update, flush)


async def _upsert_native(
        session: AsyncSession,
        model,
        values: dict[str, Any],
        keys: tuple[str, ...] | list[str],
        update_columns: tuple[str, ...] | list[str] | None,
        dialect: str,
        flush: bool = False,
) -> Upserted:
    """使用数据库原生 upsert 语法实现

    根据数据库方言使用对应的 upsert 语法。
    """
    update_cols = update_columns or tuple(col for col in values if col not in keys)
    update_dict = {col: values[col] for col in update_cols if col in values}

    # 选择 insert 构造器
    insert_map = {
        "postgresql": pg_insert,
        "mysql": mysql_insert,
        "sqlite": sqlite_insert,
    }
    insert_func = insert_map.get(dialect, pg_insert)

    stmt = insert_func(model).values(**values)

    if update_dict:
        if dialect == "mysql":
            stmt = stmt.on_duplicate_key_update(**update_dict)
        else:
            stmt = stmt.on_conflict_do_update(
                index_elements=keys, set_=update_dict)
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
        action = "insert" if rowcount == 1 else "update"
    else:
        action = "update" if update_dict else "noop"

    return Upserted(data=obj, action=action)


async def _upsert_fallback(
        session: AsyncSession,
        model,
        values: dict[str, Any],
        keys: tuple[str, ...] | list[str],
        update_columns: tuple[str, ...] | list[str] | None,
        flush: bool = False,
) -> Upserted:
    """Upsert 的通用 fallback 实现（先查后改）

    先查询记录是否存在，存在则更新，不存在则创建。
    用于不支持原生 upsert 语法的数据库。
    """
    where = {k: values[k] for k in keys if k in values}
    existing = await fetch_one(session, model, where=where)

    if existing:
        cols = update_columns or tuple(col for col in values if col not in keys)
        update_data = {col: values[col] for col in cols if col in values}
        if update_data:
            await session.execute(
                sa_update(model).filter_by(**where).values(**update_data)
            )
            if flush:
                await session.flush()
            existing = await fetch_one(session, model, where=where)
        action = "update" if update_data else "noop"
        return Upserted(data=model(**existing), action=action)

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
# 原生 SQL 查询
# -----------------------------------------------------------------------------


async def fetch_sql_one(
        session: AsyncSession,
        sql: str,
        params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """执行原生 SQL 查询单条记录

    当 ORM 查询无法满足需求时，可以直接执行 SQL 语句。

    Args:
        session: 数据库会话
        sql: 原生 SQL 语句字符串，支持参数占位符，如 :name
        params: SQL 参数字典，对应 SQL 中的命名参数

    Returns:
        单条记录字典，未找到返回空字典 {}

    e.g.::

        sql = "SELECT * FROM users WHERE email = :email LIMIT 1"
        user = await fetch_sql_one(
            session,
            sql,
            params={"email": "user@test.com"}
        )
        print(user.get("name"))

        +++++[更多详见参数或源码]+++++
    """
    result = await session.execute(text(sql), params)
    row = result.fetchone()
    return row._asdict() if row else {}


async def fetch_sql_all(
        session: AsyncSession,
        sql: str,
        params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """执行原生 SQL 查询多条记录

    当 ORM 查询无法满足需求时，可以直接执行 SQL 语句。

    Args:
        session: 数据库会话
        sql: 原生 SQL 语句字符串，支持参数占位符，如 :name
        params: SQL 参数字典，对应 SQL 中的命名参数

    Returns:
        记录字典列表，未找到返回空列表 []

    e.g.::

        sql = "SELECT id, name FROM users WHERE status = :status ORDER BY created_at"
        users = await fetch_sql_all(
            session,
            sql,
            params={"status": 1}
        )
        for user in users:
            print(user["name"])

        +++++[更多详见参数或源码]+++++
    """
    result = await session.execute(text(sql), params)
    return [row._asdict() for row in result.fetchall()]


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

    @classmethod
    async def fetch_one(
            cls,
            session: AsyncSession,
            *,
            columns: tuple[str, ...] | list[str] | None = None,
            where: dict[str, Any] | None = None,
            order_by: str | tuple[str, ...] | list[str] | None = None,
    ) -> dict[str, Any] | None:
        """查询单条记录

        Args:
            session: 数据库会话
            columns: 指定返回列，None 返回所有列
            where: 过滤条件
            order_by: 排序字段，支持 "-field" 降序

        Returns:
            单条记录字典或 None
        """
        return await fetch_one(
            session, cls, columns=columns, where=where, order_by=order_by
        )

    @classmethod
    async def fetch_all(
            cls,
            session: AsyncSession,
            *,
            columns: tuple[str, ...] | list[str] | None = None,
            where: dict[str, Any] | None = None,
            order_by: str | tuple[str, ...] | list[str] | None = None,
            offset: int | None = None,
            limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """查询多条记录

        Args:
            session: 数据库会话
            columns: 指定返回列
            where: 过滤条件
            order_by: 排序字段
            offset: 分页偏移
            limit: 分页限制

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
        )

    @classmethod
    async def count(
            cls,
            session: AsyncSession,
            *,
            where: dict[str, Any] | None = None,
    ) -> int:
        """统计记录数

        Args:
            session: 数据库会话
            where: 过滤条件

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

        Args:
            session: 数据库会话
            values: 要创建的数据字典
            on_conflict: 唯一性冲突检查
            returning: 是否返回创建后的数据
            flush: 是否立即刷入数据库

        Returns:
            Created: 创建操作结果
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
            where: dict[str, Any],
            flush: bool = False,
    ) -> Deleted:
        """删除记录

        Args:
            session: 数据库会话
            where: 过滤条件（必须）
            flush: 是否立即刷入数据库

        Returns:
            Deleted: 删除操作结果
        """
        return await delete(session, cls, where=where, flush=flush)

    @classmethod
    async def update(
            cls,
            session: AsyncSession,
            *,
            values: dict[str, Any],
            where: dict[str, Any],
            exclude_none: bool = True,
            returning: bool = False,
            flush: bool = False,
    ) -> Updated:
        """更新记录

        Args:
            session: 数据库会话
            values: 要更新的数据字典
            where: 过滤条件（必须）
            exclude_none: 是否排除 None 值
            returning: 是否返回更新后的数据
            flush: 是否立即刷入数据库

        Returns:
            Updated: 更新操作结果
        """
        return await update(
            session,
            cls,
            values=values,
            where=where,
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
            keys: tuple[str, ...] | list[str],
            update: tuple[str, ...] | list[str] | None = None,
            flush: bool = False,
    ) -> Upserted:
        """存在则更新，不存在则创建（Upsert）

        Args:
            session: 数据库会话
            values: 完整数据字典
            keys: 唯一键字段列表
            update: 指定更新的字段列表
            flush: 是否立即刷入数据库

        Returns:
            Upserted: Upsert 操作结果
        """
        return await upsert(
            session, cls, values=values, keys=keys, update=update, flush=flush
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

        Args:
            session: 数据库会话
            values: 数据字典列表
            returning: 是否返回创建后的数据
            flush: 是否立即刷入数据库

        Returns:
            BatchCreated: 批量创建结果
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

        Args:
            session: 数据库会话
            values: 数据字典列表
            return_defaults: 是否获取数据库生成的默认值
            flush: 是否立即刷入数据库

        Returns:
            BulkInserted: 批量插入结果
        """
        return await bulk_insert(
            session, cls, values=values, return_defaults=return_defaults, flush=flush
        )

    @classmethod
    async def fetch_sql_one(
            cls,
            session: AsyncSession,
            sql: str,
            params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """执行原生 SQL 查询单条记录

        Args:
            session: 数据库会话
            sql: 原生 SQL 语句
            params: SQL 参数

        Returns:
            单条记录字典
        """
        return await fetch_sql_one(session, sql, params)

    @classmethod
    async def fetch_sql_all(
            cls,
            session: AsyncSession,
            sql: str,
            params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """执行原生 SQL 查询多条记录

        Args:
            session: 数据库会话
            sql: 原生 SQL 语句
            params: SQL 参数

        Returns:
            记录字典列表
        """
        return await fetch_sql_all(session, sql, params)
