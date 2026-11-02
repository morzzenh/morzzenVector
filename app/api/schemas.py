from pydantic import BaseModel, Field, field_validator

from app import settings

# Класс поискового запроса с указанием параметра top_k (кол-во чанков в выдаче)

class SearchRequest(BaseModel):

    query: str = Field()

    top_k: int = Field(default=settings.top_k, ge=1, le=20)
