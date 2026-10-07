import os
from dotenv import load_dotenv

load_dotenv()

# Путь сохранения временного загрузочного файла

PATH_TEMP_FILE = os.getenv('PATH_TEMP_FILE')

# Используемая модель для эмбеддинга

LLM_MODEL = os.getenv('LLM_MODEL')

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