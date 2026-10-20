from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import settings
from app.database.models import Embedding, Document

from app.database.session import AsyncSessionFactory

# Создание сессии, загрузка вектора и текста в базу данных

async def vector_loading(filename: str, document_hash: str, vector_list_document: list[dict]) -> bool:

    try:
        async with AsyncSessionFactory.begin() as session:

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

        # Поиск косинусного расстояния между векторами / запись значения в distance

        distance = Embedding.embedding.cosine_distance(vectorized_query).label('distance')

        statement = (
            select(
                Document.title,
                Embedding.document_id,
                Embedding.chunk_index,
                Embedding.context,
                distance
            )
            .join(Document, Document.id == Embedding.document_id)
            .where(distance <= settings.search_max_distance)
            .order_by(distance)
            .limit(settings.top_k * 3)
        )

        rows = (await session.execute(statement)).all()

        # Алгоритм пропуска соседних чанков, если они в выдаче идут последовательно
        # это позволяет убрать в выдаче одинаковую информацию из-за перекрытия чанков

        results: list[dict] = []
        for row in rows:
            is_neighbor = any(
                r['document_id'] == row.document_id and abs(r['chunk_index'] - row.chunk_index) == 1
                for r in results
            )
            if is_neighbor:
                continue

            results.append({
                'document_id': row.document_id,
                'title': row.title,
                'chunk_index': row.chunk_index,
                'distance': round(row.distance, 4),
                'context': row.context
            })

            if len(results) == settings.top_k:
                break

    return results

# Проверка уникальности загружаемого файла

async def check_unique(document_hash: str) -> bool:

    async with AsyncSessionFactory.begin() as session:

        # Проверка уникальности кэша файла, сравнение с кэшом из бд
        # Если такой файл есть, возвращается False

        if await session.scalar(
            select(Document.id).where(Document.document_hash == document_hash)
        ):
            return False

    return True