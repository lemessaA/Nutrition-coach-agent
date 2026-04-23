"""SQLAlchemy engine, session, and table creation for the FastAPI app."""

from __future__ import annotations

import asyncio
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


def _engine_url() -> str:
    return settings.database_url


_connect_args: dict = {}
if _engine_url().startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(
    _engine_url(),
    connect_args=_connect_args,
    pool_pre_ping=not _engine_url().startswith("sqlite"),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _import_models() -> None:
    import database.models  # noqa: F401  — register ORM mappers on Base.metadata


def _create_all_tables() -> None:
    _import_models()
    Base.metadata.create_all(bind=engine)


async def init_db() -> None:
    await asyncio.to_thread(_create_all_tables)
