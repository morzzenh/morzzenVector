from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, Text, String, ForeignKey, Index
from pgvector.sqlalchemy import Vector

# БЫЛО (в database/postgres.py): from database.db_config import DATABASE_URL  — модели тянули конфиг подключения
# БЫЛО: from app.config import EMBED_DIM
# БЫЛО: from app.config import settings
# СОКРАЩЕНО: from app import settings (витрина пакета, см. app/__init__.py)
from app import settings

# СТРУКТУРА: здесь только описание таблиц. Никакой логики подключения и запросов.

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

    # УЛУЧШЕНИЕ: SHA-256 содержимого файла. Раньше повторная загрузка того же файла создавала дубль,
    # и в выдаче поиска один и тот же текст появлялся несколько раз. unique=True защищает на уровне БД.
    content_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False
    )

    # УЛУЧШЕНИЕ: запоминаем, какой моделью получены векторы. Векторы разных моделей несравнимы;
    # при смене модели с той же размерностью всё молча «ломалось» бы без единой ошибки.
    embedding_model: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # БЫЛО:
    # БЫЛО: chunks: Mapped[list['Embedding']] = relationship(
    # БЫЛО:     back_populates='document',
    # БЫЛО:     cascade='all, delete-orphan',
    # БЫЛО:     lazy='selectin'
    # БЫЛО: )
    # УЛУЧШЕНИЕ: убран lazy='selectin' — он при каждой выборке документа подгружал ВСЕ его чанки
    # с векторами, хотя они почти никогда не нужны вместе.
    chunks: Mapped[list['Embedding']] = relationship(
        back_populates='document',
        cascade='all, delete-orphan'
    )

# Создание класса векторного отображения чанков документа

class Embedding(Base):
    __tablename__ = 'embeddings'

    # УЛУЧШЕНИЕ: HNSW-индекс по косинусному расстоянию. Без индекса Postgres сравнивает запрос
    # со ВСЕМИ векторами (точно, но медленно на больших объёмах). Класс операторов
    # vector_cosine_ops должен совпадать с метрикой в запросе (cosine_distance).
    __table_args__ = (
        Index(
            'ix_embeddings_embedding_hnsw',
            'embedding',
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'embedding': 'vector_cosine_ops'},
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    # Обязательно добавляем ForeignKey для связи с таблицей documents
    # ИСПРАВЛЕНО: nullable=False (чанк без документа — битые данные) и index=True
    # (иначе удаление/поиск чанков документа — полный перебор таблицы).

    # БЫЛО: document_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('documents.id', ondelete='CASCADE'))
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # УЛУЧШЕНИЕ: порядковый номер чанка в документе — нужен, чтобы при поиске убирать
    # соседние чанки (они пересекаются из-за chunk_overlap и выглядят как дубли).
    chunk_index: Mapped[int] = mapped_column(
        nullable=False
    )

    # Векторное представление
    # ИСПРАВЛЕНО: размерность берётся из конфига, а не хардкодится числом 768.

    # БЫЛО: Vector(768) # 768 это размерность вектора
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.EMBED_DIM)
    )

    # Текстовое представление

    context: Mapped[str] = mapped_column(
        Text
    )

    # Связь назад к документу
    document: Mapped['Document'] = relationship(
        back_populates='chunks'
    )
