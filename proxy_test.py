#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки работоспособности прокси
"""
import socket
import socks
import requests
import telethon
from telethon import TelegramClient
import asyncio
import logging
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация прокси
PROXY_SETTINGS = {
    'socks5': {
        'server': '217.29.63.40',
        'port': 13918,
        'username': '4XEYdx',
        'password': 'b6em48',
    },
    'ipv6': {
        'server': '2a06:c006:a7ff:5e95:0f0d:25bc:4ba6:3bb2',
        'port': 13918,
        'username': '4XEYdx',
        'password': 'b6em48',
    }
}

# Telegram API аутентификация
API_ID = '14749377'
API_HASH = 'd92c61459052f0607f6ed29fef08d939'
PHONE = '+79222474175'

def test_requests_with_proxy():
    """Тестирование подключения через библиотеку Requests"""
    logger.info("Тестирование подключения через Requests...")
    
    try:
        # Настройка прокси
        proxies = {
            'http': f"socks5://{PROXY_SETTINGS['socks5']['username']}:{PROXY_SETTINGS['socks5']['password']}@{PROXY_SETTINGS['socks5']['server']}:{PROXY_SETTINGS['socks5']['port']}",
            'https': f"socks5://{PROXY_SETTINGS['socks5']['username']}:{PROXY_SETTINGS['socks5']['password']}@{PROXY_SETTINGS['socks5']['server']}:{PROXY_SETTINGS['socks5']['port']}"
        }
        
        # Проверяем подключение
        start_time = time.time()
        response = requests.get('https://api.ipify.org/?format=json', proxies=proxies, timeout=10)
        end_time = time.time()
        
        logger.info(f"Успешное подключение через Requests с SOCKS5 прокси!")
        logger.info(f"Ваш внешний IP: {response.json()['ip']}")
        logger.info(f"Время ответа: {end_time - start_time:.2f} секунд")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при подключении через Requests с SOCKS5 прокси: {e}")
        return False

async def test_telegram():
    """Тестирование подключения к Telegram API"""
    logger.info("Тестирование подключения к Telegram API...")
    
    try:
        # Настройка прокси
        proxy = {
            'proxy_type': 'socks5',
            'addr': PROXY_SETTINGS['socks5']['server'],
            'port': PROXY_SETTINGS['socks5']['port'],
            'username': PROXY_SETTINGS['socks5']['username'],
            'password': PROXY_SETTINGS['socks5']['password'],
            'rdns': True
        }
        
        # Создание клиента
        client = TelegramClient(
            'proxy_test_session',
            api_id=API_ID,
            api_hash=API_HASH,
            proxy=proxy
        )
        
        logger.info("Подключение к Telegram...")
        await client.connect()
        
        if await client.is_user_authorized():
            logger.info("Клиент уже авторизован. Подключение успешно!")
            me = await client.get_me()
            logger.info(f"Имя пользователя: {me.first_name} {me.last_name if me.last_name else ''}")
            logger.info(f"Username: @{me.username if me.username else 'не указан'}")
        else:
            logger.info("Клиент не авторизован, но соединение установлено.")
            logger.info("Для полной проверки требуется авторизация.")
        
        await client.disconnect()
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при подключении к Telegram: {e}")
        return False

# Тестирование IPv6-прокси
async def test_telegram_ipv6():
    """Тестирование подключения к Telegram API через IPv6 прокси"""
    logger.info("Тестирование подключения к Telegram API через IPv6...")
    
    try:
        # Настройка прокси
        proxy = {
            'proxy_type': 'socks5',
            'addr': PROXY_SETTINGS['ipv6']['server'],
            'port': PROXY_SETTINGS['ipv6']['port'],
            'username': PROXY_SETTINGS['ipv6']['username'],
            'password': PROXY_SETTINGS['ipv6']['password'],
            'rdns': True
        }
        
        # Создание клиента
        client = TelegramClient(
            'proxy_test_session_ipv6',
            api_id=API_ID,
            api_hash=API_HASH,
            proxy=proxy
        )
        
        logger.info("Подключение к Telegram через IPv6...")
        await client.connect()
        
        if await client.is_user_authorized():
            logger.info("Клиент уже авторизован. Подключение через IPv6 успешно!")
            me = await client.get_me()
            logger.info(f"Имя пользователя: {me.first_name} {me.last_name if me.last_name else ''}")
            logger.info(f"Username: @{me.username if me.username else 'не указан'}")
        else:
            logger.info("Клиент не авторизован, но соединение через IPv6 установлено.")
            logger.info("Для полной проверки требуется авторизация.")
        
        await client.disconnect()
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при подключении к Telegram через IPv6: {e}")
        return False

# Тестирование с использованием разных типов прокси
async def test_telegram_with_different_proxy_types():
    """Тестирование Telegram с разными типами прокси"""
    
    proxy_types = ['socks5', 'http', 'mtproto']
    
    for proxy_type in proxy_types:
        logger.info(f"Тестирование подключения к Telegram с прокси типа {proxy_type}...")
        
        try:
            # Настройка прокси
            proxy = {
                'proxy_type': proxy_type,
                'addr': PROXY_SETTINGS['socks5']['server'],
                'port': PROXY_SETTINGS['socks5']['port'],
                'username': PROXY_SETTINGS['socks5']['username'],
                'password': PROXY_SETTINGS['socks5']['password'],
                'rdns': True
            }
            
            # Создание клиента
            client = TelegramClient(
                f'proxy_test_session_{proxy_type}',
                api_id=API_ID,
                api_hash=API_HASH,
                proxy=proxy
            )
            
            logger.info(f"Подключение к Telegram с типом прокси {proxy_type}...")
            await client.connect()
            
            logger.info(f"Подключение с прокси типа {proxy_type} установлено!")
            
            await client.disconnect()
            logger.info(f"Тест с прокси типа {proxy_type} успешно завершен")
            
        except Exception as e:
            logger.error(f"Ошибка при подключении к Telegram с прокси типа {proxy_type}: {e}")

async def run_tests():
    """Запуск всех тестов"""
    logger.info("Начало тестирования прокси...")
    
    # Тест 1: Проверка через requests
    test_requests_with_proxy()
    
    # Тест 2: Проверка Telegram API с IPv4
    await test_telegram()
    
    # Тест 3: Проверка Telegram API с IPv6
    await test_telegram_ipv6()
    
    # Тест 4: Проверка разных типов прокси
    await test_telegram_with_different_proxy_types()
    
    logger.info("Все тесты завершены!")

if __name__ == "__main__":
    # Запускаем асинхронный код
    asyncio.run(run_tests())
