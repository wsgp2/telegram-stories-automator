#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест для проверки подключения к прокси
"""
import socket
import socks
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Прокси-сервер
PROXY_HOST = '217.29.63.40'
PROXY_PORT = 13918
PROXY_USERNAME = '4XEYdx'
PROXY_PASSWORD = 'b6em48'

# IPv6 адрес
IPV6_HOST = '2a06:c006:a7ff:5e95:0f0d:25bc:4ba6:3bb2'

def test_tcp_connection():
    """Тестирование прямого TCP-подключения к прокси"""
    logger.info(f"Проверка доступности прокси-сервера {PROXY_HOST}:{PROXY_PORT}...")
    
    try:
        # Создаем сокет
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Пытаемся подключиться
        start_time = time.time()
        result = sock.connect_ex((PROXY_HOST, PROXY_PORT))
        end_time = time.time()
        
        if result == 0:
            logger.info(f"Прокси-сервер {PROXY_HOST}:{PROXY_PORT} доступен!")
            logger.info(f"Время отклика: {end_time - start_time:.2f} секунд")
            return True
        else:
            logger.error(f"Не удалось подключиться к прокси-серверу. Код ошибки: {result}")
            return False
    
    except Exception as e:
        logger.error(f"Ошибка при подключении к прокси-серверу: {e}")
        return False
    
    finally:
        sock.close()

def test_socks_handshake():
    """Тестирование SOCKS5-рукопожатия с прокси"""
    logger.info(f"Проверка SOCKS5-рукопожатия с прокси {PROXY_HOST}:{PROXY_PORT}...")
    
    try:
        # Настраиваем SOCKS5-прокси
        s = socks.socksocket()
        s.set_proxy(
            proxy_type=socks.SOCKS5,
            addr=PROXY_HOST,
            port=PROXY_PORT,
            username=PROXY_USERNAME,
            password=PROXY_PASSWORD
        )
        s.settimeout(10)
        
        # Тестовый хост и порт (Google DNS)
        test_host = '8.8.8.8'
        test_port = 53
        
        # Попытка подключения
        start_time = time.time()
        s.connect((test_host, test_port))
        end_time = time.time()
        
        logger.info(f"SOCKS5-рукопожатие успешно! Соединение с {test_host}:{test_port} установлено.")
        logger.info(f"Время подключения: {end_time - start_time:.2f} секунд")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении SOCKS5-рукопожатия: {e}")
        return False
    
    finally:
        s.close()

def test_ipv6_connection():
    """Тестирование подключения к IPv6-адресу прокси"""
    logger.info(f"Проверка доступности IPv6-адреса {IPV6_HOST}:{PROXY_PORT}...")
    
    try:
        # Создаем сокет для IPv6
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Пытаемся подключиться
        start_time = time.time()
        result = sock.connect_ex((IPV6_HOST, PROXY_PORT, 0, 0))
        end_time = time.time()
        
        if result == 0:
            logger.info(f"IPv6-адрес {IPV6_HOST}:{PROXY_PORT} доступен!")
            logger.info(f"Время отклика: {end_time - start_time:.2f} секунд")
            return True
        else:
            logger.error(f"Не удалось подключиться к IPv6-адресу. Код ошибки: {result}")
            return False
    
    except Exception as e:
        logger.error(f"Ошибка при подключении к IPv6-адресу: {e}")
        return False
    
    finally:
        sock.close()

if __name__ == "__main__":
    logger.info("Запуск тестов прокси...")
    
    # Тест 1: Прямое TCP-подключение к прокси
    test_tcp_connection()
    
    # Тест 2: SOCKS5-рукопожатие
    test_socks_handshake()
    
    # Тест 3: Проверка IPv6-адреса
    test_ipv6_connection()
    
    logger.info("Тестирование завершено!")
