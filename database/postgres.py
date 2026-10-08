from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, Text, String, ForeignKey, text, select
from database.db_config import DATABASE_URL
from pgvector.sqlalchemy import Vector

# Создание асинхронного движка для базы данных

async_engine = create_async_engine(DATABASE_URL)

# Создание фабрики сессий AsyncSession

AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False # отключение автоматического истечения объектов
)

# Создание общего базового класса SQLAlchemy

class Base(DeclarativeBase):
    pass

# Создание класса загружаемого документа

class Document(Base):
    __tablename__ = 'documents'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    chunks: Mapped[list['Embedding']] = relationship(
        back_populates='document',
        cascade='all, delete-orphan',
        lazy='selectin'

    )

# Создание класса векторного отображения чанков документа

class Embedding(Base):
    __tablename__ = 'embeddings'

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    # Обязательно добавляем ForeignKey для связи с таблицей documents

    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('documents.id', ondelete='CASCADE')
    )

    # Векторное представление

    embedding: Mapped[list[float]] = mapped_column(
        Vector(768) # 768 это размерность вектора
    )

    # Текстовое представление

    context: Mapped[str] = mapped_column(
        Text
    )

    # Связь назад к документу

    document: Mapped['Document'] = relationship(
        back_populates='chunks'
    )

# Создание таблиц, наследуемых от Base

async def init_db():
    async with async_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        await conn.run_sync(Base.metadata.create_all)

# Создание сессии, загрузка вектора и текста в базу данных

async def vector_loading(filename: str, vector_list: list[dict]):
    async with AsyncSessionFactory.begin() as session:
        document_item = Document(
            title=filename
        )

        for item in vector_list:
            chunks_item=Embedding(
                embedding=item['embedding'],
                context=item['context'],
            )
            document_item.chunks.append(chunks_item)

        session.add(document_item)

# Создание сессии, поисковый запрос к базе данных, сравнение векторов

async def compare_vectors(vectorized_question: list[float]):
    async with AsyncSessionFactory.begin() as session:
        statement = (
            select(Embedding.context)
            .order_by(Embedding.embedding.cosine_distance(vectorized_question))
            .limit(1)
        )

        result = await session.scalars(statement)

        return result.all()