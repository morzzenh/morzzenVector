# Пакет app.services — бизнес-логика без HTTP и без SQL: чанкирование (chunking.py)
# и эмбеддинги (embedding.py).
#
# «Витрина» пакета: снаружи пишем коротко:
#     from app.services import chunking_file, create_vector, vector_search
# вместо двух длинных строк с app.services.chunking и app.services.embedding.
#
# ЦЕНА СОКРАЩЕНИЯ: теперь любой импорт чего-либо из app.services загружает ОБА модуля, в том
# числе embedding.py, который при импорте создаёт клиент Ollama. Для юнит-теста чанкирования
# это лишнее: нужно либо импортировать напрямую (from app.services.chunking import chunking_file),
# либо подменять клиент в тесте. Пока проект маленький, удобство важнее.
#
# __all__ — список публичных имён пакета (для `from app.services import *`, IDE и линтеров).
#
# ---- Как работали бы импорты БЕЗ этого файла ----
# Проверено: без app/services/__init__.py работали бы длинные импорты
#     from app.services.chunking import chunking_file
#     from app.services.embedding import create_vector, vector_search
# а короткого `from app.services import chunking_file` не было бы; pytest/mypy/Poetry
# реже считали бы папку частью проекта.

from app.services.chunking import chunking_file
from app.services.embedding import create_vector, vector_search

__all__ = ['chunking_file', 'create_vector', 'vector_search']
