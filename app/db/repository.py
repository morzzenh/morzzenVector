from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

# БЫЛО: from database.db_config import DATABASE_URL  (и модели, и движок лежали в этом же файле)
# БЫЛО: from app.config import LLM_MODEL, SEARCH_MAX_DISTANCE
# БЫЛО: from app.config import settings
# СОКРАЩЕНО: from app import settings (витрина пакета, см. app/__init__.py)
from app import settings
from app.db.models import Document, Embedding
from app.db.session import AsyncSessionFactory

# СТРУКТУРА: все запросы к БД (запись и поиск) собраны в одном месте. Эндпоинты и сервисы
# не должны знать про SQL — они вызывают функции отсюда (паттерн «репозиторий»).

# Создание сессии, загрузка вектора и текста в базу данных
# Возвращает True, если документ загружен, и False, если такой файл уже есть в базе.

# БЫЛО: async def vector_loading(filename: str, vector_list: list[dict]):
async def vector_loading(filename: str, content_hash: str, vector_list: list[dict]) -> bool:
    try:
        async with AsyncSessionFactory.begin() as session:
            # УЛУЧШЕНИЕ: проверка дубликата ДО вставки (быстрый путь); unique на content_hash
            # дополнительно защищает от гонки двух одновременных загрузок.
            exists = await session.scalar(
                select(Document.id).where(Document.content_hash == content_hash)
            )
            if exists:
                return False

            # БЫЛО: document_item = Document(title=filename)
            document_item = Document(
                title=filename,
                content_hash=content_hash,
                embedding_model=settings.LLM_MODEL,
            )

            for index, item in enumerate(vector_list):
                # БЫЛО: chunks_item=Embedding(embedding=item['embedding'], context=item['context'])
                # (индекс чанка chunk_index не сохранялся)
                chunks_item = Embedding(
                    chunk_index=index,
                    embedding=item['embedding'],
                    context=item['context'],
                )
                document_item.chunks.append(chunks_item)

            session.add(document_item)
    except IntegrityError:
        return False

    return True

# Создание сессии, поисковый запрос к базе данных, сравнение векторов

# КУДА ВСТАВИТЬ ГИБРИДНЫЙ ПОИСК И РЕРАНКЕР (следующий шаг по улучшению качества):
#
# Сейчас функция делает один шаг: векторный поиск -> фильтр дублей -> топ-k.
# Целевой конвейер из трёх шагов, и вся логика живёт ЗДЕСЬ (сигнатура и формат ответа
# не меняются, main.py трогать не нужно):
#
#   1) ГИБРИДНЫЙ ПОИСК (в начале функции, вместо одного запроса `statement` ниже).
#      Делаем ДВА запроса и объединяем результаты:
#        а) векторный — как сейчас (хорошо ловит смысл, плохо — точные слова, имена, артикулы);
#        б) полнотекстовый Postgres (хорошо ловит точные термины, плохо — перефразирование).
#      Списки склеиваем методом RRF (Reciprocal Rank Fusion): score = Σ 1 / (60 + rank_в_списке).
#      Это не требует сравнивать несопоставимые шкалы (косинус и ts_rank).
#      Берём с запасом, например по 30 кандидатов из каждого поиска.
#
#   2) РЕРАНКЕР (после гибридного поиска, ПЕРЕД блоком отсева соседей ниже).
#      Берём ~30 кандидатов, прогоняем пары (вопрос, текст чанка) через кросс-энкодер
#      (например bge-reranker-v2-m3 — мультиязычный) и сортируем по его оценке.
#      Кросс-энкодер читает вопрос и чанк ВМЕСТЕ, поэтому намного точнее векторной близости,
#      но медленный — поэтому применяется только к малому числу кандидатов.
#      Для этого функции понадобится сам текст вопроса, а не только его вектор:
#      добавьте параметр `question: str`. Сам вызов реранкера вынесите в services/reranker.py.
#
#   3) ОТСЕВ СОСЕДЕЙ и срез до top_k — оставить как есть (блок ниже).
#
# Порог SEARCH_MAX_DISTANCE после реранкера уже не подходит (это порог по косинусу):
# фильтровать надо по оценке реранкера.
# top_k — сколько лучших результатов вернуть (подробное описание в app/config.py).
# Из БД берём top_k * 3 кандидатов с запасом: часть отсеется как соседние дубли,
# и только затем итог обрезается ровно до top_k.

# БЫЛО: async def compare_vectors(vectorized_question: list[float]):
async def compare_vectors(vectorized_question: list[float], top_k: int) -> list[dict]:
    async with AsyncSessionFactory.begin() as session:
        # ИСПРАВЛЕНО: было max_inner_product (скалярное произведение, оператор <#>). Оно корректно
        # только для нормализованных векторов и отдаёт предпочтение «длинным» векторам.
        # Для текстового поиска стандарт — косинусное расстояние (<=>).
        # БЫЛО: .order_by(Embedding.embedding.max_inner_product(vectorized_question))
        distance = Embedding.embedding.cosine_distance(vectorized_question).label('distance')

        # БЫЛО: statement = (select(Embedding.context)   # только текст, без документа и дистанции
        statement = (
            select(
                Document.title,
                Embedding.document_id,
                Embedding.chunk_index,
                Embedding.context,
                distance,
            )
            .join(Document, Document.id == Embedding.document_id)
            # ИСПРАВЛЕНО: порог релевантности. Раньше всегда возвращались 3 «ближайших» чанка,
            # даже если в базе нет ничего похожего.
            .where(Embedding.embedding.cosine_distance(vectorized_question) <= settings.SEARCH_MAX_DISTANCE)
            .order_by(distance)
            # Берём с запасом: часть кандидатов отсеется как соседние дубли (см. ниже).
            # БЫЛО: .limit(3)
            .limit(top_k * 3)
        )

        # БЫЛО: result = await session.scalars(statement)
        # БЫЛО: return result.all()   # список строк-текстов без дедупликации
        rows = (await session.execute(statement)).all()

    # ИСПРАВЛЕНО: чанки пересекаются (chunk_overlap), поэтому топ-3 раньше часто состоял из
    # трёх почти одинаковых кусков одного абзаца. Пропускаем чанк, если сосед (±1) того же
    # документа уже выбран.
    results: list[dict] = []
    for row in rows:
        is_neighbor = any(
            r['document_id'] == row.document_id and abs(r['chunk_index'] - row.chunk_index) == 1
            for r in results
        )
        if is_neighbor:
            continue

        # УЛУЧШЕНИЕ: отдаём не только текст, но и документ-источник и дистанцию —
        # без этого невозможно понять, почему найдено именно это, и отладить качество.
        results.append({
            'document_id': row.document_id,
            'title': row.title,
            'chunk_index': row.chunk_index,
            'distance': round(row.distance, 4),
            'context': row.context,
        })
        if len(results) == top_k:
            break

    return results
