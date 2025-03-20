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
[Будет добавлено после разработки]

## Ограничения и предупреждения
- Использование должно соответствовать условиям использования Telegram
- Массовая автоматизация может привести к блокировке аккаунтов
- Рекомендуется использовать задержки между операциями

## Дорожная карта
- [x] Начальное планирование проекта
- [ ] Поиск и интеграция подходящей библиотеки для работы с Telegram API
- [ ] Реализация проверки контактов по номеру телефона
- [ ] Механизм публикации сторис
- [ ] Добавление упоминаний в сторис
- [ ] Интеграция прокси
- [ ] Масштабирование до 50 аккаунтов
- [ ] Интеграция с AMO CRM
