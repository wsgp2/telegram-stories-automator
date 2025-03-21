import logging
import os
import random
import asyncio
from telethon.tl.types import InputUser
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon import functions, types
import time
from pathlib import Path
import json
import datetime
from configs.settings import STORIES_DIR, MAX_MENTIONS_PER_STORY, DELAY_BETWEEN_STORIES

logger = logging.getLogger(__name__)

class StoryPublisher:
    """Класс для публикации сторис с упоминаниями пользователей"""
    
    def __init__(self, client_data):
        # Если передан словарь с клиентом, извлекаем объект клиента
        if isinstance(client_data, dict) and 'client' in client_data:
            self.client = client_data['client']
        else:
            # Иначе предполагаем, что передан сам объект клиента
            self.client = client_data
        
        # Файл для хранения истории публикаций
        self.history_file = os.path.join(os.path.dirname(STORIES_DIR), 'history', 'publishing_history.json')
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

    async def _get_random_story_file(self):
        """Получение случайного файла сторис из директории"""
        story_files = [f for f in os.listdir(STORIES_DIR) 
                      if os.path.isfile(os.path.join(STORIES_DIR, f)) 
                      and f.lower().endswith(('.mp4', '.avi', '.mov', '.jpg', '.jpeg', '.png'))]
        
        if not story_files:
            logger.error(f"В директории {STORIES_DIR} не найдены файлы для сторис")
            return None
        
        random_file = random.choice(story_files)
        return os.path.join(STORIES_DIR, random_file)
    
    async def _get_user_by_id(self, user_id):
        """Получение объекта пользователя по ID"""
        try:
            entity = await self.client.get_entity(user_id)
            return entity
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя с ID {user_id}: {e}")
            return None
    
    async def check_stories_available(self):
        """
        Проверяет, доступна ли публикация сторис для текущего аккаунта
        
        Returns:
            bool: True, если публикация сторис доступна
        """
        try:
            # Получаем информацию о текущем пользователе
            me = await self.client.get_me()
            logger.info(f"Текущий пользователь: @{me.username if me.username else me.id}")
            
            # Проверяем разрешения и настройки аккаунта
            full_user = await self.client(functions.users.GetFullUserRequest(
                id=me.id
            ))
            
            # Логируем информацию о возможностях аккаунта
            stripped_info = str(full_user)[:500] + "..." if len(str(full_user)) > 500 else str(full_user)
            logger.info(f"Информация об аккаунте: {stripped_info}")
            
            # Проверяем, есть ли ограничение на публикацию сторис
            if hasattr(full_user.full_user, 'stories_unavailable') and full_user.full_user.stories_unavailable:
                logger.warning("Публикация сторис недоступна для данного аккаунта!")
                return False
                
            # Проверяем аккаунт через флаг premium - часто для сторис нужен премиум статус
            if hasattr(me, 'premium') and not me.premium:
                logger.warning("Аккаунт не имеет премиум статуса, это может ограничивать возможности сторис")
                # Возвращаем True, так как это только предупреждение
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке доступности сторис: {e}")
            return False
    
    async def publish_story_with_mentions(self, users_to_mention, story_file=None):
        """
        Публикация сторис с упоминаниями пользователей
        
        Args:
            users_to_mention (list): Список данных пользователей для упоминания
            story_file (str, optional): Путь к файлу сторис. Если None, берется случайный файл.
        
        Returns:
            bool: Результат публикации
        """
        try:
            if not users_to_mention:
                logger.warning("Нет пользователей для упоминания")
                return False
                
            logger.info(f"Подготовка публикации сторис с {len(users_to_mention)} упоминаниями")
            
            # Проверяем доступность сторис для аккаунта
            if not await self.check_stories_available():
                logger.error("Публикация сторис недоступна для данного аккаунта")
                return False
            
            # Если не указан файл сторис, берем случайный
            if not story_file:
                story_file = await self._get_random_story_file()
                if not story_file:
                    logger.error("Не найдены файлы для сторис")
                    return False
                    
            # Проверяем существование файла
            if not os.path.exists(story_file):
                logger.error(f"Файл {story_file} не найден")
                return False
                
            # Загружаем файл на сервер Telegram
            file = await self.client.upload_file(story_file)
            
            # Создаем объект медиа в зависимости от типа файла
            if story_file.endswith(('.jpg', '.jpeg', '.png')):
                media = types.InputMediaUploadedPhoto(
                    file=file,
                    spoiler=False
                )
            elif story_file.endswith(('.mp4', '.avi', '.mov')):
                media = types.InputMediaUploadedDocument(
                    file=file,
                    mime_type='video/mp4',
                    attributes=[types.DocumentAttributeVideo(
                        duration=15,  # Длительность видео в секундах
                        w=1080,       # Ширина видео
                        h=1920,       # Высота видео
                        supports_streaming=True
                    )]
                )
            else:
                logger.error(f"Неподдерживаемый формат файла: {story_file}")
                return False
                
            # Формируем подпись и упоминания
            caption = "Тестирую авто упоминание в сторис! Если интересно то напиши свой ник телеграм в коментарий под постом https://t.me/c/2229955923/339 "
            entities = []
            offset = len(caption)
            
            # Добавляем упоминания пользователей в подпись
            for i, user_data in enumerate(users_to_mention):
                # Получаем объект InputUser для пользователя
                try:
                    input_user = await self._get_user_by_id(user_data['user_id'])
                    if not input_user:
                        continue
                        
                    # Добавляем упоминание в подпись
                    mention_text = f"@{user_data['username']} "
                    caption += mention_text
                    
                    # Создаем entity для упоминания
                    entities.append(types.MessageEntityMention(
                        offset=offset,
                        length=len(mention_text.strip())
                    ))
                    
                    offset += len(mention_text)
                    
                except Exception as e:
                    logger.error(f"Ошибка при добавлении упоминания пользователя {user_data['username']}: {e}")
                    continue
            
            # Настройки приватности (публично для всех)
            privacy_rules = [types.InputPrivacyValueAllowAll()]
            
            # Публикуем сторис с помощью метода stories.SendStoryRequest
            # Telegram ожидает значение period в секундах (86400 = 24 часа)
            try:
                result = await self.client(functions.stories.SendStoryRequest(
                    peer=types.InputPeerSelf(),  # Публикуем от своего имени
                    media=media,
                    privacy_rules=privacy_rules,
                    caption=caption,
                    entities=entities,
                    period=86400  # 24 часа в секундах
                ))
                
                logger.info(f"Сторис опубликована успешно")
                if caption:
                    logger.info(f"Подпись: {caption}")
                
                # Логируем успешную публикацию
                await self._log_publication(story_file, users_to_mention)
                
                return True
                
            except Exception as e:
                logger.error(f"Ошибка при публикации сторис: {e}")
                
                # Если ошибка связана с периодом, попробуем другие значения
                if "STORY_PERIOD_INVALID" in str(e):
                    # Различные возможные значения для period в секундах
                    periods = [43200, 21600, 172800, 3600]  # 12, 6, 48, 1 час
                    
                    for period in periods:
                        try:
                            result = await self.client(functions.stories.SendStoryRequest(
                                peer=types.InputPeerSelf(),
                                media=media,
                                privacy_rules=privacy_rules,
                                caption=caption,
                                entities=entities,
                                period=period
                            ))
                            
                            logger.info(f"Сторис опубликована успешно с периодом {period} секунд")
                            if caption:
                                logger.info(f"Подпись: {caption}")
                                
                            # Логируем успешную публикацию
                            await self._log_publication(story_file, users_to_mention)
                            
                            return True
                            
                        except Exception as e2:
                            logger.warning(f"Период {period} секунд не работает: {e2}")
                            await asyncio.sleep(1)
                
                # Если ни один период не сработал, возвращаем ошибку
                logger.error(f"Не удалось опубликовать сторис с разными периодами")
                
                # Логируем неудачную публикацию
                await self._log_publication(story_file, users_to_mention, success=False, 
                                            error=f"Не удалось опубликовать сторис: {e}")
                
                return False
                
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при публикации сторис: {e}")
            
            # Логируем неудачную публикацию
            await self._log_publication(story_file, users_to_mention, success=False, 
                                        error=f"Непредвиденная ошибка: {e}")
            
            return False
    
    async def _log_publication(self, story_file, users_mentioned, success=True, error=None):
        """
        Логирует информацию о публикации сторис в историю
        
        Args:
            story_file (str): Путь к файлу сторис
            users_mentioned (list): Список пользователей, упомянутых в сторис
            success (bool): Успешна ли публикация
            error (str, optional): Сообщение об ошибке, если публикация не удалась
        """
        try:
            # Формируем запись для истории
            history_entry = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "story_file": os.path.basename(story_file),
                "users_mentioned": [user.get('username', user.get('user_id', 'Unknown')) for user in users_mentioned],
                "success": success
            }
            
            if error:
                history_entry["error"] = str(error)
                
            # Проверяем существование файла истории
            history = []
            if os.path.exists(self.history_file):
                try:
                    with open(self.history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Ошибка чтения файла истории: {e}")
            
            # Добавляем новую запись
            history.append(history_entry)
            
            # Сохраняем файл истории
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"Информация о публикации сохранена в историю")
            
        except Exception as e:
            logger.error(f"Ошибка при логировании публикации: {e}")
    
    async def batch_publish_stories(self, all_users, stories_per_batch=1, delay=DELAY_BETWEEN_STORIES):
        """
        Пакетная публикация нескольких сторис
        
        Args:
            all_users (list): Список всех пользователей для упоминания
            stories_per_batch (int): Количество сторис в одной пакетной публикации
            delay (int): Задержка между публикациями в секундах
        
        Returns:
            int: Количество успешно опубликованных сторис
        """
        try:
            if not all_users:
                logger.warning("Нет пользователей для упоминания")
                return 0
            
            # Разбиваем пользователей на батчи для упоминания
            user_batches = []
            for i in range(0, len(all_users), MAX_MENTIONS_PER_STORY):
                user_batches.append(all_users[i:i+MAX_MENTIONS_PER_STORY])
            
            # Публикуем сторис
            successful_stories = 0
            for i, batch in enumerate(user_batches):
                if i > 0:
                    logger.info(f"Ожидание {delay} секунд перед следующей публикацией...")
                    await asyncio.sleep(delay)
                
                story_file = await self._get_random_story_file()
                result = await self.publish_story_with_mentions(batch, story_file)
                
                if result:
                    successful_stories += 1
                    logger.info(f"Опубликована сторис {successful_stories}/{len(user_batches)}")
                else:
                    logger.warning(f"Не удалось опубликовать сторис {i+1}/{len(user_batches)}")
            
            return successful_stories
            
        except Exception as e:
            logger.error(f"Ошибка при пакетной публикации сторис: {e}")
            return 0
