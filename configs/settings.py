import os
from pathlib import Path

# Базовые пути проекта
BASE_DIR = Path(__file__).parent.parent
CONTACTS_DIR = BASE_DIR / "data" / "contacts"
STORIES_DIR = BASE_DIR / "data" / "stories"
SESSIONS_DIR = BASE_DIR / "data" / "sessions"
RESULTS_DIR = BASE_DIR / "data" / "results"

# Создаем директории, если они не существуют
os.makedirs(CONTACTS_DIR, exist_ok=True)
os.makedirs(STORIES_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Настройки приложения
MAX_MENTIONS_PER_STORY = 30
DELAY_BETWEEN_STORIES = 60  # Задержка между публикациями сторис в секундах
MAX_RETRIES = 3  # Максимальное количество попыток при ошибках

# Пути к файлам
ACCOUNTS_CONFIG = BASE_DIR / "configs" / "accounts.json"
DEFAULT_CONTACTS_FILE = CONTACTS_DIR / "contacts.csv"
