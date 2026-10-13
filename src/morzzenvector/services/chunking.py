from markitdown import MarkItDown # библиотека для форматирования документов в .md
from langchain_text_splitters import RecursiveCharacterTextSplitter # библиотека для чанкирования
from shutil import copyfileobj

from morzzenvector import Settings

def chunking_document(name: str, settings: Settings) -> list[str]:

    # Создание и сохранение временного файла

    with open(settings.path_temp_file, 'wb') as temp_file:
        copyfileobj(name, temp_file)

    # Форматирование входящего файла .docx, .pdf и пр. в формат .md

    md = MarkItDown(enable_plugins=False) # Set to True to enable plugins
    formated_file = md.convert(settings.path_temp_file).markdown

    # Чанкирование отформатированного файла

    splitter = RecursiveCharacterTextSplitter(chunk_size=settings.chunk_size,
                                                   chunk_overlap=settings.chunk_overlap,
                                                   add_start_index=True)

    chunk_list = splitter.split_text(formated_file)

    return chunk_list