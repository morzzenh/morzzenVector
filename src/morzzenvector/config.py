from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, model_validator
from sqlalchemy import URL
from functools import lru_cache
from typing import Annotated

''' Класс настроек базы данных '''

class DbSettings(BaseSettings):

    database_user: str = Field(
        default='postgres',
        description='Имя пользователя базы данных. По умолчанию: postgres'
    )

    database_host: str = Field(
        default='localhost',
        description='IP адрес хоста базы данных. По умолчанию: localhost'
    )

    database_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description='Порт для подключения к бд. По умолчанию: 5432'
    )

    database_name: str = Field(
        default='postgres',
        description='Название базы данных. По умолчанию: postgres'
    )

    driver_name: str = Field(
        default='postgresql+asyncpg',
        description='Движок базы данных. Требуется асинхронный. По умолчанию: postgresql+asyncpg'
    )

    database_password: SecretStr = Field(
        default=..., # обязательное поле
        description='Пароль для подключения к бд.'
    )

''' Класс настроек модели эмбеддинга '''

class Embeddings(BaseSettings):

    embedding_model: str = Field(
        default=..., # обязательное поле
        description='Название модели эмбеддинга. От неё зависит качество всего поиска.'
    )

    embed_dim: int = Field(
        default=768,
        gt=0,
        description='Размерность вектора. Должна соответствовать используемой модели. По умолчанию: 768'
    )

    embed_doc_prefix: str = Field(
        default='', # дефолт пустая строка
        description='Префикс документа требуемый для модели nomic-embed-text. Пример: "search_document:"'
    )

    embed_query_prefix: str = Field(
        default='', # дефолт пустая строка
        description='Префикс поискового запроса требуемый для модели nomic-embed-text. Пример: "search_query:"'
    )

''' Класс настроек чанкирования текста '''

class Chunking(BaseSettings):

    chunk_size: int = Field(
        default=1000,
        gt=0,
        description='Максимальный размер одного чанка в символах. По умолчанию: 1000'
    )

    chunk_overlap: int = Field(
        default=200,
        ge=0,
        description='Перекрытие соседних чанков в символах (должно быть меньше chunk_size). По умолчанию: 200'
    )

    path_temp_file: str = Field(
        default=..., # обязательное поле
        description='Директория для создания и хранения temp загружаемого файла.'
    )

''' Базовый класс настроек Pydantic для валидации .env'''

class Settings(DbSettings, Chunking, Embeddings):

    # имена полей = имена переменных окружения .env (регистр не важен)

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    max_file_size_mb: int = Field(
        default=20,
        gt=0,
        description='Максимальный размер загружаемого файла в мегабайтах. По умолчанию: 20'
    )

    @property
    def database_url(self) -> URL:

        # Сборка URL для подключения к базе данных

        return URL.create(
            drivername=self.driver_name,
            username=self.database_user,
            password=self.database_password.get_secret_value(),
            host=self.database_host,
            port=self.database_port,
            database=self.database_name
        )

    @property
    def max_file_size(self) -> int:

        # Лимит размера файла в байтах

        return self.max_file_size_mb * 1024 * 1024

    @model_validator(mode='after')
    def _check_chunk_overlap(self):

        # Проверка согласованности нескольких полей: перекрытие чанков не может быть больше самого чанка

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError('chunk_overlap должен быть меньше chunk_size')
        return self

@lru_cache
def get_settings() -> Settings:

    # Вызов и кэширование настроек при первом обращении к get_settings()

    return Settings()

SettingsDep = Annotated[Settings, Depends(get_settings)] # создание единого Annotated для импорта настроек