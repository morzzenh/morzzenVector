from sqlalchemy import select

from app.database.models import Embedding, Document

from app.database.session import AsyncSessionFactory

# Создание сессии, загрузка вектора и текста в базу данных

async def vector_loading(filename: str, vector_list_document: list[dict]):
    async with AsyncSessionFactory.begin() as session:
        document_item = Document(
            title=filename
        )

        for item in vector_list_document:
            chunks_item = Embedding(
                embedding=item['embedding'],
                context=item['context'],
            )
            document_item.chunks.append(chunks_item)

        session.add(document_item)

# Создание сессии, поисковый запрос к базе данных, сравнение векторов

async def compare_vectors(vectorized_query: list[float]):
    async with AsyncSessionFactory.begin() as session:
        statement = (
            select(Embedding.context)
            .order_by(Embedding.embedding.cosine_distance(vectorized_query))
            .limit(1)
        )

        result = await session.scalars(statement)

        return result.all()