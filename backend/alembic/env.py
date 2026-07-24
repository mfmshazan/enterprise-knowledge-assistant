"""Alembic migration environment (async-aware).

Key points:

* We import the application's `Base.metadata` (with every model registered via
  `app.models`) as `target_metadata` — this is what `--autogenerate` diffs the
  database against to produce migrations.
* The database URL comes from application settings, not `alembic.ini`, so there
  is a single source of truth. The async URL (`postgresql+asyncpg://...`) is run
  through an async engine and Alembic's `run_sync` bridge.
* `render_as_batch=True` enables "batch mode", which lets migrations work on
  SQLite too (SQLite can't ALTER most columns in place).
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

# Registers all models on Base.metadata (imported for the side effect).
import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the runtime DB URL so migrations and the app never drift apart.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection ('offline' mode)."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # detect column type changes
        compare_server_default=True,
        render_as_batch=True,  # SQLite compatibility
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations against a live database using an async engine."""
    connectable = async_engine_from_config(
        {"sqlalchemy.url": settings.DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
