# Scheduler Module Documentation

> Модуль планировщика задач для AIgent Platform

## Обзор

Модуль планировщика позволяет пользователям создавать запланированные задачи, которые выполняются автоматически в указанное время. Например, отправка напоминаний в Telegram, выполнение периодических действий агентов и т.д.

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     Scheduler Module                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               API Layer (router.py)                  │  │
│  │  • POST   /api/scheduler/tasks                       │  │
│  │  • GET    /api/scheduler/tasks                       │  │
│  │  • GET    /api/scheduler/tasks/{id}                  │  │
│  │  • PUT    /api/scheduler/tasks/{id}                  │  │
│  │  • DELETE /api/scheduler/tasks/{id}                  │  │
│  │  • POST   /api/scheduler/tasks/{id}/pause            │  │
│  │  • POST   /api/scheduler/tasks/{id}/resume           │  │
│  │  • POST   /api/scheduler/tasks/{id}/execute          │  │
│  │  • POST   /api/scheduler/parse                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│                            ▼                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Service Layer (service.py)              │  │
│  │  • SchedulerService - главный сервис                │  │
│  │  • Background task для проверки задач               │  │
│  │  • Выполнение задач в указанное время               │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│                            ▼                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Layer (models.py)                  │  │
│  │  • ScheduledTask - модель задачи                    │  │
│  │  • Хранение в SQLite/PostgreSQL                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│                            ▼                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           External Services                          │  │
│  │  • Telegram Bot (отправка сообщений)                │  │
│  │  • Webhook API (внешние вызовы)                     │  │
│  │  • Agent Runtime (действия агентов)                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Типы задач

### 1. Telegram Message (`telegram_message`)
Отправка сообщений в Telegram по расписанию.

**Примеры использования:**
- Утренние приветствия
- Напоминания о встречах
- Ежедневные отчеты

**Параметры:**
- `target_id` - ID чата Telegram
- `message_text` - Текст сообщения

### 2. Webhook (`webhook`)
Вызов внешних HTTP endpoints.

**Примеры использования:**
- Обновление данных в external systems
- Отправка уведомлений на сторонние сервисы

**Параметры:**
- `action_payload` - JSON с URL, method, headers, data

### 3. Agent Action (`agent_action`)
Выполнение действий через AI агента.

**Примеры использования:**
- Генерация ежедневных отчетов
- Анализ данных по расписанию

## Типы расписаний

### `once` - Одноразовая задача
Выполняется один раз в указанное время.

```json
{
  "schedule_type": "once",
  "scheduled_at": "2026-03-08T08:00:00"
}
```

### `hourly` - Ежечасно
Выполняется каждый час.

```json
{
  "schedule_type": "hourly"
}
```

### `daily` - Ежедневно
Выполняется каждый день в то же время.

```json
{
  "schedule_type": "daily"
}
```

### `weekly` - Еженедельно
Выполняется каждую неделю.

```json
{
  "schedule_type": "weekly"
}
```

### `monthly` - Ежемесячно
Выполняется каждый месяц.

```json
{
  "schedule_type": "monthly"
}
```

### Custom Interval
Выполняется с произвольным интервалом в минутах.

```json
{
  "schedule_type": "once",
  "interval_minutes": 30
}
```

## API Endpoints

### Создание задачи
```http
POST /api/scheduler/tasks
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Утреннее приветствие",
  "description": "Отправляет доброе утро каждый день",
  "action_type": "telegram_message",
  "schedule_type": "daily",
  "scheduled_at": "2026-03-08T08:00:00",
  "message_text": "Доброе утро! ☀️ Начнем продуктивный день!",
  "target_id": "123456789",
  "target_type": "telegram"
}
```

### Список задач
```http
GET /api/scheduler/tasks
Authorization: Bearer <token>
```

### Получить задачу
```http
GET /api/scheduler/tasks/{task_id}
Authorization: Bearer <token>
```

### Обновить задачу
```http
PUT /api/scheduler/tasks/{task_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "is_active": false
}
```

### Удалить задачу
```http
DELETE /api/scheduler/tasks/{task_id}
Authorization: Bearer <token>
```

### Приостановить задачу
```http
POST /api/scheduler/tasks/{task_id}/pause
Authorization: Bearer <token>
```

### Возобновить задачу
```http
POST /api/scheduler/tasks/{task_id}/resume
Authorization: Bearer <token>
```

