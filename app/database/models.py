from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, BigInteger, ForeignKey, Text
from pgvector.sqlalchemy import Vector

from app import settings


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
        Vector(settings.embed_dim) # 768 это размерность вектора
    )

    # Текстовое представление

    context: Mapped[str] = mapped_column(
        Text
    )

    # Связь назад к документу

    document: Mapped['Document'] = relationship(
        back_populates='chunks'
    )