import asyncio
import inspect

import pytest
from sqlalchemy import Integer, String, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from toollib.sqlacrud import (
    CRUDMixin,
    batch_create,
    bulk_insert,
    count,
    create,
    delete,
    fetch_all,
    fetch_one,
    format_row,
    format_rows,
    raw,
    update,
    upsert,
)


class Base(CRUDMixin, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column("user_id", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("user_name", String(50), unique=True, nullable=False)
    note: Mapped[str | None] = mapped_column("user_note", String(50), nullable=True)


def _make_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def init():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(init())
    return engine, session_factory


def _run(coro):
    engine, session_factory = _make_db()

    async def main():
        async with session_factory() as session:
            return await coro(session, session_factory)

    try:
        return asyncio.run(main())
    finally:
        asyncio.run(engine.dispose())


def test_fetch_format_and_where_variants():
    async def scenario(session, _):
        inserted = await bulk_insert(session, User, values=[{"name": "a", "note": "A"}, {"name": "b", "note": "B"}])
        assert inserted.ok
        assert inserted.rowcount == 2

        row = await fetch_one(
            session,
            User,
            columns=["name"],
            where={"name": "a"},
            converters={"name": str.upper},
        )
        assert row == {"name": "A"}

        row = await fetch_one(session, User, columns=["user_name"], where=User.name == "a")
        assert row == {"user_name": "a"}

        rows = await fetch_all(
            session,
            User,
            where=(expr for expr in [User.name == "a"]),
            order_by="-name",
        )
        assert [item["name"] for item in rows] == ["a"]

        rows = await fetch_all(session, User, where=text("user_name = 'b'"))
        assert [item["name"] for item in rows] == ["b"]

        assert await count(session, User) == 2
        assert await fetch_one(session, User, where={"name": "missing"}) is None
        with pytest.raises(ValueError):
            await fetch_one(session, User, where={"name": "a", "user_name": "b"})
        with pytest.raises(ValueError):
            await fetch_one(session, User, columns=["name", "user_name"])
        assert format_row(None, ["name"]) == {}
        assert format_rows([], ["name"]) == []

    _run(scenario)


def test_create_conflict_is_atomic_and_validated():
    async def scenario(session, _):
        created = await create(session, User, values={"name": "a", "note": "first"})
        assert created.ok
        assert created.rowcount == 1
        assert created.data is not None
        assert created.data["id"] > 0

        conflict = await create(
            session,
            User,
            values={"name": "a", "note": "second"},
            on_conflict={"name": "a"},
        )
        assert not conflict.ok
        assert conflict.rowcount == 0
        assert conflict.data is not None
        assert conflict.data["note"] == "first"

        mismatch = await create(
            session,
            User,
            values={"name": "b", "note": "inserted"},
            on_conflict={"name": "ghost"},
        )
        assert mismatch.ok
        assert mismatch.data is not None
        assert mismatch.data["name"] == "b"

        with pytest.raises(ValueError):
            await create(session, User, values={"name": "c"}, on_conflict={})
        with pytest.raises(TypeError):
            await create(session, User, values={"name": "c"}, on_conflict=[("name", "c")])
        with pytest.raises(ValueError):
            await create(session, User, values={"name": "c", "note": "n"}, on_conflict={"note": "n"})
        with pytest.raises(ValueError):
            await create(
                session,
                User,
                values={"name": "c", "note": "n"},
                on_conflict={"name": "c", "note": "n"},
            )
        with pytest.raises(ValueError):
            await create(session, User, values={"name": "c"}, on_conflict={"name": None})

        conflict_without_return = await create(
            session,
            User,
            values={"name": "a"},
            on_conflict={"name": "a"},
            returning=False,
        )
        assert not conflict_without_return.ok
        assert conflict_without_return.data is not None
        assert conflict_without_return.data["name"] == "a"

        plain = await create(session, User, values={"name": "c"}, returning=False)
        assert plain.ok
        assert plain.data is None

        by_db_name = await create(session, User, values={"user_name": "db-name", "note": "db"})
        assert by_db_name.ok
        assert by_db_name.data is not None
        assert by_db_name.data["name"] == "db-name"

    _run(scenario)


def test_update_null_columns_and_returning_guard():
    async def scenario(session, _):
        await create(session, User, values={"name": "a", "note": "keep"})

        skipped = await update(session, User, values={"note": None}, where={"id": 1})
        assert not skipped.ok
        row = await fetch_one(session, User, where={"id": 1})
        assert row is not None
        assert row["note"] == "keep"

        cleared = await update(
            session,
            User,
            values={"note": None},
            where={"id": 1},
            null_columns=["note"],
            returning=True,
        )
        assert cleared.ok
        assert cleared.data is not None
        assert cleared.data["note"] is None

        renamed = await update(
            session,
            User,
            values={"name": "renamed"},
            where={"name": "a"},
            returning=True,
        )
        assert renamed.ok
        assert renamed.data is not None
        assert renamed.data["name"] == "renamed"

        with pytest.raises(ValueError):
            await update(session, User, values={"id": 99}, where={"id": 1}, returning=True)
        with pytest.raises(ValueError):
            await update(
                session,
                User,
                values={"note": "x", "user_note": "y"},
                where={"id": 1},
            )

        with pytest.raises(ValueError):
            await update(
                session,
                User,
                values={"note": "x"},
                where=User.name == "a",
                returning=True,
            )
        with pytest.raises(ValueError):
            await update(session, User, values={"unknown": "x"}, where={"id": 1})

    _run(scenario)


def test_upsert_and_bulk_insert_return_defaults():
    async def scenario(session, _):
        first = await upsert(
            session,
            User,
            values={"name": "a", "note": "1"},
            keys=["name"],
            returning=True,
        )
        assert first.ok
        assert first.data is not None
        assert first.data["note"] == "1"

        second = await upsert(
            session,
            User,
            values={"name": "a", "note": "2"},
            keys=("name",),
            updates=("name", "note"),
            returning=True,
        )
        assert second.ok
        assert second.data is not None
        assert second.data["note"] == "2"
        assert second.data["id"] == first.data["id"]

        bulk = await bulk_insert(
            session,
            User,
            values=[{"name": "b"}, {"name": "c", "note": "c"}],
            return_defaults=True,
        )
        assert bulk.rowcount == 2
        assert len(bulk.data) == 2
        assert all(item["id"] > 0 for item in bulk.data)

        plain = await bulk_insert(session, User, values=[{"name": "d"}], return_defaults=False)
        assert plain.ok
        assert plain.data == []

        no_return = await upsert(
            session,
            User,
            values={"name": "e", "note": "e"},
            keys=("name",),
            returning=False,
        )
        assert no_return.ok
        assert no_return.data is None

        with pytest.raises(ValueError):
            await upsert(
                session,
                User,
                values={"name": "f"},
                keys=("name",),
                updates=("note",),
            )
        with pytest.raises(ValueError):
            await upsert(
                session,
                User,
                values={"id": 100, "name": "f"},
                keys=("name",),
                updates=("id",),
            )
        with pytest.raises(ValueError):
            await upsert(session, User, values={"note": "x"}, keys=("note",))
        with pytest.raises(ValueError):
            await upsert(
                session,
                User,
                values={"name": "g", "note": "x"},
                keys=("name", "note"),
            )
        with pytest.raises(ValueError):
            await bulk_insert(session, User, values=[{}])

    _run(scenario)


def test_batch_create_and_empty_batch():
    async def scenario(session, _):
        batch = await batch_create(session, User, values=[{"name": "batch-a"}, {"name": "batch-b"}])
        assert batch.ok
        assert batch.rowcount == 2
        assert all(item["id"] > 0 for item in batch.data)

        empty = await batch_create(session, User, values=[])
        assert empty.ok
        assert empty.rowcount == 0
        assert empty.data == []

    _run(scenario)


def test_delete_raw_and_crudmixin():
    async def scenario(session, session_factory):
        signature = inspect.signature(User.create)
        assert "session" in signature.parameters
        assert "values" in signature.parameters
        assert "model" not in signature.parameters

        created = await User.create(session, values={"name": "a", "note": "x"})
        assert created.ok
        assert await User.count(session) == 1

        row = await User.fetch_one(session, where={"name": "a"})
        assert row is not None
        assert row["note"] == "x"

        deleted = await User.delete(session, where={"name": "a"})
        assert deleted.ok
        assert deleted.rowcount == 1

        with pytest.raises(ValueError):
            await delete(session, User)

        result = await User.raw(session, "SELECT :value AS value", {"value": 7})
        assert result.scalar_one() == 7

        with pytest.raises(ValueError):
            await raw(session, "   ")
        with pytest.raises(TypeError):
            await raw(session, "SELECT 1", params=[1])

        await User.create(session, values={"name": "committed"}, returning=False)
        result = await raw(session, "SELECT 8 AS value", commit=True)
        assert result.scalar_one() == 8
        async with session_factory() as other_session:
            assert await count(other_session, User, where={"name": "committed"}) == 1

    _run(scenario)
