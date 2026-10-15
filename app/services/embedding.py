from langchain_ollama import OllamaEmbeddings

from app import settings

''' Создание клиента OllamaEmbeddings '''

model = OllamaEmbeddings(model=settings.embedding_model)

# Векторизация документа и создание списка словарей [{'embedding': [0.1, 0.2, ...], 'context': 'Текст чанка'}, {}, ...]

async def create_vector_document(chunked_text: list[str]) -> list[dict]:

    vector_list_document: list[dict] = []

    for chunk in chunked_text:

        vector = await model.aembed_query(f'{settings.embed_doc_prefix} {chunk}')

        vector_list_document.append({
            'embedding': vector,
            'context': chunk
        })

    return vector_list_document

# Векторизация поискового запроса и создание списка векторов (float)

async def create_vector_query(query: str) -> list[float]:

    vectorized_query = await model.aembed_query(f'{settings.embed_query_prefix} {query}')

    return vectorized_query


