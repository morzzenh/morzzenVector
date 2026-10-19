from fastapi import UploadFile, APIRouter,HTTPException

from app.database import vector_loading, compare_vectors
from app.services import create_vector_document, create_vector_query, chunking_document
from app.constans import VALID_TYPES_FILES
from app import settings

from starlette.concurrency import run_in_threadpool

router = APIRouter()

# Загрузка текстового файла и валидация формата
@router.post('/uploadfile')
async def upload_file(file: UploadFile):

    if file.content_type not in VALID_TYPES_FILES:
        raise HTTPException(
            status_code=415,
            detail=f'Неподдерживаемый тип файла. Допустимые форматы: {VALID_TYPES_FILES}'
        )
    if file.size > settings.max_file_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f'Загружаемый файл большого размера. Допустимый размер: {settings.max_file_size_mb} мб'
        )

    # Обработка текстового файла для модели эмбеддинга

    chunked_text = await run_in_threadpool(chunking_document,file.file, file.filename) # чанкирование всего текста асинхронно

    vector_list_document = await create_vector_document(chunked_text) # векторизация всех чанков

    # Загрузка вектора в базу данных

    await vector_loading(file.filename, vector_list_document)

    return {'status': 'Файл успешно загружен в базу'}

# Поисковый запрос к Базе Данных

@router.post('/search')
async def search(query: str):

    # Векторизация поискового запроса

    vectorized_question = await create_vector_query(query)

    # Сравнение векторов базы данных и поискового запроса

    result = await compare_vectors(vectorized_question)

    return {'status': 'Поиск по базе данных выполнен успешно!', 'results': result}
