from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import settings
from app.database.models import Embedding, Document

from app.database.session import AsyncSessionFactory

# Создание сессии, загрузка вектора и текста в базу данных

async def vector_loading(filename: str, document_hash: str, vector_list_document: list[dict]) -> bool:

    try:
        async with AsyncSessionFactory.begin() as session:

            # Проверка уникальности кэша файла, сравнение с кэшом из бд
            # Если такой файл есть, возвращается False

            if await session.scalar(
                select(Document.id).where(Document.document_hash == document_hash)
            ):
                return False

            # Создание документа в бд, запись его кэша и используемой модели эмбеддинга

            document_item = Document(
                title=filename,
                document_hash=document_hash,
                embedding_model=settings.embedding_model
            )

            # Запись чанков документа с собственными индексами, вектором и контекстом

            for index, item in enumerate(vector_list_document):
                chunks_item = Embedding(
                    chunk_index=index,
                    embedding=item['embedding'],
                    context=item['context'],
                )
                document_item.chunks.append(chunks_item)

            session.add(document_item)

    # отлавливание ошибки IntegrityError, чтобы при одновременной загрузке одинакового документа
    # еще до проверки кэша, не возникала ошибка, когда бд не может сделать запись, т.к. document_hash
    # должен быть уникальным (unique=True)

    except IntegrityError:
        return False

    return True

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