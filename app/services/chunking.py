import os
import tempfile
from pathlib import Path

from markitdown import MarkItDown # библиотека для форматирования документов в .md
from langchain_text_splitters import RecursiveCharacterTextSplitter # библиотека для чанкирования
from shutil import copyfileobj # функция копирования файла как объекта

from app import settings

''' Создание форматера входящего файла .docx, .pdf и пр. в формат .md '''

_md = MarkItDown(enable_plugins=False) # Set to True to enable plugins

''' Создание класса разделителя чанков '''

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap
)

''' Функция чанкирования текста, при котором создается tempfile '''

def chunking_document(file, filename: str) -> list[str]:

    suffix = Path(filename).suffix # отделение расширения файла для передачи в tempfile

    # Создание и сохранение временного файла класса NamedTemporaryFile (именованный файл)

    with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False, dir=Path(__file__).resolve().parent.parent / 'storage') as temp_file:

        copyfileobj(file, temp_file) # функция копирования загружаемого файла name в temp_file
        name_tempfile = temp_file.name

    try:
        # Форматирование загружаемого текстового файла в формат .md
        formated_file = _md.convert(name_tempfile).markdown

    finally:
        # Удаление tempfile через os
        os.remove(name_tempfile)

    return _splitter.split_text(formated_file)