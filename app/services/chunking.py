import os
import tempfile
from shutil import copyfileobj

from markitdown import MarkItDown  # библиотека для форматирования документов в .md
from langchain_text_splitters import RecursiveCharacterTextSplitter  # библиотека для чанкирования

# ИСПРАВЛЕНО: импорт `from app.app_config import *` заменён на явный.
# `import *` засоряет пространство имён и скрывает, откуда берутся переменные.
# БЫЛО: from app.app_config import *
# БЫЛО: from app.config import CHUNK_SIZE, CHUNK_OVERLAP
# БЫЛО: from app.config import settings
# СОКРАЩЕНО: from app import settings (витрина пакета, см. app/__init__.py)
from app import settings

# УЛУЧШЕНИЕ: сплиттер создаётся один раз при импорте, а не при каждом вызове.
# ИСПРАВЛЕНО: add_start_index=True убран — он работает только в create_documents(),
# а при split_text() ничего не делает (вводил в заблуждение).
# БЫЛО (внутри функции, при каждом вызове; числа зашиты в код):
# БЫЛО: text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
# БЫЛО:                                                chunk_overlap=200,
# БЫЛО:                                                add_start_index=True)
_splitter = RecursiveCharacterTextSplitter(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
# БЫЛО (тоже внутри функции): md = MarkItDown(enable_plugins=False) # Set to True to enable plugins
_markitdown = MarkItDown(enable_plugins=False)


# БЫЛО: def chunking_file(name) -> list[str]:
# ИСПРАВЛЕНО: функция принимает имя файла — нужно расширение для временного файла.
def chunking_file(fileobj, filename: str) -> list[str]:
    """Функция чанкирования файла."""
    # ИСПРАВЛЕНО: раньше файл писался в общий PATH_TEMP_FILE БЕЗ расширения:
    #   1) MarkItDown выбирает конвертер по расширению; без него тип угадывается и PDF/docx
    #      могли превращаться в мусор -> мусорные эмбеддинги -> «поиск выдаёт не то»;
    #   2) параллельные загрузки затирали друг друга;
    #   3) файл никогда не удалялся.
    # Теперь: уникальный временный файл с настоящим расширением, удаляется в finally.
    # БЫЛО: with open(PATH_TEMP_FILE, 'wb') as temp_file:
    # БЫЛО:     copyfileobj(name, temp_file)
    suffix = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_path = temp_file.name
        copyfileobj(fileobj, temp_file)

    try:
        # Форматирование входящего файла .docx, .pdf и пр. в формат .md
        # БЫЛО: formated_file = md.convert(PATH_TEMP_FILE).markdown
        formated_file = _markitdown.convert(temp_path).markdown
    finally:
        os.remove(temp_path)

    # Чанкирование отформатированного файла
    # БЫЛО: chunk_list = text_splitter.split_text(formated_file)
    # БЫЛО: return chunk_list
    return _splitter.split_text(formated_file)
