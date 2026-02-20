from logging.config import fileConfig
import asyncio

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import get_settings
from app.models.base import Base

# Alembic Config
config = context.config
fileConfig(config.config_file_name)

# Metadata
target_metadata = Base.metadata

# Load settings
settings = get_settings()

# Fix Docker vs Localhost issue
host = settings.POSTGRES_HOST
port = settings.POSTGRES_PORT

if host == "db":
    host = "localhost"

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:"
    f"{settings.POSTGRES_PASSWORD}@{host}:"
    f"{port}/{settings.POSTGRES_DB}"
)

config.set_main_option("sqlalchemy.url", DATABASE_URL)


# -------------------------
# Offline Migrations
# -------------------------

def run_migrations_offline():

    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# -------------------------
# Online Migrations
# -------------------------

def do_run_migrations(connection: Connection):

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


# -------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()