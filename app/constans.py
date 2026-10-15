# Документы Microsoft Word в формате MIME

DOC = 'application/msword'
DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
DOCM = 'application/vnd.ms-word.document.macroEnabled.12'
DOT = 'application/msword'
DOTX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.template'

# Документы PDF в формате MIME

PDF = 'application/pdf'

# Текстовые и размечаемые документы в формате MIME

TXT = 'text/plain'
MD = 'text/markdown'
CSV = 'text/csv'
HTML = 'text/html'
JSON = 'application/json'
XML = 'application/xml'

# Список разрешенных форматов загружаемого файла

VALID_TYPES_FILES = [DOC, DOCX, DOCM, DOT, DOTX, PDF, TXT, MD, CSV, HTML, JSON, XML]