from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app import settings
from app.database.models import Document, Embedding
from app.database.session import AsyncSessionFactory

# Создание сессии, загрузка вектора и текста в базу данных


async def vector_loading(
    filename: str, document_hash: str, vector_list_document: list[dict]
) -> bool:
    try:
        async with AsyncSessionFactory.begin() as session:
            # Создание документа в бд, запись его кэша и используемой модели эмбеддинга
            document_item = Document(
                title=filename,
                document_hash=document_hash,
                embedding_model=settings.embedding_model,
            )

            # Запись чанков документа с собственными индексами, вектором и контекстом
            for index, item in enumerate(vector_list_document):
                chunks_item = Embedding(
                    chunk_index=index,
                    embedding=item["embedding"],
                    context=item["context"],
                )
                document_item.chunks.append(chunks_item)
            session.add(document_item)

    # отлавливание ошибки IntegrityError, чтобы при одновременной загрузке одинакового документа
    # еще до проверки кэша, не возникала ошибка, когда бд не может сделать запись,
    # т.к. document_hash должен быть уникальным (unique=True)
    except IntegrityError:
        return False

    return True


# Создание сессии, поисковый запрос к базе данных, сравнение векторов
async def compare_vectors(string_query: str, vectorized_query: list[float], top_k: int):
    async with AsyncSessionFactory.begin() as session:
        # Реализация гибридного поиска в 4 этапа:
        # - полнотекстовый поиск postgres,
        # - векторный поиск по hnsw индексу,
        # - объединение и сортировка
        # - удаление дублей

        # 1. Полнотекстовый поиск postgres
        search_query = func.websearch_to_tsquery("russian", string_query)

        # Вычисление ранга (релевантности)
        rank_col = func.ts_rank_cd(Embedding.search_vector, search_query)

        statement_words = (
            select(
                Document.title,
                Embedding.document_id,
                Embedding.chunk_index,
                Embedding.context,
                rank_col
            )
            .join(Document, Document.id == Embedding.document_id)
            # Условие соответствия запросу (оператор @@)
            .where(Embedding.search_vector.bool_op("@@")(search_query))
            # Сортировка по убыванию ранга (чем больше, тем релевантнее)
            .order_by(rank_col.desc())
            .limit(top_k)
        )

        # 2. Векторный поиск косинусного расстояния между векторами / запись значения в distance
        distance = Embedding.embedding.cosine_distance(vectorized_query).label("distance")

        statement_vectors = (
            select(
                Document.title,
                Embedding.document_id,
                Embedding.chunk_index,
                Embedding.context,
                distance,
            )
            .join(Document, Document.id == Embedding.document_id)
            .where(distance <= settings.search_max_distance)
            .order_by(distance)
            .limit(top_k * 3)
        )

        rows_vectors = (await session.execute(statement_vectors)).all() # получение данных из бд
        rows_words = (await session.execute(statement_words)).all()

        # 3. Объединение и сортировка
        fused_candidates = {}  # хранилище кандидатов

        for rank, row in enumerate(rows_vectors, start=1):
            key = (row.document_id, row.chunk_index)
            if key not in fused_candidates:
                fused_candidates[key] = {
                    "document_id": row.document_id,
                    "title": row.title,
                    "chunk_index": row.chunk_index,
                    "context": row.context,
                    "distance": round(row.distance, 4), # сохраняем расстояние (для вектора)
                    "rrf_score": 0.0, # счетчик очков
                }
            # Даем очки: чем меньше rank (чем выше место), тем больше очков
            # Формула: 1 / (K + rank)
            fused_candidates[key]["rrf_score"] += 1.0 / (settings.k + rank)

        for rank, row in enumerate(rows_words, start=1):
            key = (row.document_id, row.chunk_index)
            if key not in fused_candidates:
                fused_candidates[key] = {
                    "document_id": row.document_id,
                    "title": row.title,
                    "chunk_index": row.chunk_index,
                    "context": row.context,
                    "distance": None, # значение None, т.к. чанка найден только текстом
                    "rrf_score": 0.0,
                }
            fused_candidates[key]["rrf_score"] += 1.0 / (settings.k + rank)

        # Сортировка по очкам от большего к меньшему
        sorted_candidates = sorted(
            fused_candidates.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        # 4. Алгоритм пропуска соседних чанков, если они в выдаче идут последовательно
        # это позволяет убрать в выдаче одинаковую информацию из-за перекрытия чанков
        results: list[dict] = []
        for candidate in sorted_candidates:
            is_neighbor = any(
                r["document_id"] == candidate["document_id"]
                and abs(r["chunk_index"] - candidate["chunk_index"]) == 1
                for r in results
            )
            if is_neighbor:
                continue

            results.append(
                {
                    "document_id": candidate["document_id"],
                    "title": candidate["title"],
                    "chunk_index": candidate["chunk_index"],
                    "distance": candidate["distance"],
                    "context": candidate["context"],
                }
            )

            if len(results) == top_k:
                break # останавливаемся, если набрали достаточно результатов

    return results


# Проверка уникальности загружаемого файла
async def check_unique(document_hash: str) -> bool:
    async with AsyncSessionFactory.begin() as session:
        # Проверка уникальности кэша файла, сравнение с кэшом из бд
        # Если такой файл есть, возвращается False
        if await session.scalar(select(Document.id).where(Document.document_hash == document_hash)):
            return False

    return True
