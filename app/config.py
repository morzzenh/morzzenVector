# БЫЛО: import os
# БЫЛО: from dotenv import load_dotenv
# БЫЛО: from sqlalchemy import URL
# БЫЛО: load_dotenv()
# УЛУЧШЕНИЕ: конфигурация на pydantic-settings. Вместо россыпи os.getenv() — один класс Settings:
#   * типы приводятся сами (порт -> int, порог -> float), а не вручную int(os.getenv(...));
#   * обязательные поля без значения по умолчанию: если в .env забыли DATABASE_HOST,
#     приложение упадёт СРАЗУ при старте с понятным сообщением, а не где-то внутри SQLAlchemy;
#   * границы значений (ge/le) проверяются при старте;
#   * пароль хранится как SecretStr — не попадает в логи и print(settings);
#   * .env читается самим pydantic-settings, load_dotenv() больше не нужен;
#   * у каждого поля есть description — настройки самодокументируются.
import pydantic as p
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):


    # Имена полей = именам переменных окружения (регистр не важен), существующий .env работает как раньше.
    # extra='ignore' — лишние переменные (например, старый PATH_TEMP_FILE) не вызывают ошибку.
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # ---------- База данных ----------
    # БЫЛО (в database/db_config.py, отдельный файл со своим load_dotenv()):
    # БЫЛО: drivername=os.getenv('DRIVER_NAME'),
    DRIVER_NAME: str = p.Field(
        default='postgresql+asyncpg',
        description='Драйвер подключения к БД. Должен быть асинхронным. '
        'Значение по умолчанию: postgresql+asyncpg',
    )
    # БЫЛО: username=os.getenv('DATABASE_USER'),
    DATABASE_USER: str = p.Field(
        default=...,  # ... (Ellipsis) = значения по умолчанию нет, поле ОБЯЗАТЕЛЬНОЕ
        description='Пользователь БД. Обязательное поле',
    )
    # БЫЛО: password=os.getenv('DATABASE_PASSWORD'),
    DATABASE_PASSWORD: p.SecretStr = p.Field(
        default=...,  # ... (Ellipsis) = значения по умолчанию нет, поле ОБЯЗАТЕЛЬНОЕ
        description='Пароль пользователя БД. Хранится как SecretStr и не попадает в логи. Обязательное поле',
    )
    # БЫЛО: host=os.getenv('DATABASE_HOST'),
    DATABASE_HOST: str = p.Field(
        default='localhost',
        description='Хост БД. Значение по умолчанию: localhost',
    )
    # БЫЛО: port=os.getenv('DATABASE_PORT'),
    DATABASE_PORT: int = p.Field(
        default=5432,
        ge=1,
        le=65535,
        description='Порт БД. Значение по умолчанию: 5432',
    )
    # БЫЛО: database=os.getenv('DATABASE_NAME')
    DATABASE_NAME: str = p.Field(
        default=...,  # ... (Ellipsis) = значения по умолчанию нет, поле ОБЯЗАТЕЛЬНОЕ
        description='Имя базы данных. Обязательное поле',
    )

    # ---------- Модель эмбеддингов ----------
    # ЗАМЕЧАНИЕ: переменная называется LLM_MODEL, но это не LLM, а embedding-модель. Название путает.
    # Оставлено прежнее имя переменной окружения, чтобы не ломать существующий .env.
    # ВАЖНО: от этой модели зависит качество всего поиска (подробности — в services/embedding.py).
    # БЫЛО: LLM_MODEL = os.getenv('LLM_MODEL')   # при отсутствии было None и падало позже, непонятно где
    LLM_MODEL: str = p.Field(
        default=...,  # ... (Ellipsis) = значения по умолчанию нет, поле ОБЯЗАТЕЛЬНОЕ
        description='Модель эмбеддингов в Ollama. От неё зависит качество всего поиска. '
        'Для русскоязычных документов nomic-embed-text плохая — используйте bge-m3. '
        'Обязательное поле',
    )
    # ИСПРАВЛЕНО (главная причина плохого поиска): размерность вектора раньше была захардкожена (768)
    # в моделях БД и никак не связана с выбранной моделью.
    # БЫЛО (в database/postgres.py): Vector(768) # 768 это размерность вектора
    # БЫЛО: EMBED_DIM = int(os.getenv('EMBED_DIM', '768'))
    EMBED_DIM: int = p.Field(
        default=768,
        gt=0,
        description='Размерность вектора. Должна совпадать с моделью: nomic-embed-text = 768, bge-m3 = 1024. '
        'Значение по умолчанию: 768',
    )
    # ИСПРАВЛЕНО (главная причина плохого поиска): многие embedding-модели обучены с префиксами.
    # Без них документ и запрос лежат в разных «областях» пространства, и схожесть считается плохо.
    # БЫЛО: префиксов не было вообще — текст чанка и запрос уходили в модель как есть.
    # БЫЛО: DOC_PREFIX = os.getenv('EMBED_DOC_PREFIX', 'search_document: ')
    EMBED_DOC_PREFIX: str = p.Field(
        default='search_document: ',
        description='Префикс, добавляемый к тексту чанка перед векторизацией. '
        'Нужен nomic-embed-text, для bge-m3 задайте пустое значение. '
        'В .env значение с пробелом на конце берите в кавычки, иначе пробел потеряется. '
        'Значение по умолчанию: "search_document: "',
    )
    # БЫЛО: QUERY_PREFIX = os.getenv('EMBED_QUERY_PREFIX', 'search_query: ')
    EMBED_QUERY_PREFIX: str = p.Field(
        default='search_query: ',
        description='Префикс, добавляемый к поисковому запросу перед векторизацией '
        '(отличается от префикса документа!). Для bge-m3 задайте пустое значение. '
        'Значение по умолчанию: "search_query: "',
    )

    # ---------- Чанкирование ----------
    # УЛУЧШЕНИЕ: «магические числа» (размер чанка, топ-N, лимит файла) вынесены в конфиг,
    # чтобы их можно было подбирать без правки кода.
    # БЫЛО (в text_splitter.py): chunk_size=1000, chunk_overlap=200  — числа внутри кода
    # БЫЛО: CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
    CHUNK_SIZE: int = p.Field(
        default=1000,
        gt=0,
        description='Максимальный размер одного чанка в символах. Значение по умолчанию: 1000',
    )
    # БЫЛО: CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))
    CHUNK_OVERLAP: int = p.Field(
        default=200,
        ge=0,
        description='Перекрытие соседних чанков в символах (должно быть меньше CHUNK_SIZE). '
        'Значение по умолчанию: 200',
    )

    # ---------- Поиск ----------
    # top_k — сколько самых релевантных фрагментов вернуть. Мало (1–3): коротко и точно, но нужный
    # фрагмент можно упустить. Много (10–20): выше шанс его захватить, но больше «шума» и токенов,
    # если результаты потом идут в LLM. Обычно 3–10. Название из ML: «top-k results».
    # БЫЛО: SEARCH_TOP_K = int(os.getenv('SEARCH_TOP_K', '5'))
    SEARCH_TOP_K: int = p.Field(
        default=5,
        ge=1,
        le=20,
        description='Сколько самых релевантных чанков вернуть в ответе поиска (top-k). '
        'Значение по умолчанию: 5',
    )
    # Раньше возвращались всегда 3 «ближайших» чанка, даже если в базе нет ничего похожего.
    # БЫЛО: порога не было, запрос всегда делал .limit(3).
    # БЫЛО: SEARCH_MAX_DISTANCE = float(os.getenv('SEARCH_MAX_DISTANCE', '0.6'))
    SEARCH_MAX_DISTANCE: float = p.Field(
        default=0.6,
        ge=0,
        le=2,
        description='Порог косинусного расстояния: 0 — идентично, 1 — не связано, 2 — противоположно. '
        'Результаты дальше порога считаются нерелевантными. Зависит от модели — подберите по '
        'реальным запросам. Значение по умолчанию: 0.6',
    )

    # ---------- Загрузка файлов ----------
    # УЛУЧШЕНИЕ: PATH_TEMP_FILE удалён. Один общий временный файл для всех запросов — это гонка данных:
    # два одновременных /uploadfile затирали друг друга. Теперь временный файл создаётся через
    # tempfile на каждый запрос (см. services/chunking.py).
    # БЫЛО: PATH_TEMP_FILE = os.getenv('PATH_TEMP_FILE')   # Путь сохранения временного загрузочного файла
    # БЫЛО: MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE_MB', '20')) * 1024 * 1024
    MAX_FILE_SIZE_MB: int = p.Field(
        default=20,
        gt=0,
        description='Максимальный размер загружаемого файла в мегабайтах. Значение по умолчанию: 20',
    )

    # УЛУЧШЕНИЕ: проверка согласованности нескольких полей сразу — раньше такой ошибки никто не ловил:
    # перекрытие чанков не может быть больше самого чанка, иначе сплиттер падает уже при загрузке файла.
    @p.model_validator(mode='after')
    def _check_chunk_overlap(self):
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError('CHUNK_OVERLAP должен быть меньше CHUNK_SIZE')
        return self

    @property
    def MAX_FILE_SIZE(self) -> int:
        """Лимит размера файла в байтах."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def DATABASE_URL(self) -> URL:
        # Сборка URL для подключения к базе данных
        # БЫЛО: DATABASE_URL = URL.create(drivername=..., username=..., password=..., host=..., port=..., database=...)
        # get_secret_value() — единственное место, где пароль «раскрывается».
        return URL.create(
            drivername=self.DRIVER_NAME,
            username=self.DATABASE_USER,
            password=self.DATABASE_PASSWORD.get_secret_value(),
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            database=self.DATABASE_NAME,
        )


# Единый объект настроек: `from app.config import settings` и дальше settings.CHUNK_SIZE.
settings = Settings()
