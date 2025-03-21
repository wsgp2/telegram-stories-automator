#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Stories Automator - Основной скрипт запуска

Автоматизация публикации сторис в Telegram с проверкой номеров и упоминаниями пользователей.

Автор: Сергей Дышкант (SergD)
Контакт: https://t.me/sergei_dyshkant
"""

import os
import sys
import logging
import json
import asyncio
import random
from pathlib import Path

# Добавляем корневую директорию проекта в PATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.account_manager import AccountManager
from utils.contact_checker import ContactChecker
from utils.story_publisher import StoryPublisher
from configs.settings import CONTACTS_DIR, STORIES_DIR, RESULTS_DIR, BASE_DIR, DELAY_BETWEEN_STORIES

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_DIR, 'telegram_stories.log'))
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска приложения"""
    try:
        logger.info("Запуск Telegram Stories Automator")
        
        # Проверяем наличие необходимых директорий
        os.makedirs(CONTACTS_DIR, exist_ok=True)
        os.makedirs(STORIES_DIR, exist_ok=True)
        os.makedirs(RESULTS_DIR, exist_ok=True)
        
        # Получаем список аккаунтов
        account_manager = AccountManager()
        clients = await account_manager.setup_clients()
        
        if not clients:
            logger.error("Не удалось загрузить ни одного аккаунта")
            return
        
        logger.info(f"Загружено {len(clients)} аккаунтов")
        
        # Проверяем существование контактов и получаем список найденных
        mode = input("Выберите режим проверки (1 - по номеру телефона, 2 - по юзернейму): ")
        
        found_users = []
        
        if mode == "1":
            # Проверка по номеру телефона
            contacts_file = input(f"Введите путь к файлу с номерами (или нажмите Enter для 'contacts_example.csv'): ")
            if not contacts_file:
                contacts_file = os.path.join(CONTACTS_DIR, 'contacts_example.csv')
            elif not os.path.isabs(contacts_file) and not contacts_file.startswith(CONTACTS_DIR):
                # Если путь не абсолютный и не начинается с CONTACTS_DIR, добавляем CONTACTS_DIR
                contacts_file = os.path.join(CONTACTS_DIR, contacts_file)
            
            logger.info(f"Проверка контактов из файла {contacts_file}")
            
            for i, client in enumerate(clients):
                checker = ContactChecker(client)
                user_contacts = await checker.check_contacts_from_file(contacts_file)
                found_users.extend(user_contacts)
                
                if i < len(clients) - 1:
                    # Задержка между аккаунтами, чтобы не перегружать API
                    logger.info(f"Ожидание перед проверкой с нового аккаунта...")
                    await asyncio.sleep(DELAY_BETWEEN_STORIES)
        
        elif mode == "2":
            # Проверка по юзернейму
            usernames_file = input(f"Введите путь к файлу с юзернеймами (или нажмите Enter для 'contacts_test.csv'): ")
            if not usernames_file:
                usernames_file = os.path.join(CONTACTS_DIR, 'contacts_test.csv')
            elif not os.path.isabs(usernames_file) and not usernames_file.startswith(CONTACTS_DIR):
                # Если путь не абсолютный и не начинается с CONTACTS_DIR, добавляем CONTACTS_DIR
                usernames_file = os.path.join(CONTACTS_DIR, usernames_file)
            
            logger.info(f"Проверка юзернеймов из файла {usernames_file}")
            
            for i, client in enumerate(clients):
                checker = ContactChecker(client)
                username_users = await checker.check_usernames_from_file(usernames_file)
                found_users.extend(username_users)
                
                if i < len(clients) - 1:
                    # Задержка между аккаунтами, чтобы не перегружать API
                    logger.info(f"Ожидание перед проверкой с нового аккаунта...")
                    await asyncio.sleep(DELAY_BETWEEN_STORIES)
        
        else:
            logger.error("Неверный режим проверки")
            return
        
        if not found_users:
            logger.warning("Не найдено ни одного пользователя для упоминания")
            return
        
        logger.info(f"Найдено {len(found_users)} пользователей для упоминания")
        
        # Публикация сторис с упоминаниями
        should_publish = input("Опубликовать сторис с упоминаниями? (y/n): ")
        if should_publish.lower() != 'y':
            logger.info("Публикация отменена пользователем")
            return
        
        # Проверяем наличие файлов сторис
        story_files = [f for f in os.listdir(STORIES_DIR) 
                      if os.path.isfile(os.path.join(STORIES_DIR, f)) 
                      and f.lower().endswith(('.mp4', '.avi', '.mov', '.jpg', '.jpeg', '.png'))]
        
        if not story_files:
            logger.error(f"В директории {STORIES_DIR} не найдены файлы для сторис")
            return
        
        logger.info(f"Найдено {len(story_files)} файлов для сторис")
        
        # Публикуем сторис по очереди с разных аккаунтов
        total_published = 0
        users_per_story = min(10, len(found_users))  # Максимум 10 упоминаний на одну сторис
        
        # Разбиваем пользователей на группы
        user_groups = [found_users[i:i+users_per_story] for i in range(0, len(found_users), users_per_story)]
        
        for i, client in enumerate(clients):
            publisher = StoryPublisher(client)
            
            # Получаем группы для текущего аккаунта
            account_groups = user_groups[i::len(clients)]
            if not account_groups:
                continue
            
            logger.info(f"Публикация сторис с аккаунта {i+1} с {len(account_groups)} группами упоминаний")
            
            for group in account_groups:
                # Выбираем случайный файл сторис
                story_file = os.path.join(STORIES_DIR, random.choice(story_files))
                
                # Публикуем сторис
                result = await publisher.publish_story_with_mentions(group, story_file)
                
                if result:
                    total_published += 1
                    logger.info(f"Опубликована сторис {total_published}/{len(account_groups)}")
                else:
                    logger.warning(f"Не удалось опубликовать сторис с аккаунта {i+1}")
                
                # Задержка между публикациями
                await asyncio.sleep(DELAY_BETWEEN_STORIES)
        
        logger.info(f"Всего опубликовано {total_published} сторис")
        
    except KeyboardInterrupt:
        logger.info("Работа программы прервана пользователем")
    except Exception as e:
        logger.error(f"Ошибка при выполнении программы: {e}")
    finally:
        # Закрываем все клиенты
        try:
            await account_manager.close_all_clients()
        except Exception as e:
            logger.error(f"Ошибка при закрытии клиентов: {e}")
        logger.info("Программа завершена")

if __name__ == "__main__":
    asyncio.run(main())
