from markitdown import MarkItDown # библиотека для форматирования документов в .md
from langchain_text_splitters import RecursiveCharacterTextSplitter # библиотека для чанкирования
from app.app_config import *
from shutil import copyfileobj

def chunking_file(name) -> list[str]:

    # Создание и сохранение временного файла

    with open(PATH_TEMP_FILE, 'wb') as temp_file:
        copyfileobj(name, temp_file)

    # Форматирование входящего файла .docx, .pdf и пр. в формат .md

    md = MarkItDown(enable_plugins=False) # Set to True to enable plugins
    formated_file = md.convert(PATH_TEMP_FILE).markdown

    # Чанкирование отформатированного файла

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
                                                   chunk_overlap=200,
                                                   add_start_index=True)

    chunk_list = text_splitter.split_text(formated_file)

    return chunk_list