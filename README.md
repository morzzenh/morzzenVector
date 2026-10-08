# morzzenVector

Семантический поиск по документам: загрузка файла → чанки → эмбеддинги (Ollama) → pgvector → поиск по смыслу.

## Запуск
1. PostgreSQL с расширением `pgvector`, запущенный Ollama (`ollama pull bge-m3`).
2. `cp .env.example .env` и заполнить.
3. `pip install -r requirements.txt`
4. Из корня проекта: `uvicorn app.main:app --reload`

## API
- `POST /uploadfile` — multipart-файл.
- `POST /search` — `{"question": "...", "top_k": 5}`; в ответе чанки с названием документа и косинусной дистанцией (меньше — ближе).

Смена embedding-модели требует пересоздать таблицы и заново загрузить документы.

## Структура проекта
```
app/
  main.py          # сборка приложения: FastAPI, lifespan, подключение роутера
  config.py        # вся конфигурация из .env (модель, чанки, порог поиска, URL БД)
  constants.py     # MIME-типы разрешённых файлов
  api/
    routes.py      # HTTP-эндпоинты /uploadfile и /search
    schemas.py     # схемы запросов
  services/
    chunking.py    # файл -> markdown -> чанки
    embedding.py   # чанки/запрос -> векторы (Ollama)
  db/
    session.py     # движок, сессии, init_db
    models.py      # таблицы Document и Embedding
    repository.py  # запись и поиск (сюда добавлять гибридный поиск и реранкер)
```
Зависимости направлены в одну сторону: `api -> services / db -> config`.
