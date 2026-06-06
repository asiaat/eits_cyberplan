import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

"""Alembic migration env.

This is a minimal env for a migrations-only setup.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, text as sa_text
from sqlalchemy import pool

from alembic import context

config = context.config

from app.db.base import Base
from app.models import *  # noqa
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    import os
    if "DATABASE_URL" in os.environ:
        config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Ensure alembic_version table has a wide enough column for long revision IDs
        connection.execute(
            sa_text(
                "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(128) PRIMARY KEY)"
            )
        )
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()