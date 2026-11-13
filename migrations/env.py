"""How Alembic connects and what it compares against.

The URL comes from the environment, never from ``alembic.ini``, so no
connection string is ever committed.

``target_metadata`` is the models package, which imports every table. A table
missing from that import would look to Alembic like a table to drop.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from murfulu.db.config import resolve_url
from murfulu.db.models import Base

config = context.config

if config.config_file_name is not None:
    # Keep the loggers that already exist. The default switches every one of
    # them off, so a migration run inside the test suite (tests/test_db_live.py,
    # which runs only with Postgres reachable) silenced murfulu's own warnings
    # for every test after it — found 2026-11-13 when test_karbon_1_2_0 saw an
    # empty log in the full run and a full one alone.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", resolve_url().replace("%", "%%"))


def run_migrations_offline() -> None:
    """Emit SQL without connecting, for review or for a DBA to run."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect and run the migrations."""
    section = config.get_section(config.config_ini_section, {})
    connectable = engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