### Выполнить задачу сейчас
```http
POST /api/scheduler/tasks/{task_id}/execute
Authorization: Bearer <token>
```

### Парсинг естественного языка
```http
POST /api/scheduler/parse
Content-Type: application/json
Authorization: Bearer <token>

{
  "text": "завтра в 3 утра",
  "timezone": "Europe/Moscow"
}

Response:
{
  "success": true,
  "scheduled_at": "2026-03-08T03:00:00",
  "schedule_type": "once",
  "description": "Завтра в 03:00"
}
```

## Примеры использования

### Пример 1: Утреннее напоминание
```bash
curl -X POST http://localhost:8000/api/scheduler/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Доброе утро",
    "description": "Приветствие каждое утро",
    "action_type": "telegram_message",
    "schedule_type": "daily",
    "scheduled_at": "2026-03-08T08:00:00",
    "message_text": "Доброе утро! 🌅 Не забудь выпить кофе!",
    "target_id": "123456789",
    "target_type": "telegram"
  }'
```

### Пример 2: Напоминание через 30 минут
```bash
curl -X POST http://localhost:8000/api/scheduler/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Напоминание о встрече",
    "action_type": "telegram_message",
    "schedule_type": "once",
    "scheduled_at": "2026-03-07T15:30:00",
    "message_text": "Через 30 минут начинается встреча!",
    "target_id": "123456789"
  }'
```

### Пример 3: Еженедельный отчет
```bash
curl -X POST http://localhost:8000/api/scheduler/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Еженедельный отчет",
    "action_type": "agent_action",
    "schedule_type": "weekly",
    "message_text": "Сгенерируй отчет за неделю",
    "agent_id": "<agent-id>"
  }'
```

## Интеграция с Telegram ботом

Планировщик интегрирован с Telegram ботом и может отправлять сообщения от имени бота.

### Как это работает:
1. Пользователь создает задачу с `action_type: telegram_message`
2. Указывает `target_id` (ID чата Telegram)
3. Указывает `message_text` (текст сообщения)
4. В назначенное время планировщик вызывает `telegram_bot.send_message()`
5. Сообщение отправляется пользователю

### Получение chat_id:
1. Пользователь пишет боту в Telegram
2. Отправляет команду `/status`
3. Бот показывает ID чата

## Мониторинг

### Health Check
```http
GET /api/scheduler/health
```

Ответ:
```json
{
  "status": "healthy",
  "is_running": true
}
```

### Логи
Планировщик пишет логи:
- `INFO` - Создание/обновление задач
- `INFO` - Выполнение задач
- `ERROR` - Ошибки выполнения

## Безопасность

1. **Аутентификация** - Все endpoints требуют JWT токен
2. **Авторизация** - Пользователь может управлять только своими задачами
3. **Валидация** - Все входные данные валидируются через Pydantic
4. **Изоляция** - Каждая задача выполняется независимо

## Ограничения

- Минимальный интервал: 1 минута
- Максимальное количество задач на пользователя: 100 (настраивается)
- История выполнения: хранится в полях `run_count`, `last_run_at`
- Точность: ±60 секунд (зависит от `check_interval`)

## Troubleshooting

### Задача не выполнилась
1. Проверьте, что задача активна (`is_active: true`)
2. Проверьте `next_run_at` - должно быть в прошлом
3. Проверьте логи backend на ошибки

### Ошибка отправки в Telegram
1. Проверьте, что `target_id` правильный
2. Проверьте, что пользователь не заблокировал бота
3. Проверьте, что бот имеет право отправлять сообщения

### Задача выполняется с задержкой
- Нормальная задержка до 60 секунд (период проверки)
- Проверьте нагрузку на сервер

## Разработка

### Добавление нового типа действия

1. Добавьте тип в `ActionType` enum (schemas.py)
2. Добавьте обработчик в `_execute_task()` (service.py)
3. Обновите документацию

### Пример:
```python
# schemas.py
class ActionType(str, Enum):
    ...
    NEW_ACTION = "new_action"

# service.py
async def _execute_task(self, task: ScheduledTask):
    ...
    elif task.action_type == ActionType.NEW_ACTION.value:
        await self._execute_new_action(task)
        ...

async def _execute_new_action(self, task: ScheduledTask):
    # Реализация нового действия
    pass
```
