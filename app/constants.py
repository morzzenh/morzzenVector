# СТРУКТУРА: неизменяемые константы (MIME-типы) отделены от настроек из .env (config.py).

# Форматы документов Microsoft Word

DOC = 'application/msword'
DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
DOCM = 'application/vnd.ms-word.document.macroEnabled.12'
DOT = 'application/msword'
DOTX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.template'

# Формат PDF

PDF = 'application/pdf'

# Текстовые и размечаемые форматы

TXT = 'text/plain'
MD = 'text/markdown'
CSV = 'text/csv'
HTML = 'text/html'
JSON = 'application/json'
XML = 'application/xml'

# УЛУЧШЕНИЕ: список разрешённых типов лежит рядом с константами, а не в main.py.
# ЗАМЕЧАНИЕ: content_type присылает клиент и он подделывается — это лишь первичный фильтр.
# БЫЛО (в app/main.py): VALID_TYPES_FILES = [DOC, DOCX, DOCM, DOT, DOTX, PDF, TXT, MD, CSV, HTML, JSON, XML]
VALID_TYPES_FILES = [DOC, DOCX, DOCM, DOT, DOTX, PDF, TXT, MD, CSV, HTML, JSON, XML]
