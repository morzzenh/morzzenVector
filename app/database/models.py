from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app import settings


# Создание общего базового класса SQLAlchemy
class Base(DeclarativeBase):
    pass


# Создание класса загружаемого документа
class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    document_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)

    chunks: Mapped[list[Embedding]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


# Создание класса векторного отображения чанков документа
class Embedding(Base):
    __tablename__ = "embeddings"

    # HNSW-индекс по косинусному расстоянию. Без индекса Postgres сравнивает
    # со всеми векторами (точно, но медленно на больших объемах). Класс операторов
    # vector_cosine_ops должен совпадать с метрикой в запросе (cosine_distance)
    __table_args__ = (
        Index(
            "hnsw_index",
            "embedding",
            postgresql_using=settings.index_type,
            postgresql_with={
                "m": settings.max_connections,
                "ef_construction": settings.exploration_depth,
            },
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Обязательно добавляем ForeignKey для связи с таблицей documents
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,  # чанк без документа - битые данные
        index=True,  # индекс, чтобы при удалении/поиске чанков не было полного перебора таблицы
    )

    # Порядковые номер чанка в документе - нужен, чтобы при поиске убирать
    # соседние чанки (при пересечении chunk_overlap)
    chunk_index: Mapped[int] = mapped_column(nullable=False)

    # Векторное представление
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.embed_dim)  # 768 это размерность вектора
    )

    # Текстовое представление
    context: Mapped[str] = mapped_column(Text)

    # Связь назад к документу
    document: Mapped[Document] = relationship(back_populates="chunks")
