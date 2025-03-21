import logging
import os
import random
import asyncio
from telethon.tl.types import InputUser
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon import functions, types
import time
from pathlib import Path

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
    
    def _get_random_story_file(self):
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
                logger.warning("Не указаны пользователи для упоминания в сторис")
                return False
            
            # Ограничиваем количество упоминаний
            users_batch = users_to_mention[:MAX_MENTIONS_PER_STORY]
            logger.info(f"Подготовка публикации сторис с {len(users_batch)} упоминаниями")
            
            # Получаем файл сторис
            if not story_file:
                story_file = self._get_random_story_file()
                if not story_file:
                    return False
            
            # Проверяем, что файл существует
            if not os.path.exists(story_file):
                logger.error(f"Файл сторис {story_file} не найден")
                return False
            
            # Определяем тип файла (фото или видео)
            file_ext = os.path.splitext(story_file)[1].lower()
            is_video = file_ext in ['.mp4', '.avi', '.mov']
            
            # Загружаем файл
            uploaded_file = await self.client.upload_file(story_file)
            
            # Формируем список пользователей для упоминания
            mentioned_users = []
            for user_data in users_batch:
                user = await self._get_user_by_id(user_data['user_id'])
                if user:
                    mentioned_users.append(user)
            
            # Формируем caption с упоминаниями
            caption = "Тестирую авто упоминание в сторис! Если интересно то напиши свой ник телеграм в коментарий под постом https://t.me/c/2229955923/339 "
            entities = []
            
            offset = len(caption)
            for i, user in enumerate(mentioned_users):
                display_name = user.username if user.username else f"{user.first_name or ''} {user.last_name or ''}".strip()
                mention_text = f"@{user.username} " if user.username else f"{display_name} "
                
                caption += mention_text
                
                # Добавляем entity только если есть username
                if user.username:
                    entities.append(types.MessageEntityMention(
                        offset=offset,
                        length=len(mention_text.strip())
                    ))
                
                offset += len(mention_text)
            
            # Подготавливаем медиа в зависимости от типа файла
            if is_video:
                media = types.InputMediaUploadedVideo(
                    file=uploaded_file,
                    ttl_seconds=60*60*24,  # 24 часа
                    spoiler=False,
                    supports_streaming=True,
                    nosound=False
                )
            else:
                media = types.InputMediaUploadedPhoto(
                    file=uploaded_file,
                    ttl_seconds=60*60*24,  # 24 часа
                    spoiler=False
                )
            
            # Настройки приватности - видно всем
            privacy_rules = [types.InputPrivacyValueAllowAll()]
            
            # Публикуем сторис с помощью метода stories.SendStoryRequest
            result = await self.client(functions.stories.SendStoryRequest(
                peer=types.InputPeerSelf(),  # Публикуем от своего имени
                media=media,
                privacy_rules=privacy_rules,
                caption=caption,
                entities=entities,
                period=24  # Период в часах
            ))
            
            logger.info(f"Сторис опубликована успешно")
            logger.info(f"Подпись: {caption}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при публикации сторис: {e}")
            return False
    
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
                
                story_file = self._get_random_story_file()
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
