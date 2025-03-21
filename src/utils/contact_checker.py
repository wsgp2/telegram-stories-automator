import logging
import csv
import pandas as pd
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
import asyncio
import time
from tqdm import tqdm

logger = logging.getLogger(__name__)

class ContactChecker:
    """Класс для проверки наличия контактов в Telegram"""
    
    def __init__(self, client):
        self.client = client
        self.found_users = {}
    
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
            # Добавляем @ если его нет в начале
            if not username.startswith('@'):
                username = '@' + username
                
            entity = await self.client.get_entity(username)
            logger.info(f"Найден пользователь {username}: {entity.id}")
            return entity
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
            # Чтение юзернеймов из файла
            usernames = []
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if 'username' in row:
                        usernames.append(row['username'])
            
            if not usernames:
                logger.warning(f"В файле {filepath} не найдены юзернеймы")
                return []
            
            logger.info(f"Загружено {len(usernames)} юзернеймов для проверки")
            
            # Проверка юзернеймов и получение пользователей
            found_users = []
            for username in tqdm(usernames, desc="Проверка юзернеймов", unit="user"):
                entity = await self.get_user_by_username(username)
                if entity:
                    found_users.append({
                        'user_id': entity.id,
                        'username': username,
                        'first_name': getattr(entity, 'first_name', ''),
                        'last_name': getattr(entity, 'last_name', '')
                    })
                # Небольшая задержка, чтобы не перегружать API
                await asyncio.sleep(1)
            
            logger.info(f"Найдено {len(found_users)} пользователей из {len(usernames)}")
            
            # Сохраняем результаты в CSV
            if found_users:
                output_dir = os.path.join(os.path.dirname(filepath), 'results')
                os.makedirs(output_dir, exist_ok=True)
                
                output_file = os.path.join(output_dir, 'found_users.csv')
                df = pd.DataFrame(found_users)
                df.to_csv(output_file, index=False, encoding='utf-8')
                
                logger.info(f"Результаты сохранены в {output_file}")
            
            return found_users
            
        except Exception as e:
            logger.error(f"Ошибка при проверке юзернеймов из файла {filepath}: {e}")
            return []
