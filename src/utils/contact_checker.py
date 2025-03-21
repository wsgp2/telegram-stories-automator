import logging
import csv
import pandas as pd
import os
import json
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
import asyncio
import time
from tqdm import tqdm
from configs.settings import RESULTS_DIR

logger = logging.getLogger(__name__)

class ContactChecker:
    """Класс для проверки наличия контактов в Telegram"""
    
    def __init__(self, client_data):
        # Если передан словарь с клиентом, извлекаем объект клиента
        if isinstance(client_data, dict) and 'client' in client_data:
            self.client = client_data['client']
        else:
            # Иначе предполагаем, что передан сам объект клиента
            self.client = client_data
        self.found_users = {}
        self.cache_file = os.path.join(RESULTS_DIR, 'users_cache.json')
        self.cached_users = self._load_cache()
    
    def _load_cache(self):
        """Загрузка кэша проверенных пользователей"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Загружено {len(cache)} пользователей из кэша")
                return cache
            except Exception as e:
                logger.error(f"Ошибка при загрузке кэша: {e}")
        return {}
    
    def _save_cache(self):
        """Сохранение кэша проверенных пользователей"""
        try:
            # Объединяем новых найденных пользователей с кэшем
            merged_cache = {**self.cached_users, **self.found_users}
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(merged_cache, f, ensure_ascii=False, indent=2)
            logger.info(f"Сохранено {len(merged_cache)} пользователей в кэш")
        except Exception as e:
            logger.error(f"Ошибка при сохранении кэша: {e}")
    
    async def check_phone_number(self, phone_number):
        """Проверяет наличие пользователя в Telegram по номеру телефона"""
        try:
            # Нормализация номера телефона
            phone = phone_number.strip()
            if not phone.startswith('+'):
                phone = '+' + phone
            
            # Создание контакта для импорта
            contact = InputPhoneContact(
                client_id=0,  # Произвольный ID
                phone=phone,
                first_name="Check",  # Временное имя
                last_name=""
            )
            
            # Импорт контакта
            result = await self.client(ImportContactsRequest([contact]))
            
            # Проверка результата
            if result.users:
                user = result.users[0]
                user_data = {
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': phone
                }
                self.found_users[phone] = user_data
                return user_data
            else:
                logger.info(f"Пользователь с номером {phone} не найден в Telegram")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при проверке номера {phone_number}: {e}")
            return None
    
    async def process_contacts_file(self, file_path, output_path=None):
        """Обработка файла с контактами"""
        try:
            # Чтение контактов из файла
            contacts = []
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                header = next(csv_reader, None)  # Пропускаем заголовок если есть
                
                for row in csv_reader:
                    if row and len(row) > 0:
                        contacts.append(row[0])  # Предполагаем, что номер телефона в первом столбце
            
            logger.info(f"Загружено {len(contacts)} контактов из файла {file_path}")
            
            # Проверка контактов
            results = []
            for phone in tqdm(contacts, desc="Проверка контактов"):
                result = await self.check_phone_number(phone)
                if result:
                    results.append(result)
                # Пауза для избежания ограничений API
                await asyncio.sleep(0.5)
            
            # Сохранение результатов
            if output_path:
                df = pd.DataFrame(results)
                df.to_csv(output_path, index=False)
                logger.info(f"Результаты сохранены в {output_path}")
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при обработке файла контактов: {e}")
            return []
    
    async def cleanup_contacts(self):
        """Удаление добавленных контактов"""
        try:
            if self.found_users:
                user_ids = [user_data['user_id'] for user_data in self.found_users.values()]
                if user_ids:
                    from telethon.tl.functions.contacts import DeleteContactsRequest
                    await self.client(DeleteContactsRequest(id=user_ids))
                    logger.info(f"Удалено {len(user_ids)} временных контактов")
                self.found_users = {}
        except Exception as e:
            logger.error(f"Ошибка при очистке контактов: {e}")
    
    def get_found_users(self):
        """Возвращает найденных пользователей"""
        return self.found_users
    
    async def get_user_by_username(self, username):
        """
        Получение сущности пользователя по юзернейму
        
        Args:
            username (str): Юзернейм пользователя (без символа @)
            
        Returns:
            Entity или None: Сущность пользователя или None, если пользователь не найден
        """
        try:
            # Проверяем, что клиент корректный
            if not self.client:
                logger.error(f"Отсутствует клиент для поиска пользователя {username}")
                return None
                
            # Удаляем @ если он есть в начале, чтобы избежать двойного @
            if username.startswith('@'):
                username = username[1:]
                
            # Используем get_entity для поиска пользователя по юзернейму
            try:
                entity = await self.client.get_entity(username)
                logger.info(f"Найден пользователь @{username}: {entity.id}")
                return entity
            except ValueError:
                # Пробуем поискать с @
                try:
                    entity = await self.client.get_entity(f"@{username}")
                    logger.info(f"Найден пользователь @{username}: {entity.id}")
                    return entity
                except Exception as e:
                    logger.error(f"Пользователь @{username} не найден: {e}")
                    return None
                
        except Exception as e:
            logger.error(f"Ошибка при поиске пользователя {username}: {e}")
            return None
    
    async def check_usernames_from_file(self, filepath):
        """
        Проверка существования пользователей по юзернейму из файла
        
        Args:
            filepath (str): Путь к CSV-файлу с юзернеймами
            
        Returns:
            list: Список найденных пользователей
        """
        if not os.path.exists(filepath):
            logger.error(f"Файл {filepath} не найден")
            return []
        
        try:
            found_users = []
            
            # Загружаем юзернеймы из CSV файла
            df = pd.read_csv(filepath)
            if 'username' not in df.columns:
                logger.error(f"В файле {filepath} отсутствует колонка 'username'")
                return []
                
            # Предварительно отфильтровываем пользователей, которые уже есть в кэше
            new_usernames = []
            cached_found = []
            
            for _, row in df.iterrows():
                username = row['username'].strip()
                if not username:
                    continue
                
                # Проверяем, есть ли пользователь в кэше
                cache_key = username.lower().replace('@', '')
                if cache_key in self.cached_users:
                    cached_user = self.cached_users[cache_key]
                    cached_found.append(cached_user)
                    logger.info(f"Пользователь @{username} найден в кэше: {cached_user.get('user_id')}")
                else:
                    new_usernames.append(username)
            
            if not new_usernames:
                logger.info(f"Все {len(cached_found)} пользователей уже были проверены ранее")
                # Добавляем найденных из кэша пользователей в общий список
                for user_data in cached_found:
                    self.found_users[user_data['username'].lower().replace('@', '')] = user_data
                return cached_found
                
            logger.info(f"Загружено {len(new_usernames)} новых юзернеймов для проверки")
            
            # Создаём tqdm прогресс-бар для отслеживания прогресса
            for username in tqdm(new_usernames, desc="Проверка юзернеймов", unit="user"):
                # Получаем информацию о пользователе
                user = await self.get_user_by_username(username)
                if user:
                    # Сохраняем найденного пользователя
                    user_data = {
                        'user_id': user.id,
                        'username': username,
                        'first_name': getattr(user, 'first_name', ''),
                        'last_name': getattr(user, 'last_name', '')
                    }
                    found_users.append(user_data)
                    
                    # Добавляем в общий словарь найденных пользователей
                    cache_key = username.lower().replace('@', '')
                    self.found_users[cache_key] = user_data
                    
                # Небольшая задержка, чтобы не перегружать API
                await asyncio.sleep(1)
            
            # Объединяем результаты с кэшем
            all_found = found_users + cached_found
            logger.info(f"Найдено {len(found_users)} новых пользователей из {len(new_usernames)}")
            logger.info(f"Всего найдено {len(all_found)} пользователей (включая кэшированных)")
            
            # Сохраняем обновленный кэш
            self._save_cache()
            
            return all_found
            
        except Exception as e:
            logger.error(f"Ошибка при обработке файла с юзернеймами: {e}")
            return []
