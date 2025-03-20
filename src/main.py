import os
import sys
import logging
import asyncio
import json
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта
sys.path.append(str(Path(__file__).parent.parent))

from utils.account_manager import AccountManager
from utils.contact_checker import ContactChecker
from utils.story_publisher import StoryPublisher
from configs.settings import CONTACTS_DIR, RESULTS_DIR, DEFAULT_CONTACTS_FILE, STORIES_DIR

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(RESULTS_DIR, 'app.log'))
    ]
)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Запуск приложения Telegram Stories Automator")
    
    # Проверка наличия необходимых директорий и файлов
    if not os.path.exists(STORIES_DIR) or not any(os.scandir(STORIES_DIR)):
        logger.error(f"Директория {STORIES_DIR} не существует или пуста. Добавьте видео файлы для сторис.")
        return
    
    # Инициализация менеджера аккаунтов
    account_manager = AccountManager()
    clients = await account_manager.setup_clients()
    
    if not clients:
        logger.error("Не удалось настроить ни один клиент Telegram. Проверьте конфигурацию аккаунтов.")
        return
    
    logger.info(f"Успешно настроено {len(clients)} клиентов Telegram")
    
    try:
        # Запрос пути к файлу с контактами или использование стандартного
        contacts_file = input(f"Введите путь к файлу контактов (или нажмите Enter для использования {DEFAULT_CONTACTS_FILE}): ")
        if not contacts_file:
            contacts_file = DEFAULT_CONTACTS_FILE
        
        if not os.path.exists(contacts_file):
            logger.error(f"Файл контактов {contacts_file} не найден.")
            return
        
        # Создание объекта проверки контактов
        client = account_manager.get_client(0)  # Используем первый клиент для проверки
        contact_checker = ContactChecker(client)
        
        # Обработка файла контактов
        output_file = os.path.join(RESULTS_DIR, 'telegram_users.csv')
        users = await contact_checker.process_contacts_file(contacts_file, output_file)
        
        if not users:
            logger.warning("Не найдено пользователей Telegram среди контактов.")
            return
        
        logger.info(f"Найдено {len(users)} пользователей Telegram среди контактов")
        
        # Создание объекта публикации сторис
        publisher = StoryPublisher(client)
        
        # Публикация сторис с упоминаниями
        success_count = await publisher.batch_publish_stories(users)
        logger.info(f"Успешно опубликовано {success_count} сторис с упоминаниями")
        
        # Очистка контактов
        await contact_checker.cleanup_contacts()
        
    except Exception as e:
        logger.error(f"Произошла ошибка при выполнении приложения: {e}")
    finally:
        # Закрытие клиентов
        await account_manager.close_all_clients()
        logger.info("Работа приложения завершена")

if __name__ == "__main__":
    # Запуск асинхронной функции main
    asyncio.run(main())
