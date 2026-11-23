import asyncio
import os
from urllib.parse import quote_plus

import pytest
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from toollib.sqlacrud import bulk_insert, count, create, delete, fetch_all, fetch_one, raw, update, upsert

_REQUIRED_ENV = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_USERNAME", "MYSQL_PASSWORD")
if not all(os.getenv(name) for name in _REQUIRED_ENV):
    pytest.skip("MySQL environment variables are not set", allow_module_level=True)

_TABLE = "toollib_sqlacrud_mysql_live"
Base = declarative_base()


class MysqlUser(Base):
    __tablename__ = _TABLE

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column("user_email", String(120), unique=True, nullable=False)
    name = Column("user_name", String(50), nullable=False)
    note = Column("user_note", String(50), nullable=True)


def _dsn(driver: str) -> str:
    user = quote_plus(os.environ["MYSQL_USERNAME"])
    password = quote_plus(os.environ["MYSQL_PASSWORD"])
    host = os.environ["MYSQL_HOST"]
    port = os.environ["MYSQL_PORT"]
    database = os.environ["MYSQL_DATABASE"]
    return f"{driver}://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


def _assert_server_reachable() -> None:
    engine = create_engine(_dsn("mysql+pymysql"))
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    finally:
        engine.dispose()


def test_mysql_crud_paths():
    _assert_server_reachable()

    async def main():
        engine = create_async_engine(_dsn("mysql+aiomysql"))
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with engine.begin() as connection:
                await connection.execute(text(f"DROP TABLE IF EXISTS {_TABLE}"))
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)

            async with session_factory() as session:
                created = await create(
                    session,
                    MysqlUser,
                    values={"user_email": "mysql-a@test.com", "name": "A", "note": "first"},
                )
                assert created.ok
                assert created.data is not None
                assert created.data["id"] > 0

                conflict = await create(
                    session,
                    MysqlUser,
                    values={"email": "mysql-a@test.com", "name": "duplicated"},
                    on_conflict={"email": "mysql-a@test.com"},
                )
                assert not conflict.ok
                assert conflict.data is not None
                assert conflict.data["name"] == "A"

                upserted = await upsert(
                    session,
                    MysqlUser,
                    values={"email": "mysql-a@test.com", "name": "B", "note": "second"},
                    keys=("email",),
                    updates=("name", "note"),
                    returning=True,
                )
                assert upserted.ok
                assert upserted.rowcount == 1
                assert upserted.data is not None
                assert upserted.data["name"] == "B"
                assert upserted.data["id"] == created.data["id"]

                no_return = await upsert(
                    session,
                    MysqlUser,
                    values={"email": "mysql-a@test.com", "name": "C"},
                    keys=("email",),
                    returning=False,
                )
                assert no_return.data is None

                bulk = await bulk_insert(
                    session,
                    MysqlUser,
                    values=[
                        {"email": "mysql-b@test.com", "name": "Bulk1"},
                        {"email": "mysql-c@test.com", "name": "Bulk2", "note": "note"},
                    ],
                    return_defaults=True,
                )
                assert bulk.ok
                assert bulk.rowcount == 2
                assert len(bulk.data) == 2
                assert all(item["id"] > 0 for item in bulk.data)

                assert await count(session, MysqlUser) == 3

                row = await fetch_one(session, MysqlUser, where={"email": "mysql-a@test.com"})
                assert row is not None
                assert row["name"] == "C"

                rows = await fetch_all(session, MysqlUser, order_by="-id", limit=2)
                assert len(rows) == 2
                assert rows[0]["id"] > rows[1]["id"]

                updated = await update(
                    session,
                    MysqlUser,
                    values={"note": None},
                    where={"email": "mysql-a@test.com"},
                    null_columns=["note"],
                    returning=True,
                )
                assert updated.ok
                assert updated.data is not None
                assert updated.data["note"] is None

                result = await raw(session, f"SELECT count(*) AS total FROM {_TABLE}")
                assert result.scalar_one() == 3

                deleted = await delete(session, MysqlUser, where={"email": "mysql-b@test.com"})
                assert deleted.ok
                assert deleted.rowcount == 1

                savepoint = await session.begin_nested()
                with pytest.raises(RuntimeError):
                    await upsert(
                        session,
                        MysqlUser,
                        values={
                            "id": created.data["id"],
                            "email": "mysql-other@test.com",
                            "name": "Other",
                        },
                        keys=("email",),
                        returning=True,
                    )
                await savepoint.rollback()

                result = await raw(session, "SELECT 10 AS value", commit=True)
                assert result.scalar_one() == 10
                assert await count(session, MysqlUser) == 2
        finally:
            async with engine.begin() as connection:
                await connection.execute(text(f"DROP TABLE IF EXISTS {_TABLE}"))
            await engine.dispose()

    asyncio.run(main())
