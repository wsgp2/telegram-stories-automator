# Telegram Stories Automator

## Описание проекта
Автоматизированная система для публикации сторис в Telegram с нескольких аккаунтов, с упоминанием контактов.

### Основной функционал:
1. **Мультиаккаунт**: Работа с несколькими Telegram аккаунтами (изначально 2, масштабирование до 50)
2. **Прокси-поддержка**: Каждый аккаунт использует свой прокси
3. **Проверка контактов**: Проверка наличия пользователей в Telegram по номеру телефона
4. **Автоматические упоминания**: Создание упоминаний контактов в сторис
5. **Массовая обработка**: Размещение до 30 упоминаний на одну сторис

### Техническая реализация:
- Импорт контактов из файла (в будущем - из AMO CRM)
- Библиотека для работы с Telegram API
- Обработка видео-файлов для публикации в качестве сторис
- Система очередей для распределения нагрузки при масштабировании

## Требования
- Python 3.8+
- Telegram API ключи для каждого аккаунта
- Список прокси-серверов
- База телефонных номеров для проверки и упоминания

## Техническая реализация
### API для работы с Telegram
Проект использует библиотеку **Telethon**, которая предоставляет доступ к официальному API Telegram, включая функции для работы со сторис:
- Проверка наличия пользователей по номеру телефона через `ImportContactsRequest`
- Публикация сторис через метод `stories.SendStoryRequest`
- Упоминание пользователей в сторис с помощью `MessageEntityMention`

### Ограничения API
- Для работы со сторис требуются полные права доступа к аккаунту (не бот-токен)
- Согласно политике Telegram, массовая автоматизация может привести к блокировке аккаунтов
- Упомянуть в сторис можно только пользователей с публичным username

## Структура проекта
```
TG_stories/
├── configs/            # Конфигурационные файлы
│   ├── accounts.json   # Данные аккаунтов и прокси
│   └── settings.py     # Основные настройки
├── data/               
│   ├── contacts/       # Файлы с контактами
│   └── stories/        # Видео для публикации
├── src/                # Исходный код
│   ├── api/            # Модули для работы с API
│   ├── utils/          # Вспомогательные функции
│   └── main.py         # Основной файл запуска
├── tests/              # Тесты
├── requirements.txt    # Зависимости
└── README.md           # Документация
```

## Установка и использование

### 1. Клонирование репозитория и установка зависимостей

```bash
# Клонировать репозиторий
git clone https://github.com/wsgp2/telegram-stories-automator.git
cd telegram-stories-automator

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка аккаунтов Telegram

1. Создайте приложение Telegram для получения `api_id` и `api_hash`:
   - Перейдите на [my.telegram.org](https://my.telegram.org/)
   - Войдите в свой аккаунт Telegram
   - Выберите "API development tools"
   - Создайте новое приложение, укажите любое имя и описание
   - Скопируйте полученные `api_id` и `api_hash`

2. Настройте файл `configs/accounts.json` по следующему формату:

```json
{
  "accounts": [
    {
      "phone": "+79XXXXXXXXX",
      "api_id": "YOUR_API_ID",
      "api_hash": "YOUR_API_HASH",
      "proxy": {
        "server": "proxy.example.com",
        "port": 1080,
        "username": "user",
        "password": "pass",
        "type": "socks5"
      }
    }
  ]
}
```

**Важно**: 
- Поддерживаемые типы прокси: `socks5`, `socks4`, `http`.
- Прокси является необязательным параметром, но рекомендуется для предотвращения блокировок.
- Убедитесь, что аккаунты имеют премиум статус для работы со сторис.

### 3. Подготовка контактов

1. Создайте CSV файл с контактами в директории `data/contacts/`:

```csv
username,phone
username1,+79XXXXXXXXX
username2,+79XXXXXXXXX
```

2. Также можно использовать только юзернеймы (без `@`):

```csv
username
username1
username2
```

### 4. Подготовка медиафайлов для сторис

Поместите медиафайлы (фото/видео) в директорию `data/stories/`:
- Поддерживаемые форматы для фото: `.jpg`, `.jpeg`, `.png`
- Поддерживаемые форматы для видео: `.mp4`, `.avi`, `.mov`
- Рекомендуемое соотношение сторон: 9:16 (вертикальное)

### 5. Запуск проекта

```bash
# Запуск основного скрипта
python src/main.py
```

При первом запуске для каждого аккаунта потребуется ввести код подтверждения, который придет в Telegram.

## Основные функции и их использование

### 1. Проверка контактов

Проверка существующих пользователей Telegram выполняется классом `ContactChecker`:

```python
from src.utils.contact_checker import ContactChecker

