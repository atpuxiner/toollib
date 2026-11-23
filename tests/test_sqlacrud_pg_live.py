import asyncio
import os
from urllib.parse import quote_plus

import pytest
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from toollib.sqlacrud import bulk_insert, count, create, delete, fetch_all, fetch_one, raw, update, upsert

_REQUIRED_ENV = ("DB_HOST", "DB_PORT", "DB_DATABASE", "DB_USERNAME", "DB_PASSWORD")
if not all(os.getenv(name) for name in _REQUIRED_ENV):
    pytest.skip("PostgreSQL environment variables are not set", allow_module_level=True)

_TABLE = "toollib_sqlacrud_pg_live"
Base = declarative_base()


class PgUser(Base):
    __tablename__ = _TABLE

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(120), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    note = Column(String(50), nullable=True)


def _dsn(driver: str) -> str:
    user = quote_plus(os.environ["DB_USERNAME"])
    password = quote_plus(os.environ["DB_PASSWORD"])
    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    database = os.environ["DB_DATABASE"]
    return f"{driver}://{user}:{password}@{host}:{port}/{database}"


def _assert_server_reachable() -> None:
    engine = create_engine(_dsn("postgresql+psycopg2"))
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    finally:
        engine.dispose()


def test_postgres_crud_paths():
    _assert_server_reachable()

    async def main():
        engine = create_async_engine(_dsn("postgresql+asyncpg"))
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with engine.begin() as connection:
                await connection.execute(text(f"DROP TABLE IF EXISTS {_TABLE}"))
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)

            async with session_factory() as session:
                created = await create(
                    session,
                    PgUser,
                    values={"email": "pg-a@test.com", "name": "A", "note": "first"},
                )
                assert created.ok
                assert created.data is not None
                assert created.data["id"] > 0

                conflict = await create(
                    session,
                    PgUser,
                    values={"email": "pg-a@test.com", "name": "duplicated"},
                    on_conflict={"email": "pg-a@test.com"},
                )
                assert not conflict.ok
                assert conflict.data is not None
                assert conflict.data["name"] == "A"

                upserted = await upsert(
                    session,
                    PgUser,
                    values={"email": "pg-a@test.com", "name": "B", "note": "second"},
                    keys=("email",),
                    updates=("name", "note"),
                    returning=True,
                )
                assert upserted.ok
                assert upserted.data is not None
                assert upserted.data["name"] == "B"
                assert upserted.data["id"] == created.data["id"]

                bulk = await bulk_insert(
                    session,
                    PgUser,
                    values=[
                        {"email": "pg-b@test.com", "name": "Bulk1"},
                        {"email": "pg-c@test.com", "name": "Bulk2", "note": "note"},
                    ],
                    return_defaults=True,
                )
                assert bulk.ok
                assert bulk.rowcount == 2
                assert len(bulk.data) == 2
                assert all(item["id"] > 0 for item in bulk.data)

                assert await count(session, PgUser) == 3

                row = await fetch_one(session, PgUser, where={"email": "pg-a@test.com"})
                assert row is not None
                assert row["name"] == "B"

                rows = await fetch_all(session, PgUser, order_by="-id", limit=2)
                assert len(rows) == 2
                assert rows[0]["id"] > rows[1]["id"]

                updated = await update(
                    session,
                    PgUser,
                    values={"note": None},
                    where={"email": "pg-a@test.com"},
                    null_columns=["note"],
                    returning=True,
                )
                assert updated.ok
                assert updated.data is not None
                assert updated.data["note"] is None

                result = await raw(session, f"SELECT count(*) AS total FROM {_TABLE}")
                assert result.scalar_one() == 3
                result.close()

                deleted = await delete(session, PgUser, where={"email": "pg-b@test.com"})
                assert deleted.ok
                assert deleted.rowcount == 1

                result = await raw(session, "SELECT 9 AS value", commit=True)
                assert result.scalar_one() == 9
                assert await count(session, PgUser) == 2
        finally:
            async with engine.begin() as connection:
                await connection.execute(text(f"DROP TABLE IF EXISTS {_TABLE}"))
            await engine.dispose()

    asyncio.run(main())
