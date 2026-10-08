# Пакет app.api — HTTP-слой: эндпоинты (routes.py) и схемы запросов (schemas.py).
#
# «Витрина» пакета: благодаря импортам ниже снаружи пишем коротко:
#     from app.api import router          # вместо: from app.api.routes import router
# а раскладку по файлам внутри можно менять, не трогая импорты по всему проекту.
#
# __all__ — список публичных имён (для `from app.api import *`, IDE и линтеров).
#
# Порядок важен: schemas импортируется РАНЬШЕ routes, потому что routes сам использует
# SearchRequest (внутри пакета импортируем модуль напрямую: from app.api.schemas import ...).
#
# ---- Как работали бы импорты БЕЗ этого файла ----
# Проверено: без app/api/__init__.py строка `from app.api.routes import router` в main.py
# работала бы — api/ стала бы пакетом-пространством имён. Но `from app.api import router`
# и `__all__` стали бы невозможны, а pytest/mypy/Poetry хуже считали бы папку частью проекта.

from app.api.schemas import SearchRequest
from app.api.routes import router

__all__ = ['router', 'SearchRequest']
