import asyncio

from logging.config import fileConfig

from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from alembic import context

from app.database.models import Base
from app.config import settings

config = context.config

# Форматирование URL строки под синтаксис Alembic для корректного парсинга из env
stringified_sqlalchemy_url = settings.database_url.render_as_string(
    hide_password=False
)

# Экранирование символа %
percent_replaced_url = stringified_sqlalchemy_url.replace("%", "%%")

# Подменяем sqlalchemy.url значением форматированного URL - percent_replaced_url
config.set_main_option("sqlalchemy.url", percent_replaced_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Указываем какую metadata использовать
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """ Запуск миграций в offline-режиме """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """ Запуск миграций асинхронно в online-режиме """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online():
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