# Пример использования для проверки телефонных номеров
checker = ContactChecker(client)
results = await checker.process_contacts_file('data/contacts/contacts.csv')

# Пример использования для проверки по юзернеймам
users = await checker.check_usernames_from_file('data/contacts/usernames.csv')
```

### 2. Публикация сторис с упоминаниями

Публикация сторис осуществляется классом `StoryPublisher`:

```python
from src.utils.story_publisher import StoryPublisher

# Создание экземпляра класса
publisher = StoryPublisher(client)

# Проверка доступности сторис для аккаунта
is_available = await publisher.check_stories_available()

# Публикация сторис с упоминаниями
users_to_mention = [
    {'user_id': 12345678, 'username': 'username1'},
    {'user_id': 87654321, 'username': 'username2'}
]
success = await publisher.publish_story_with_mentions(users_to_mention)
```

### 3. Тегирование пользователей на изображениях сторис

В версии 1.2 добавлена возможность размещать теги пользователей непосредственно на изображении сторис:

```python
# Пример массива users_to_mention такой же, как и раньше
# Но теперь теги появляются как на изображении, так и в подписи
success = await publisher.publish_story_with_mentions(users_to_mention)
```

**Как это работает:**
1. Пользователи тегируются в виде кликабельных областей прямо на изображении сторис
2. Размещение тегов происходит по вертикали слева
3. Каждый тег содержит имя пользователя и ссылку на его профиль
4. Максимальное количество тегов ограничено параметром `MAX_MENTIONS_PER_STORY` в `configs/settings.py`

**Настройка позиционирования тегов:**
Параметры размещения тегов можно настроить в файле `src/utils/story_publisher.py`:

```python
# Настройки размера и расположения тегов
tag_width = 0.3   # 30% от ширины экрана
tag_height = 0.05 # 5% от высоты экрана
spacing = 0.01    # Промежуток между тегами (1% от высоты)
start_x = 0.05    # Начальная позиция по X (5% от левого края)
start_y = 0.15    # Начальная позиция по Y (15% от верха)
```

## Логирование и отслеживание ошибок

Приложение ведёт логи в консоли и в файле, а также сохраняет историю публикаций в `data/history/publishing_history.json`.

Пример записи в истории публикаций:
```json
{
  "timestamp": "2023-05-20 15:30:45",
  "file": "/path/to/story.jpg",
  "success": true,
  "users_mentioned": [
    {"user_id": 12345678, "username": "username1"}
  ]
}
```

## Ограничения и рекомендации

1. **Интервалы между публикациями**: 
   - Рекомендуется задержка не менее 60 секунд между публикациями сторис с одного аккаунта
   - Параметр можно настроить в `configs/settings.py` (DELAY_BETWEEN_STORIES)

2. **Количество упоминаний**:
   - Максимум 30 упоминаний на одну сторис (MAX_MENTIONS_PER_STORY)
   - При превышении лимита остальные упоминания игнорируются

3. **Прокси и безопасность**:
   - Используйте разные прокси для разных аккаунтов
   - Избегайте слишком частых публикаций с одного аккаунта
   - Рекомендуется использовать аккаунты с премиум статусом

4. **Масштабирование**:
   - При использовании более 10 аккаунтов рекомендуется распределить запуски по времени
   - Подготавливайте разные медиафайлы для разных аккаунтов

## Устранение неполадок

### Проблемы с авторизацией

Если возникают проблемы при входе в аккаунт:
1. Проверьте правильность `api_id` и `api_hash`
2. Убедитесь в правильности формата номера телефона (+79XXXXXXXXX)
3. Удалите файлы сессий в папке `data/sessions/` и попробуйте снова

### Ошибки при публикации сторис

1. **STORY_PERIOD_INVALID**: Приложение автоматически пробует разные значения периода
2. **PREMIUM_ACCOUNT_REQUIRED**: Убедитесь, что аккаунт имеет премиум статус
3. **FLOOD_WAIT_X**: Слишком много запросов, ждите X секунд
4. **MEDIA_INVALID**: Проверьте формат и размер медиафайла

## Автор

**Сергей Дышкант** (SergD)
- Telegram: [@sergei_dyshkant](https://t.me/sergei_dyshkant)

По вопросам разработки и внедрения решений для автоматизации Telegram можно обращаться по указанным контактам.

## Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле LICENSE.
