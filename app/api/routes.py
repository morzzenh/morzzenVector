import hashlib
from typing import Annotated

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import WithJsonSchema
from starlette.concurrency import run_in_threadpool

from app import settings
from app.api.schemas import SearchRequest
from app.constans import VALID_TYPES_FILES
from app.database import check_unique, compare_vectors, vector_loading
from app.services import chunking_document, create_vector_document, create_vector_query

router = APIRouter()

# Временный костыль
SwaggerFileFormat = Annotated[UploadFile, WithJsonSchema({"type": "string", "format": "binary"})]


# Загрузка текстовых файлов и валидация формата
@router.post("/uploadfile")
async def upload_file(files: list[SwaggerFileFormat] = File()):

    chunks, documents_names, failed_documents = [], [], []

    # Перебор всех файлов в цикле
    for file in files:
        try:
            if file.content_type not in VALID_TYPES_FILES:
                raise HTTPException(
                    status_code=415,
                    detail=f"Неподдерживаемый тип файла. Допустимые форматы: {VALID_TYPES_FILES}",
                )
            if file.size > settings.max_file_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"Загружаемый файл большого размера. "
                           f"Допустимый размер: {settings.max_file_size_mb} мб",
                )
            # Кэширование файла для последующей проверки уникальности
            document_hash = hashlib.sha256(
                await file.read()
            ).hexdigest()  # алгоритм кэширования sha256, вид hexdigest (a69f12df83)
            await file.seek(0)

            # Проверка уникальности загружаемого файла
            if not await check_unique(document_hash):
                raise HTTPException(status_code=409, detail="Такой файл уже был загружен ранее")

            # Обработка текстового файла для модели эмбеддинга
            chunked_text = await run_in_threadpool(
                chunking_document, file.file, file.filename
            )  # чанкирование всего текста асинхронно

            # Если документ пустой, выйдет ошибка
            if not chunked_text:
                raise HTTPException(status_code=422, detail="Не удалось извлечь текст из файла")

            vector_list_document = await create_vector_document(
                chunked_text
            )  # векторизация всех чанков

            # Загрузка вектора в базу данных, проверка на уникальность файла
            if not await vector_loading(file.filename, document_hash, vector_list_document):
                raise HTTPException(status_code=409, detail="Такой файл уже был загружен ранее")

            chunks.append(len(chunked_text))

            documents_names.append(file.filename)

        # Отлавливание ошибок, чтобы нужны файлы загрузились и приложение не упало,
        # но ошибки были показаны
        except HTTPException as e:
            failed_documents.append(
                {"filename": file.filename, "status_code": e.status_code, "detail": e.detail}
            )

    result = {
        "status": f'Документы "{",".join(documents_names)}" успешно загружены в базу',
        "all chunks": sum(chunks),
        "all documents": len(documents_names),
    }

    if not failed_documents:
        return result

    result.update(
        {
            "errors": "Ошибка загрузки документов:",
            "status_errors": failed_documents,
        }
    )
    return result


# Поисковый запрос к Базе Данных
@router.post("/search")
async def search(request: SearchRequest):
    # Векторизация поискового запроса
    vectorized_question = await create_vector_query(request.query)

    # Сравнение векторов базы данных и поискового запроса
    result = await compare_vectors(request.query, vectorized_question, request.top_k)

    return {"status": "Поиск по базе данных выполнен успешно!", "results": result}
