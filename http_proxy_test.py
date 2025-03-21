#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование HTTP прокси
"""
import requests
import logging
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Прокси данные
PROXY_HOST = '217.29.63.40'
PROXY_PORT = '13918'
PROXY_USER = '4XEYdx'
PROXY_PASS = 'b6em48'

def test_http_proxy():
    """Проверка HTTP прокси через библиотеку requests"""
    logger.info(f"Тестирование HTTP прокси {PROXY_HOST}:{PROXY_PORT}...")
    
    # Настройка прокси с аутентификацией
    proxy_url = f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    try:
        # Пробуем получить наш внешний IP
        start_time = time.time()
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            logger.info(f"HTTP прокси работает! Статус: {response.status_code}")
            logger.info(f"Ваш внешний IP: {response.json()['origin']}")
            logger.info(f"Время ответа: {end_time - start_time:.2f} секунд")
            return True
        else:
            logger.error(f"HTTP прокси вернул неожиданный статус: {response.status_code}")
            logger.error(f"Ответ: {response.text}")
            return False
    
    except requests.exceptions.ProxyError as e:
        logger.error(f"Ошибка при использовании HTTP прокси: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при тестировании HTTP прокси: {e}")
        return False

def test_different_formats():
    """Проверяем разные форматы прокси"""
    
    # Формат 1: Basic auth через ссылку
    proxies1 = {
        'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
        'https': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
    }
    
    # Формат 2: Прокси без аутентификации
    proxies2 = {
        'http': f'http://{PROXY_HOST}:{PROXY_PORT}',
        'https': f'http://{PROXY_HOST}:{PROXY_PORT}'
    }
    
    # Формат 3: Прокси с auth параметром
    proxies3 = {
        'http': f'http://{PROXY_HOST}:{PROXY_PORT}',
        'https': f'http://{PROXY_HOST}:{PROXY_PORT}'
    }
    auth = requests.auth.HTTPProxyAuth(PROXY_USER, PROXY_PASS)
    
    # Тестирование каждого формата
    for i, proxies in enumerate([proxies1, proxies2], 1):
        logger.info(f"Тестирование формата {i}...")
        
        try:
            if i == 3:
                response = requests.get('http://httpbin.org/ip', proxies=proxies3, auth=auth, timeout=10)
            else:
                response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
                
            if response.status_code == 200:
                logger.info(f"Формат {i} работает! IP: {response.json()['origin']}")
            else:
                logger.error(f"Формат {i} вернул статус {response.status_code}: {response.text}")
        
        except Exception as e:
            logger.error(f"Ошибка при тестировании формата {i}: {e}")

if __name__ == "__main__":
    logger.info("Запуск тестов HTTP прокси...")
    
    # Тест 1: Стандартный HTTP прокси
    test_http_proxy()
    
    # Тест 2: Проверка разных форматов
    test_different_formats()
    
    logger.info("Тестирование завершено!")
