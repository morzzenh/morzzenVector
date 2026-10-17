from fastapi import UploadFile, APIRouter

from app.database import vector_loading, compare_vectors
from app.services import create_vector_document, create_vector_query, chunking_document
from app.constans import VALID_TYPES_FILES

from starlette.concurrency import run_in_threadpool

router = APIRouter()

# Загрузка текстового файла и валидация формата
@router.post('/uploadfile')
async def upload_file(file: UploadFile):

    if file.content_type not in VALID_TYPES_FILES:
        return {'Ошибка': 'Разрешена загрузка только текстовых файлов'}

    # Обработка текстового файла для LLM

    chunked_text = await run_in_threadpool(chunking_document,file.file, file.filename) # чанкирование всего текста асинхронно

    vector_list_document = await create_vector_document(chunked_text) # векторизация всех чанков

    # Загрузка вектора в базу данных

    await vector_loading(file.filename, vector_list_document)

    # Тестовый вызов из БД

    return {'Статус': 'Файл успешно загружен в базу'}

# Поисковый запрос к Базе Данных

@router.post('/search')
async def search(query: str):

    # Векторизация поискового запроса

    vectorized_question = await create_vector_query(query)

    # Сравнение векторов базы данных и поискового запроса

    result = await compare_vectors(vectorized_question)

    return {'Статус': 'Поиск по базе данных выполнен успешно!', 'Результаты': result}
