from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

# ИСПРАВЛЕНО: везде одинаковые абсолютные импорты от корня проекта (app.*) и без `import *`.
# Раньше здесь было `from app_config import *`, а в services — `from app.app_config`:
# это работало только из-за настроек PyCharm, а один и тот же модуль загружался под двумя именами.
# Запуск из КОРНЯ проекта: `uvicorn app.main:app --reload`.
# БЫЛО: from database.postgres import vector_loading, compare_vectors
# БЫЛО: from app_config import *
# БЫЛО: from services.text_splitter import chunking_file
# БЫЛО: from services.embedding import create_vector, vector_search
# БЫЛО: from starlette.concurrency import run_in_threadpool
# БЫЛО: from database.postgres import init_db
# (эндпоинты и их импорты переехали в app/api/routes.py)
# БЫЛО: from app.api.routes import router
# БЫЛО: from app.db.session import init_db
# СОКРАЩЕНО: импорт через «витрину» пакетов (см. app/api/__init__.py и app/db/__init__.py)
from app.api import router
from app.db import init_db


# УЛУЧШЕНИЕ: @app.on_event('startup') объявлен устаревшим (deprecated) — вместо него lifespan.
# Создание необходимых таблиц в БД при первом запуске
# БЫЛО: @app.on_event('startup')
# БЫЛО: async def on_startup():
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print('База данных и таблицы успешно инициализированы!')
    yield

# БЫЛО: app = FastAPI()
app = FastAPI(lifespan=lifespan)
app.include_router(router)


# Запуск сервера uvicorn на localhost:8000
# Запускать из корня проекта: python -m app.main

if __name__ == '__main__':
    # БЫЛО: uvicorn.run('main:app', host='localhost', port=8000, reload=True)
    uvicorn.run('app.main:app', host='localhost', port=8000, reload=True)
