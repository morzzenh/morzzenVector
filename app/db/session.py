from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# БЫЛО (в database/postgres.py): from database.db_config import DATABASE_URL
# БЫЛО: from app.config import DATABASE_URL
# БЫЛО: from app.config import settings
# СОКРАЩЕНО: from app import settings (витрина пакета, см. app/__init__.py)
from app import settings
from app.db.models import Base

# СТРУКТУРА: подключение к БД (движок, сессии, инициализация) вынесено из postgres.py в отдельный
# модуль. Раньше в одном файле были и подключение, и модели таблиц, и запросы — это три разные
# причины для изменения. Теперь: session.py (подключение), models.py (таблицы), repository.py (запросы).

# Создание асинхронного движка для базы данных

async_engine = create_async_engine(settings.DATABASE_URL)

# Создание фабрики сессий AsyncSession

AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False # отключение автоматического истечения объектов
)

# Создание таблиц, наследуемых от Base

# ЗАМЕЧАНИЕ: create_all не умеет изменять уже существующие таблицы. Для смены размерности вектора
# или добавления колонок нужны миграции (Alembic). Пока что — пересоздавать вручную вручную.
async def init_db():
    async with async_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        await conn.run_sync(Base.metadata.create_all)
