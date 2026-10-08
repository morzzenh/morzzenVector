# План доработок morzzenVector

Что делать дальше, по приоритету. Отмечайте `[x]` по мере выполнения.
Код ниже — ориентиры, а не готовые файлы: версии и параметры нужно проверить под ваш проект.

---

## 1. Запуск в Docker (Dockerfile + docker-compose)

Цель: `docker compose up` поднимает всё — приложение, Postgres с pgvector и Ollama — на любой машине одной командой.

- [ ] `Dockerfile` для приложения
- [ ] `docker-compose.yml` с тремя сервисами: `app`, `db`, `ollama`
- [ ] `.dockerignore`
- [ ] Добавить настройку `OLLAMA_BASE_URL` в `app/config.py` (см. ниже — **без этого в Docker не заработает**)
- [ ] Инструкция запуска в README

### Dockerfile
- Базовый образ `python:3.12-slim` (markitdown требует Python 3.10+).
- Многоэтапная сборка (multi-stage): на первом этапе ставятся зависимости, во второй образ копируется только результат — образ меньше и безопаснее.
- Запуск от **непривилегированного** пользователя (не root).
- Не копировать `.env` в образ: секреты передаются через `env_file` / переменные окружения при запуске.
- Команда запуска: `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Именно `0.0.0.0`: `localhost` внутри контейнера снаружи недоступен.

### docker-compose.yml
- **db**: образ `pgvector/pgvector:pg17` (Postgres уже с расширением vector), том (volume) для данных, `healthcheck` через `pg_isready`.
- **ollama**: образ `ollama/ollama`, том для моделей (иначе они скачиваются заново при каждом пересоздании). Модель нужно один раз скачать: `docker compose exec ollama ollama pull bge-m3`.
- **app**: `depends_on` с `condition: service_healthy` для db, `env_file: .env`.
- В `.env` для Docker: `DATABASE_HOST=db` (имя сервиса, а не `localhost`), `OLLAMA_BASE_URL=http://ollama:11434`.

### Что поправить в коде
`OllamaEmbeddings(model=...)` сейчас не получает адрес сервера и ходит на `localhost:11434`. В контейнере Ollama живёт по адресу `http://ollama:11434`. Нужно:
1. Поле `OLLAMA_BASE_URL` в `Settings` (default `http://localhost:11434`).
2. `OllamaEmbeddings(model=settings.LLM_MODEL, base_url=settings.OLLAMA_BASE_URL)` в `app/services/embedding.py`.

---

## 2. Poetry вместо requirements.txt

Цель: воспроизводимые зависимости (lock-файл), разделение прод- и dev-зависимостей, единая точка настройки инструментов.

- [ ] `poetry init` → `pyproject.toml` (имя, версия, `python = "^3.12"`)
- [ ] Перенести зависимости из `requirements.txt`: `poetry add fastapi uvicorn ...`
- [ ] Dev-группа: `poetry add --group dev ruff pytest pytest-asyncio httpx mypy pre-commit`
- [ ] Закоммитить `poetry.lock` (это и даёт воспроизводимость)
- [ ] Удалить `requirements.txt`
- [ ] Использовать Poetry в Dockerfile: `poetry install --only main --no-root`
- [ ] Обновить README (`poetry install`, `poetry run uvicorn ...`)

Заметки:
- `pyproject.toml` — также место для настроек ruff, mypy, pytest (отдельные конфиги не нужны).
- Версию Poetry в Docker и CI лучше зафиксировать, иначе `poetry.lock` может «гулять».

---

## 3. Линтер и форматтер: ruff

Цель: единый стиль и поиск типичных ошибок автоматически, без споров о форматировании.

- [ ] Добавить `ruff` в dev-зависимости
- [ ] Секция `[tool.ruff]` в `pyproject.toml`
- [ ] Включить правила: `E`, `F` (базовые ошибки), `I` (порядок импортов), `UP` (современный синтаксис), `B` (частые баги), `ASYNC` (ошибки в async-коде), `S` (безопасность)
- [ ] `line-length = 100`, `target-version = "py312"`
- [ ] Команды: `ruff check --fix .` и `ruff format .`
- [ ] Прогнать по всему проекту и исправить замечания

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "ASYNC", "S"]
```

Ruff заменяет сразу flake8, isort и black.

---

## 4. Что ещё улучшить в коде

### Качество поиска 
- [ ] **Набор для оценки (eval):** 20–30 пар «вопрос → ожидаемый документ» и скрипт, который считает, в скольких случаях нужный чанк попал в топ-5. Без него любые изменения оцениваются на глаз. Начните с этого.
- [ ] Сменить модель на мультиязычную (`bge-m3`) для русских документов и сравнить на eval-наборе.
- [ ] Гибридный поиск (вектор + полнотекстовый Postgres, объединение через RRF) — место описано в `app/db/repository.py`.
- [ ] Реранкер (`bge-reranker-v2-m3`) на топ-30 кандидатов.
- [ ] Чанкирование по заголовкам markdown (`MarkdownHeaderTextSplitter`), заголовок раздела добавлять в текст чанка.

### Тесты
- [ ] `pytest` + `pytest-asyncio`; тест-клиент FastAPI на `httpx`.

### База данных
- [ ] **Alembic** для миграций вместо `Base.metadata.create_all` в `init_db`. `create_all` не умеет изменять существующие таблицы, а смена размерности вектора или добавление колонки без миграций ломает данные. В идеале собирать отдельнвй образ db-migrator, чтобы добавлялись туда только файлы миграции. (подсмотреть можно в проекте, который я скинул)
- [ ] Эндпоинты `GET /documents` (список с пагинацией) и `DELETE /documents/{id}` — сейчас удалить документ можно только руками в БД.

### Надёжность и эксплуатация
- [ ] Заменить `print` на `logging` (структурные логи, уровни, id запроса) (взять стандартную библиотеку либо взять целый модуль из того проекта, что я скинул).
- [ ] Эндпоинт `GET /health` (проверка БД и Ollama) — нужен и для Docker healthcheck.
- [ ] Обработка недоступного Ollama: понятный ответ 503 вместо 500 с трейсбеком.
- [ ] Ограничить число одновременных запросов к Ollama (`asyncio.Semaphore`) и разбивать очень большие файлы на батчи при векторизации.
- [ ] Загрузка тяжёлых файлов: рассмотреть фоновую обработку (очередь задач), а не ожидание в запросе.

### Безопасность
- [ ] Аутентификация (хотя бы API-ключ в заголовке) и ограничение частоты запросов — сейчас эндпоинты открыты всем - изучить security fastapi раздел.


### Качество кода
- [ ] Типизация и `mypy` (хотя бы `--strict` для `app/`).
- [ ] `pre-commit`: ruff, ruff-format, mypy перед каждым коммитом.
- [ ] `Makefile` или `justfile` с короткими командами: `make lint`, `make test`, `make up`.
- [ ] Переименовать `LLM_MODEL` в `EMBEDDING_MODEL` (это embedding-модель, не LLM; название путает). Потребует правки `.env` у всех.
- [ ] Docstring'и у публичных функций, README с примерами `curl` для `/uploadfile` и `/search`.

---

## Порядок работ

1. Poetry (основа для остального).
2. Ruff + pre-commit.
3. Dockerfile и docker-compose (с `OLLAMA_BASE_URL`).
4. Тесты и CI.
5. Eval-набор, затем гибридный поиск и реранкер.
6. Alembic, логирование, health, безопасность.
