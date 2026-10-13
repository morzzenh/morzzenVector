import uvicorn
from fastapi import FastAPI, UploadFile
from morzzenvector.database import init_db, vector_loading, compare_vectors, AsyncSessionFactoryDep, create_engine
from morzzenvector.services import EmbeddingDep, create_vector_document, create_vector_query, chunking_document
from morzzenvector import SettingsDep, get_settings
from app_config import *
from starlette.concurrency import run_in_threadpool
app = FastAPI()

# Разрешенные MIME-форматы загружаемых документов (из mime_tupes.py)

VALID_TYPES_FILES = [DOC, DOCX, DOCM, DOT, DOTX, PDF, TXT, MD, CSV, HTML, JSON, XML]

# Создание необходимых таблиц в БД при первом запуске

@app.on_event('startup')
async def on_startup():

    settings = get_settings()

    engine = create_engine(settings)

    await init_db(engine)
    print('База данных и таблицы успешно инициализированы!')

# Загрузка текстового файла и валидация формата
@app.post('/uploadfile')
async def upload_file(
        file: UploadFile,
        settings: SettingsDep,
        client: EmbeddingDep,
        async_session_factory: AsyncSessionFactoryDep
):

    if file.content_type not in VALID_TYPES_FILES:
        return {'Ошибка': 'Разрешена загрузка только текстовых файлов'}

    # Обработка текстового файла для LLM

    chunked_text = await run_in_threadpool(chunking_document,file.file, settings) # чанкирование всего текста асинхронно

    vector_list_document = await create_vector_document(chunked_text, client, settings) # векторизация всех чанков

    # Загрузка вектора в базу данных

    await vector_loading(file.filename, vector_list_document, async_session_factory)

    # Тестовый вызов из БД

    return {'Статус': 'Файл успешно загружен в базу'}

# Поисковый запрос к Базе Данных

@app.post('/search')
async def search(
        query: str,
        settings: SettingsDep,
        client: EmbeddingDep,
        async_session_factory: AsyncSessionFactoryDep
):

    # Векторизация поискового запроса

    vectorized_question = await create_vector_query(query, client, settings)

    # Сравнение векторов базы данных и поискового запроса

    result = await compare_vectors(vectorized_question, async_session_factory)

    return {'Статус': 'Поиск по базе данных выполнен успешно!', 'Результаты': result}

# Запуск сервера uvicorn на localhost:8000

if __name__ == '__main__':
    uvicorn.run('main:app', host='localhost', port=8000, reload=True)