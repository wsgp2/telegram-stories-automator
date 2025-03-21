import json
import logging
from telethon import TelegramClient, errors
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
                if 'proxy' in account:
                    proxy_data = account['proxy']
                    proxy_type = proxy_data.get('type', 'socks5')  # По умолчанию используем socks5
                    
                    # Создаем конфигурацию прокси
                    proxy = {
                        'proxy_type': proxy_type,
                        'addr': proxy_data['server'],
                        'port': int(proxy_data['port']),
                        'rdns': True
                    }
                    
                    # Добавляем аутентификацию, если предоставлена
                    if 'username' in proxy_data and 'password' in proxy_data:
                        proxy['username'] = proxy_data['username']
                        proxy['password'] = proxy_data['password']
                    
                    # Логируем настройки прокси для отладки
                    logger.info(f"Настройки прокси: {proxy_type} {proxy_data['server']}:{proxy_data['port']}")
                
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
                    code = input(f"Введите код подтверждения для аккаунта {account['phone']}: ")
                    
                    try:
                        await client.sign_in(account['phone'], code)
                    except errors.SessionPasswordNeededError:
                        # Если включена двухфакторная аутентификация
                        if 'two_fa_password' in account and account['two_fa_password']:
                            password = account['two_fa_password']
                            logger.info(f"Используем сохраненный пароль 2FA для аккаунта {account['phone']}")
                        else:
                            password = input(f"Введите пароль двухфакторной аутентификации для аккаунта {account['phone']}: ")
                        await client.sign_in(password=password)
                    except Exception as auth_error:
                        logger.error(f"Ошибка авторизации аккаунта {i+1}: {auth_error}")
                        continue
                    
                    logger.info(f"Аккаунт {i+1} успешно авторизован")
                
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
