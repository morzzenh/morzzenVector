FROM python:3.14-slim
LABEL authors="morzzenVector"

# Устанавливаем uv внутри контейнера
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Отключение беферизации логов, чтобы они приходили в консоль мгновенно
ENV PYTHONUNBUFFERED=1

# Блокировка создания кэш-файлов __pycache__ (байт-кода), чтобы не нагружать контейнер
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /morzzenVector

# Установка через apt-get (менеджер пакетов Debian) build-essential (компилятор C++)
# и libpq-dev (системная бибилиотека для работы с Postgres)
# "&& rm -rf .." это команда удаления временных файлов кэшей пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка python библиотек через uv в workdir
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --python-preference system --no-dev

# Копирование проекта из текущей директории на ПК в текущую директорию контейнера
COPY . .

# Запус приложения в docker container через uvicorn
CMD exec uv run uvicorn 'app.main:app' --host '0.0.0.0' --port ${APP_PORT}