from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select

from app import settings
from app.database.models import Base, Embedding, Document

# Создание асинхронного движка базы данных

async_engine = create_async_engine(settings.database_url)

# Создание фабрики сессий

AsyncSessionFactory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False # отключение автоматического истечения объектов
    )

# Создание таблиц, наследуемых от Base (при запуске приложения)

async def init_db():
    async with async_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        await conn.run_sync(Base.metadata.create_all)

# Удаление таблиц, наследуемых от Base (при остановке приложения, для тестов)

async def close_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Создание сессии, загрузка вектора и текста в базу данных

async def vector_loading(filename: str, vector_list_document: list[dict]):
    async with AsyncSessionFactory.begin() as session:
        document_item = Document(
            title=filename
        )

        for item in vector_list_document:
            chunks_item = Embedding(
                embedding=item['embedding'],
                context=item['context'],
            )
            document_item.chunks.append(chunks_item)

        session.add(document_item)

# Создание сессии, поисковый запрос к базе данных, сравнение векторов

async def compare_vectors(vectorized_query: list[float]):
    async with AsyncSessionFactory.begin() as session:
        statement = (
            select(Embedding.context)
            .order_by(Embedding.embedding.cosine_distance(vectorized_query))
            .limit(1)
        )

        result = await session.scalars(statement)

        return result.all()