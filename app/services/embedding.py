from langchain_ollama import OllamaEmbeddings

from app import settings

""" Создание клиента OllamaEmbeddings """
model = OllamaEmbeddings(model=settings.embedding_model, base_url=settings.ollama_host)


# Векторизация документа и создание списка словарей
# [{'embedding': [0.1, 0.2, ...], 'context': 'Текст чанка'}, {}, ...]
async def create_vector_document(chunked_text: list[str]) -> list[dict]:
    vectors = await model.aembed_documents(
        [f"{settings.embed_doc_prefix} {chunk}" for chunk in chunked_text]
    )

    return [
        {"embedding": vector, "context": chunk}
        for vector, chunk in zip(vectors, chunked_text, strict=False)
    ]


# Векторизация поискового запроса и создание списка векторов (float)
async def create_vector_query(query: str) -> list[float]:
    vectorized_query = await model.aembed_query(f"{settings.embed_query_prefix} {query}")
    return vectorized_query
