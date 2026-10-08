from langchain_ollama import OllamaEmbeddings

# БЫЛО: from app.app_config import LLM_MODEL
# БЫЛО: (промежуточная версия) from app.config import LLM_MODEL, DOC_PREFIX, QUERY_PREFIX
# БЫЛО: from app.config import settings
# СОКРАЩЕНО: from app import settings (витрина пакета, см. app/__init__.py)
from app import settings

# ВАЖНО — ВЫБОР МОДЕЛИ ЭМБЕДДИНГОВ: самая частая причина «поиск выдаёт не то, что ищешь».
# Модель превращает текст в вектор, и «похожесть» на выходе ровно настолько хороша, насколько
# модель понимает язык документов. Что может пойти не так:
#   1) ЯЗЫК. nomic-embed-text обучена в основном на английском. На русских документах она
#      плохо различает смысл: запрос и нужный чанк получают «далёкие» векторы, а случайный
#      чанк с похожими словами оказывается ближе. Для русского нужна мультиязычная модель:
#      bge-m3 (1024 измерения, префиксы не нужны), multilingual-e5, qwen3-embedding.
#   2) ПРЕФИКСЫ. У nomic/e5/embeddinggemma документ и запрос кодируются с разными префиксами
#      (см. EMBED_DOC_PREFIX / EMBED_QUERY_PREFIX в config.py). Забыли префикс — качество падает.
#   3) РАЗМЕРНОСТЬ. EMBED_DIM должен совпадать с моделью (nomic = 768, bge-m3 = 1024).
#   4) СМЕНА МОДЕЛИ. Векторы разных моделей несравнимы: после смены надо пересоздать таблицы
#      и заново загрузить все документы (старые векторы остаются «из другого мира»).
# Как проверить модель, а не гадать: набор из 20–30 пар «вопрос → ожидаемый документ» и
# подсчёт, как часто нужный чанк попадает в топ-5. Сравните 2–3 модели на этом наборе.
# БЫЛО: llm = OllamaEmbeddings(model=LLM_MODEL)
llm = OllamaEmbeddings(model=settings.LLM_MODEL)

# Векторизация и создание списка словарей [{'embedding': [0.1, 0.2, ...], 'context': 'Текст чанка'}, {}, ...]

async def create_vector(chunked_text: list[str]) -> list[dict]:

    # УЛУЧШЕНИЕ: раньше aembed_query вызывался в цикле — по одному HTTP-запросу к Ollama на чанк.
    # aembed_documents отправляет все чанки одним батчем: значительно быстрее.
    # ИСПРАВЛЕНО: aembed_query предназначен для поисковых запросов, а не для документов.
    # ИСПРАВЛЕНО: добавлен префикс документа (см. комментарий в app_config.py) —
    # без него качество поиска у nomic-embed-text заметно падает.
    # Префикс используется только для вектора; в базе хранится чистый текст чанка.
    # БЫЛО:
    # БЫЛО: vector_list: list[dict] = []
    # БЫЛО: for chunk in chunked_text:
    # БЫЛО:     vector = await llm.aembed_query(chunk)
    # БЫЛО:     vector_list.append({
    # БЫЛО:         'embedding': vector,
    # БЫЛО:         'context': chunk
    # БЫЛО:     })
    # БЫЛО: return vector_list
    vectors = await llm.aembed_documents([settings.EMBED_DOC_PREFIX + chunk for chunk in chunked_text])

    return [
        {'embedding': vector, 'context': chunk}
        for vector, chunk in zip(vectors, chunked_text)
    ]

# Векторизация поискового запроса

async def vector_search(question: str) -> list[float]:

    # ИСПРАВЛЕНО: запрос получает префикс запроса (отличается от префикса документа!).
    # БЫЛО: vectorized_question = await llm.aembed_query(question)
    # БЫЛО: return vectorized_question
    return await llm.aembed_query(settings.EMBED_QUERY_PREFIX + question)
