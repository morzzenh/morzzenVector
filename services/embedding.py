from langchain_ollama import OllamaEmbeddings
from app.app_config import LLM_MODEL

llm = OllamaEmbeddings(model=LLM_MODEL)

# Векторизация и создание списка словарей [{'embedding': [0.1, 0.2, ...], 'context': 'Текст чанка'}, {}, ...]

async def create_vector(chunked_text: list[str]) -> list[dict]:

    vector_list: list[dict] = []

    for chunk in chunked_text:

        vector = await llm.aembed_query(f'search_document: {chunk}')

        vector_list.append({
            'embedding': vector,
            'context': chunk
        })

    return vector_list

# Векторизация поискового запроса

async def vector_search(question: str) -> list[float]:

    vectorized_question = await llm.aembed_query(f'search_query: {question}')

    return vectorized_question


