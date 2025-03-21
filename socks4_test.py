#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование SOCKS4 прокси
"""
import socket
import socks
import time
import logging
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Прокси данные
PROXY_HOST = '103.167.156.16'
PROXY_PORT = 1080
PROXY_TYPE = socks.SOCKS4  # используем SOCKS4

def test_socks_connection():
    """Тестирование прямого соединения через SOCKS4 прокси"""
    logger.info(f"Тестирование SOCKS4 прокси {PROXY_HOST}:{PROXY_PORT}...")
    
    # Создаем сокет с прокси
    s = socks.socksocket()
    s.set_proxy(PROXY_TYPE, PROXY_HOST, PROXY_PORT)
    s.settimeout(10)
    
    try:
        # Пробуем подключиться к Telegram серверу
        start_time = time.time()
        s.connect(('149.154.167.51', 443))
        end_time = time.time()
        
        logger.info(f"Успешное соединение с сервером Telegram!")
        logger.info(f"Время соединения: {end_time - start_time:.2f} секунд")
        s.close()
        return True
    
    except Exception as e:
        logger.error(f"Ошибка соединения через SOCKS4 прокси: {e}")
        s.close()
        return False

def test_with_requests():
    """Тестирование через библиотеку requests"""
    logger.info("Тестирование через requests...")
    
    # Настраиваем requests на использование SOCKS прокси
    session = requests.Session()
    session.proxies = {
        'http': f'socks4://{PROXY_HOST}:{PROXY_PORT}',
        'https': f'socks4://{PROXY_HOST}:{PROXY_PORT}'
    }
    
    try:
        # Пробуем получить информацию о нашем IP
        response = session.get('https://httpbin.org/ip', timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Успешный запрос через SOCKS4! Статус: {response.status_code}")
            logger.info(f"Ваш внешний IP: {response.json()['origin']}")
            return True
        else:
            logger.error(f"Неожиданный статус: {response.status_code}")
            logger.error(f"Ответ: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Ошибка запроса через SOCKS4 прокси: {e}")
        return False

if __name__ == "__main__":
    logger.info("Запуск тестов SOCKS4 прокси...")
    
    # Тест 1: Прямое соединение
    test_socks_connection()
    
    # Тест 2: Через requests
    test_with_requests()
    
    logger.info("Тестирование завершено!")
