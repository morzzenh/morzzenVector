import hashlib

from fastapi import APIRouter, UploadFile, HTTPException
from starlette.concurrency import run_in_threadpool

from app.api.schemas import SearchRequest
# БЫЛО: from app.config import MAX_FILE_SIZE
# БЫЛО: from app.config import settings
from app import settings
from app.constants import VALID_TYPES_FILES
# БЫЛО: from app.db.repository import vector_loading, compare_vectors
# БЫЛО: from app.services.chunking import chunking_file
# БЫЛО: from app.services.embedding import create_vector, vector_search
# СОКРАЩЕНО: через __init__.py пакетов. А schemas выше импортируем напрямую: это тот же пакет app.api
from app.db import vector_loading, compare_vectors
from app.services import chunking_file, create_vector, vector_search

# СТРУКТУРА: эндпоинты вынесены из main.py в APIRouter. main.py теперь только собирает приложение.
# Слои: api (HTTP) -> services (чанкирование, эмбеддинги) -> db (модели, запросы).
# БЫЛО (в main.py): app = FastAPI()  и декораторы @app.post(...)
router = APIRouter()


# Загрузка текстового файла и валидация формата
# БЫЛО: @app.post('/uploadfile')
@router.post('/uploadfile')
async def upload_file(file: UploadFile):
    # ИСПРАВЛЕНО: раньше при ошибке возвращался HTTP 200 с текстом ошибки в теле — клиент не может
    # отличить успех от провала по коду ответа. Ошибки должны быть HTTPException с кодом 4xx.
    # БЫЛО: return {'Ошибка': 'Разрешена загрузка только текстовых файлов'}   # HTTP 200!
    if file.content_type not in VALID_TYPES_FILES:
        raise HTTPException(status_code=415, detail='Неподдерживаемый формат файла')

    # УЛУЧШЕНИЕ: ограничение размера — иначе можно загрузить файл на гигабайты и положить сервер.
    # БЫЛО: if file.size is not None and file.size > MAX_FILE_SIZE:
    if file.size is not None and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail='Файл слишком большой')

    # УЛУЧШЕНИЕ: хэш содержимого для защиты от повторной загрузки одного и того же файла.
    content_hash = hashlib.sha256(await file.read()).hexdigest()
    await file.seek(0)

    # Обработка текстового файла для LLM
    # ИСПРАВЛЕНО: передаём имя файла — по расширению MarkItDown выбирает конвертер. До этого было им файла без расширения,
    # библиотека ошибалась - файл превращался в мусор - отсюда мусорные чанки и нерелевантный поиск
    # БЫЛО: chunked_text = await run_in_threadpool(chunking_file,file.file) # чанкирование всего текста асинхронно
    chunked_text = await run_in_threadpool(chunking_file, file.file, file.filename) # чанкирование в потоке

    # УЛУЧШЕНИЕ: пустой результат (скан без текста, пустой файл) раньше падал бы дальше или
    # записывал документ без чанков.
    if not chunked_text:
        raise HTTPException(status_code=422, detail='Не удалось извлечь текст из файла')

    vector_list = await create_vector(chunked_text) # векторизация всех чанков

    # Загрузка вектора в базу данных

    # БЫЛО: await vector_loading(file.filename, vector_list)
    loaded = await vector_loading(file.filename, content_hash, vector_list)
    if not loaded:
        raise HTTPException(status_code=409, detail='Такой файл уже загружен')

    # БЫЛО: return {'Статус': 'Файл успешно загружен в базу'}
    return {'status': 'Файл успешно загружен в базу', 'chunks': len(chunked_text)}

# Поисковый запрос к Базе Данных
# БЫЛО: @app.post('/search')
# БЫЛО: async def search(question: str):
@router.post('/search')
async def search(request: SearchRequest):

    # Векторизация поискового запроса

    # БЫЛО: vectorized_question = await vector_search(question)
    vectorized_question = await vector_search(request.question)

    # Сравнение векторов базы данных и поискового запроса

    # БЫЛО: result = await compare_vectors(vectorized_question)
    result = await compare_vectors(vectorized_question, request.top_k)

    # БЫЛО: return {'Статус': 'Поиск по базе данных выполнен успешно!', 'Результаты': result}
    return {'status': 'Поиск по базе данных выполнен успешно!', 'results': result}
