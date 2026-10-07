import uvicorn
from fastapi import FastAPI, UploadFile
from database.postgres import vector_loading, compare_vectors
from app_config import *
from services.text_splitter import chunking_file
from services.embedding import create_vector, vector_search
from starlette.concurrency import run_in_threadpool
from database.postgres import init_db
app = FastAPI()

# Разрешенные MIME-форматы загружаемых документов (из mime_tupes.py)

VALID_TYPES_FILES = [DOC, DOCX, DOCM, DOT, DOTX, PDF, TXT, MD, CSV, HTML, JSON, XML]

# Создание необходимых таблиц в БД при первом запуске

@app.on_event('startup')
async def on_startup():
    await init_db()
    print('База данных и таблицы успешно инициализированы!')

# Загрузка текстового файла и валидация формата
@app.post('/uploadfile')
async def upload_file(file: UploadFile):
    if file.content_type not in VALID_TYPES_FILES:
        return {'Ошибка': 'Разрешена загрузка только текстовых файлов'}

    # Обработка текстового файла для LLM

    chunked_text = await run_in_threadpool(chunking_file,file.file) # чанкирование всего текста асинхронно

    vector_list = await create_vector(chunked_text) # векторизация всех чанков

    # Загрузка вектора в базу данных

    await vector_loading(file.filename, vector_list)

    # Тестовый вызов из БД

    return {'Статус': 'Файл успешно загружен в базу'}

# Поисковый запрос к Базе Данных

@app.post('/search')
async def search(question: str):

    # Векторизация поискового запроса

    vectorized_question = await vector_search(question)

    # Сравнение векторов базы данных и поискового запроса

    result = await compare_vectors(vectorized_question)

    return {'Статус': 'Поиск по базе данных выполнен успешно!', 'Результаты': result}

# Запуск сервера uvicorn на localhost:8000

if __name__ == '__main__':
    uvicorn.run('main:app', host='localhost', port=8000, reload=True)