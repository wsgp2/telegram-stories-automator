import json
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import os

from configs.settings import ACCOUNTS_CONFIG, SESSIONS_DIR

logger = logging.getLogger(__name__)

class AccountManager:
    """Класс для управления аккаунтами Telegram"""
    
    def __init__(self):
        self.accounts = []
        self.clients = []
        self._load_accounts()
    
    def _load_accounts(self):
        """Загрузка данных аккаунтов из конфигурационного файла"""
        try:
            with open(ACCOUNTS_CONFIG, 'r') as f:
                config = json.load(f)
                self.accounts = config.get('accounts', [])
            logger.info(f"Загружено {len(self.accounts)} аккаунтов из конфигурации")
        except Exception as e:
            logger.error(f"Ошибка при загрузке аккаунтов: {e}")
            self.accounts = []
    
    async def setup_clients(self):
        """Настройка и авторизация клиентов Telegram"""
        self.clients = []
        
        for i, account in enumerate(self.accounts):
            try:
                session_file = os.path.join(SESSIONS_DIR, f"account_{i}.session")
                
                # Настройка прокси, если указан
                proxy = None
                if 'proxy' in account and all(account['proxy'].values()):
                    proxy_data = account['proxy']
                    proxy = {
                        'proxy_type': 'socks5',  # Можно изменить на http/https при необходимости
                        'addr': proxy_data['server'],
                        'port': int(proxy_data['port']),
                        'username': proxy_data['username'],
                        'password': proxy_data['password'],
                        'rdns': True
                    }
                
                # Создание клиента
                client = TelegramClient(
                    session_file,
                    api_id=account['api_id'],
                    api_hash=account['api_hash'],
                    proxy=proxy
                )
                
                # Подключение к Telegram
                await client.connect()
                
                # Проверка авторизации и логин при необходимости
                if not await client.is_user_authorized():
                    logger.info(f"Аккаунт {i+1} не авторизован, отправка кода подтверждения")
                    await client.send_code_request(account['phone'])
                    
                    # Здесь должен быть запрос кода у пользователя
                    verification_code = input(f"Введите код подтверждения для аккаунта {account['phone']}: ")
                    
                    try:
                        await client.sign_in(account['phone'], verification_code)
                        logger.info(f"Аккаунт {i+1} успешно авторизован")
                    except Exception as auth_error:
                        logger.error(f"Ошибка авторизации аккаунта {i+1}: {auth_error}")
                        continue
                
                # Добавление клиента в список
                self.clients.append({
                    'client': client,
                    'account_info': account,
                    'index': i
                })
                logger.info(f"Клиент для аккаунта {i+1} успешно настроен")
                
            except Exception as e:
                logger.error(f"Ошибка при настройке клиента для аккаунта {i+1}: {e}")
        
        logger.info(f"Настроено {len(self.clients)} клиентов из {len(self.accounts)} аккаунтов")
        return self.clients
    
    async def close_all_clients(self):
        """Закрытие всех клиентских сессий"""
        for client_data in self.clients:
            try:
                await client_data['client'].disconnect()
                logger.info(f"Клиент для аккаунта {client_data['index']+1} отключен")
            except Exception as e:
                logger.error(f"Ошибка при закрытии клиента {client_data['index']+1}: {e}")
    
    def get_client(self, index=0):
        """Получение клиента по индексу"""
        if 0 <= index < len(self.clients):
            return self.clients[index]['client']
        return None
    
    def get_all_clients(self):
        """Получение всех настроенных клиентов"""
        return [data['client'] for data in self.clients]
