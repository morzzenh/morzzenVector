from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from app import settings
from app.database.models import Base

# Создание асинхронного движка базы данных

async_engine = create_async_engine(settings.database_url)

# Создание асинхронной фабрики сессий

AsyncSessionFactory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False # отключение автоматического истечения объектов,
    # защита от ошибки MissingGreenlet при обращении к объекту сессии после commit сессии и ее закрытии
    )

# Создание таблиц в базе данных, наследуемых от Base (при запуске приложения)

async def init_db():

    async with async_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        await conn.run_sync(Base.metadata.create_all)

# Удаление таблиц, наследуемых от Base (при остановке приложения, для тестов)

async def close_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)