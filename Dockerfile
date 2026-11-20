FROM python:3.14-slim AS base
LABEL authors="morzzenVector"

# Устанавливаем uv внутри контейнера
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml .python-version uv.lock ./

# Отключение беферизации логов, чтобы они приходили в консоль мгновенно
ENV PYTHONUNBUFFERED=1

# Блокировка создания кэш-файлов __pycache__ (байт-кода), чтобы не нагружать контейнер
ENV PYTHONDONTWRITEBYTECODE=1

# WORKDIR /morzzenVector

# Установка через apt-get (менеджер пакетов Debian) build-essential (компилятор C++)
# и libpq-dev (системная бибилиотека для работы с Postgres)
# "&& rm -rf .." это команда удаления временных файлов кэшей пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# --- ЭТАП 1: Образ только для миграций Alembic
FROM base AS migrations

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --python-preference system --no-dev --group migrations

COPY ./app/database/models.py ./app/database/
COPY ./app/config.py ./app/
COPY ./migrations/ ./migrations/
COPY alembic.ini ./

# Добавление всех актуальных миграций
CMD exec uv run alembic upgrade head

# --- ЭТАП 2: Образ основного приложения api
FROM base AS api

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --python-preference system --no-dev --group api

# Копирование проекта из текущей директории и удаление migrations
COPY . .
RUN rm -rf ./migrations/ alembic.ini

# Запус приложения в docker container через uvicorn
CMD exec uv run --no-sync uvicorn 'app.main:app' --host '0.0.0.0' --port ${APP_PORT}