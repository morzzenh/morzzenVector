from functools import lru_cache
from typing import Annotated
from fastapi import Depends

from langchain_ollama import OllamaEmbeddings

from morzzenvector import SettingsDep

''' Создание клиента OllamaEmbeddings с кэшированием. С одинаковыми аргументами settings
 возвращается кэшированное значение клиента. При изменении аргумента, клиент пересоздается
 и кэшируется уже другое значение '''

@lru_cache
def _get_cached_embed_client(model_name:str):
    return OllamaEmbeddings(model=model_name)

def get_embed_client(settings: SettingsDep):
    return _get_cached_embed_client(settings.embedding_model)

EmbeddingDep = Annotated[OllamaEmbeddings, Depends(get_embed_client)] # создание единой Annotated для клиента модели

# Векторизация документа и создание списка словарей [{'embedding': [0.1, 0.2, ...], 'context': 'Текст чанка'}, {}, ...]

async def create_vector_document(chunked_text: list[str], client: OllamaEmbeddings, settings: SettingsDep) -> list[dict]:

    vector_list_document: list[dict] = []

    for chunk in chunked_text:

        vector = await client.aembed_query(f'{settings.embed_doc_prefix} {chunk}')

        vector_list_document.append({
            'embedding': vector,
            'context': chunk
        })

    return vector_list_document

# Векторизация поискового запроса и создание списка векторов (float)

async def create_vector_query(query: str, client: OllamaEmbeddings, settings: SettingsDep) -> list[float]:

    vectorized_query = await client.aembed_query(f'{settings.embed_query_prefix} {query}')

    return vectorized_query


