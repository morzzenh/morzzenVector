# Пакет app.db — всё про базу данных: models.py (таблицы), session.py (подключение),
# repository.py (запросы).
#
# «Витрина» пакета: снаружи пишем коротко:
#     from app.db import init_db, compare_vectors, Document
# вместо:
#     from app.db.session import init_db
#     from app.db.repository import compare_vectors
#     from app.db.models import Document
#
# ПОРЯДОК ИМПОРТОВ НИЖЕ ВАЖЕН (иначе циклический импорт и ImportError):
#   models -> session -> repository, потому что session использует models.Base,
#   а repository использует и models, и session. Внутри пакета (session.py, repository.py)
#   модули импортируют друг друга напрямую (from app.db.models import ...), а не через
#   `from app.db import ...`, пока пакет ещё не дозагружен.
#
# __all__ — список публичных имён пакета (для `from app.db import *`, IDE и линтеров).
#
# ---- Как работали бы импорты БЕЗ этого файла ----
# Проверено: без app/db/__init__.py работали бы только длинные импорты
#     from app.db.session import init_db     и т.п.
# Короткого `from app.db import init_db` не было бы. Плюс отсутствия файла — ловушка с
# циклическим импортом невозможна: при импорте app.db.session код пакета app.db не выполняется.

from app.db.models import Base, Document, Embedding
from app.db.session import AsyncSessionFactory, async_engine, init_db
from app.db.repository import compare_vectors, vector_loading

__all__ = [
    'AsyncSessionFactory',
    'Base',
    'Document',
    'Embedding',
    'async_engine',
    'compare_vectors',
    'init_db',
    'vector_loading',
]
