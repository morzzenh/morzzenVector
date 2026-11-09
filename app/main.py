from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api import router
from app.config import settings
from app.database import init_db


# Создание необходимых таблиц в БД при первом запуске
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("База данных и таблицы успешно инициализированы!")

    yield  # приложение запущено и принимает HTTP запросы


app = FastAPI(lifespan=lifespan)

app.include_router(router)

# Запуск сервера uvicorn на localhost:8000
if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=settings.app_port, reload=True)
