from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # session factory

Base = declarative_base()  # base class for all models


def _run_lightweight_migrations() -> None:
    """Apply small, idempotent column additions for existing tables.

    ``Base.metadata.create_all`` happily creates brand new tables but will
    NEVER alter a table that already exists. When we add a new column to an
    existing table (e.g. ``users.role`` for the marketplace feature) we need a
    tiny ad-hoc migration so the server starts cleanly on databases that were
    created before that column existed. Each step is gated on an information-
    schema check so re-running on an already-migrated DB is a no-op.
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    users_columns = {c["name"] for c in inspector.get_columns("users")}
    statements: list[str] = []

    if "role" not in users_columns:
        statements.append(
            "ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'buyer'"
        )

    if not statements:
        return

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


async def init_db():
    """Initialize database tables (creates new tables and runs column adds)."""
    Base.metadata.create_all(bind=engine)
    _run_lightweight_migrations()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
