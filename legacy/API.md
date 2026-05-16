# API Documentation

> Документация REST API AIgent Platform | Версия 2.0

## Базовый URL

```
Development: http://localhost:8000
Production:  https://api.aigent.com
```

## Аутентификация

API использует JWT Bearer токены. Включайте токен в заголовок запроса:

```http
Authorization: Bearer <your_jwt_token>
```

## Content-Type

Все запросы/ответы в формате JSON:

```http
Content-Type: application/json
```

---

## Health Check

### GET /health

Проверка статуса сервиса.

**Запрос:**
```bash
curl http://localhost:8000/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "telegram_bot": "running",
  "database": "connected"
}
```

**Статус коды:**
- `200 OK` - Сервис работает нормально

---

## Аутентификация

### POST /api/auth/register

Регистрация нового пользователя.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

**Параметры:**
| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| email | string | ✅ | Email пользователя (уникальный) |
| password | string | ✅ | Пароль (мин. 8 символов) |
| full_name | string | ❌ | Полное имя |

**Ответ (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true
  }
}
```

**Ошибки:**
- `400 Bad Request` - Email уже зарегистрирован
- `422 Validation Error` - Невалидные данные

---

### POST /api/auth/login

Вход в систему.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Параметры:**
| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| email | string | ✅ | Email пользователя |
| password | string | ✅ | Пароль |

**Ответ (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true
  }
}
```

**Ошибки:**
- `401 Unauthorized` - Неверный email или пароль

---

### POST /api/auth/telegram

Аутентификация через Telegram.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/auth/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "telegram_username": "johndoe",
    "auth_data": "..."
  }'
```

**Ответ (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": null,
    "telegram_id": "123456789",
    "is_active": true
  }
}
```

---

## Агенты

### GET /api/agents

Получить список агентов текущего пользователя.

**Запрос:**
```bash
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer <token>"
```

**Параметры запроса:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| skip | int | Количество пропускаемых записей (пагинация) |
| limit | int | Максимальное количество записей (default: 100) |

**Ответ (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Помощник по коду",
      "description": "AI агент для помощи в программировании",
      "system_prompt": "Ты опытный программист...",
      "model": "openrouter/free",
      "is_active": true,
      "created_at": "2026-03-07T10:00:00Z",
      "skills": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440002",
          "name": "code_review",
          "description": "Ревью кода"
        }
      ],
      "tools": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440003",
          "name": "web_search",
          "description": "Поиск в интернете"
        }
      ]
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

---

### POST /api/agents

Создать нового агента.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/agents \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Мой Агент",
    "description": "Описание агента",
    "system_prompt": "Ты полезный ассистент...",
    "model": "openrouter/free",
    "skill_ids": ["550e8400-e29b-41d4-a716-446655440002"],
    "tool_ids": ["550e8400-e29b-41d4-a716-446655440003"]
  }'
```

**Параметры:**
| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| name | string | ✅ | Название агента (3-100 символов) |
| description | string | ❌ | Описание агента |
| system_prompt | string | ❌ | Системный промпт |
| model | string | ❌ | Модель LLM (default: openrouter/free) |
| skill_ids | array | ❌ | Список ID навыков |
| tool_ids | array | ❌ | Список ID инструментов |
| is_active | boolean | ❌ | Активен ли агент (default: true) |

**Ответ (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "name": "Мой Агент",
  "description": "Описание агента",
  "system_prompt": "Ты полезный ассистент...",
  "model": "openrouter/free",
  "is_active": true,
  "created_at": "2026-03-07T10:00:00Z",
  "updated_at": "2026-03-07T10:00:00Z",
  "skills": [],
  "tools": []
}
```

**Ошибки:**
- `422 Validation Error` - Невалидные данные

---

### GET /api/agents/{agent_id}

Получить детали агента.

**Запрос:**
```bash
curl http://localhost:8000/api/agents/550e8400-e29b-41d4-a716-446655440004 \
  -H "Authorization: Bearer <token>"
```

**Ответ (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "name": "Мой Агент",
  "description": "Описание агента",
  "system_prompt": "Ты полезный ассистент...",
  "model": "openrouter/free",
  "is_active": true,
  "created_at": "2026-03-07T10:00:00Z",
  "updated_at": "2026-03-07T10:00:00Z",
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "skills": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "code_review",
      "description": "Ревью кода",
      "prompt_template": "Проанализируй код...",
      "config": {"language": "python"}
    }
  ],
  "tools": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "web_search",
      "description": "Поиск в интернете",
      "type": "http",
      "config": {"endpoint": "https://api.search.com"}
    }
  ]
}
```

**Ошибки:**
- `404 Not Found` - Агент не найден
- `403 Forbidden` - Нет доступа к агенту

---

### PUT /api/agents/{agent_id}

Обновить агента.

**Запрос:**
```bash
curl -X PUT http://localhost:8000/api/agents/550e8400-e29b-41d4-a716-446655440004 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Обновленное название",
    "system_prompt": "Новый системный промпт...",
    "skill_ids": ["550e8400-e29b-41d4-a716-446655440002", "550e8400-e29b-41d4-a716-446655440005"]
  }'
```

**Параметры:**
Все поля опциональны. Передаются только изменяемые поля.

**Ответ (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "name": "Обновленное название",
  "description": "Описание агента",
  "system_prompt": "Новый системный промпт...",
  "model": "openrouter/free",
  "is_active": true,
  "updated_at": "2026-03-07T11:00:00Z"
}
```

---

### DELETE /api/agents/{agent_id}

Удалить агента.

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/api/agents/550e8400-e29b-41d4-a716-446655440004 \
  -H "Authorization: Bearer <token>"
```

**Ответ (204 No Content):**
Пустой ответ.

**Ошибки:**
- `404 Not Found` - Агент не найден

---

## Навыки (Skills)

### GET /api/skills

Получить список навыков.

**Запрос:**
```bash
curl http://localhost:8000/api/skills \
  -H "Authorization: Bearer <token>"
```

**Ответ (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "code_review",
      "display_name": "Ревью кода",
      "description": "Анализирует код и дает рекомендации",
      "category": "development",
      "prompt_template": "Проанализируй следующий код:\n\n```{{language}}\n{{code}}\n```",
      "parameters": {
        "language": {
          "type": "string",
          "description": "Язык программирования",
          "required": true
        },
        "code": {
          "type": "string", 
          "description": "Код для анализа",
          "required": true
        }
      },
      "is_builtin": true,
      "created_at": "2026-03-07T10:00:00Z"
    }
  ]
}
```

---

### POST /api/skills

Создать кастомный навык.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/skills \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_skill",
    "display_name": "Мой навык",
    "description": "Описание навыка",
    "category": "custom",
    "prompt_template": "Шаблон с {{variable}}",
    "parameters": {
      "variable": {
        "type": "string",
        "description": "Описание переменной",
        "required": true
      }
    }
  }'
```

**Ответ (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440006",
  "name": "custom_skill",
  "display_name": "Мой навык",
  "description": "Описание навыка",
  "category": "custom",
  "prompt_template": "Шаблон с {{variable}}",
  "parameters": {...},
  "is_builtin": false,
  "created_at": "2026-03-07T10:00:00Z"
}
```

---

### GET /api/skills/{skill_id}

Получить детали навыка.

**Запрос:**
```bash
curl http://localhost:8000/api/skills/550e8400-e29b-41d4-a716-446655440002 \
  -H "Authorization: Bearer <token>"
```

---

### PUT /api/skills/{skill_id}

Обновить навык (только кастомные).

**Запрос:**
```bash
curl -X PUT http://localhost:8000/api/skills/550e8400-e29b-41d4-a716-446655440006 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Новое название",
    "prompt_template": "Новый шаблон"
  }'
```

**Ошибки:**
- `403 Forbidden` - Нельзя редактировать встроенные навыки

---

### DELETE /api/skills/{skill_id}

Удалить навык (только кастомные).

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/api/skills/550e8400-e29b-41d4-a716-446655440006 \
  -H "Authorization: Bearer <token>"
```

---

## Инструменты (Tools)

### GET /api/tools

Получить список инструментов.

**Запрос:**
```bash
curl http://localhost:8000/api/tools \
  -H "Authorization: Bearer <token>"
```

**Ответ (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "web_search",
      "display_name": "Поиск в интернете",
      "description": "Выполняет поиск в интернете",
      "type": "http",
      "config": {
        "endpoint": "https://api.search.com/search",
        "method": "GET",
        "headers": {"Authorization": "Bearer {{api_key}}"}
      },
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "Поисковый запрос"}
        },
        "required": ["query"]
      },
      "is_builtin": true
    }
  ]
}
```

---

### POST /api/tools

Создать кастомный инструмент.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/tools \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_api",
    "display_name": "Мой API",
    "description": "Вызов моего API",
    "type": "http",
    "config": {
      "endpoint": "https://myapi.com/call",
      "method": "POST",
      "headers": {"Content-Type": "application/json"}
    },
    "input_schema": {
      "type": "object",
      "properties": {
        "data": {"type": "string"}
      },
      "required": ["data"]
    }
  }'
```

**Типы инструментов:**
- `http` - HTTP API вызовы
- `python` - Python скрипты (в разработке)

---

### GET /api/tools/{tool_id}

Получить детали инструмента.

---

### PUT /api/tools/{tool_id}

Обновить инструмент (только кастомные).

---

### DELETE /api/tools/{tool_id}

Удалить инструмент (только кастомные).

---

## Чат

### POST /api/chat

Отправить сообщение агенту.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440004",
    "message": "Привет! Как дела?",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440007",
    "context": {
      "user_name": "John",
      "preferences": {"language": "ru"}
    }
  }'
```

**Параметры:**
| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| agent_id | UUID | ✅ | ID агента |
| message | string | ✅ | Сообщение пользователя |
| conversation_id | UUID | ❌ | ID существующей беседы (создается новая если не указан) |
| context | object | ❌ | Дополнительный контекст |

**Ответ (200 OK):**
```json
{
  "message": {
    "id": "550e8400-e29b-41d4-a716-446655440008",
    "role": "assistant",
    "content": "Привет! У меня все отлично, спасибо! Чем могу помочь?",
    "created_at": "2026-03-07T10:05:00Z"
  },
  "conversation_id": "550e8400-e29b-41d4-a716-446655440007",
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 20,
    "total_tokens": 70
  }
}
```

**Особенности:**
- Автоматическое применение навыков агента
- Выполнение инструментов при необходимости
- Сохранение истории в базе данных

---

### GET /api/chat/history

Получить историю сообщений.

**Запрос:**
```bash
curl "http://localhost:8000/api/chat/history?conversation_id=550e8400-e29b-41d4-a716-446655440007" \
  -H "Authorization: Bearer <token>"
```

**Параметры запроса:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| conversation_id | UUID | ID беседы |
| limit | int | Количество сообщений (default: 50) |
| before | datetime | Сообщения до этой даты |

**Ответ (200 OK):**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440007",
  "messages": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440009",
      "role": "user",
      "content": "Привет!",
      "created_at": "2026-03-07T10:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "role": "assistant",
      "content": "Привет! Чем могу помочь?",
      "created_at": "2026-03-07T10:00:05Z",
      "tool_calls": [
        {
          "id": "call_123",
          "tool_name": "web_search",
          "input": {"query": "приветствие"},
          "output": "..."
        }
      ]
    }
  ],
  "has_more": false
}
```

---

## Конверсации (Conversations)

### GET /api/conversations

Получить список бесед.

**Запрос:**
```bash
curl http://localhost:8000/api/conversations \
  -H "Authorization: Bearer <token>"
```

**Ответ (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440007",
      "agent_id": "550e8400-e29b-41d4-a716-446655440004",
      "agent_name": "Мой Агент",
      "title": "Обсуждение проекта",
      "last_message_at": "2026-03-07T10:05:00Z",
      "message_count": 15
    }
  ]
}
```

---

### DELETE /api/conversations/{conversation_id}

Удалить беседу.

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/api/conversations/550e8400-e29b-41d4-a716-446655440007 \
  -H "Authorization: Bearer <token>"
```

---

## Планировщик задач (Scheduler)

Модуль для создания и управления запланированными задачами.

### POST /api/scheduler/tasks

Создать новую запланированную задачу.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/scheduler/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Утреннее приветствие",
    "description": "Отправляет доброе утро каждый день",
    "action_type": "telegram_message",
    "schedule_type": "daily",
    "scheduled_at": "2026-03-08T08:00:00",
    "message_text": "Доброе утро! ☀️ Начнем продуктивный день!",
    "target_id": "123456789",
    "target_type": "telegram"
  }'
```

**Параметры:**
| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| name | string | ✅ | Название задачи |
| description | string | ❌ | Описание задачи |
| action_type | string | ✅ | Тип действия: telegram_message, webhook, agent_action |
| schedule_type | string | ✅ | Тип расписания: once, hourly, daily, weekly, monthly |
| scheduled_at | datetime | ❌ | Время выполнения (для one-time задач) |
| cron_expression | string | ❌ | Cron выражение |
| interval_minutes | int | ❌ | Интервал в минутах |
| message_text | string | ❌ | Текст сообщения |
| action_payload | string | ❌ | JSON с дополнительными данными |
| target_id | string | ❌ | ID цели (например, chat_id) |
| target_type | string | ❌ | Тип цели: telegram, email, webhook |
| agent_id | string | ❌ | ID агента (для agent_action) |
| max_runs | int | ❌ | Максимальное количество выполнений |

**Ответ (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440100",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Утреннее приветствие",
  "description": "Отправляет доброе утро каждый день",
  "action_type": "telegram_message",
  "schedule_type": "daily",
  "scheduled_at": "2026-03-08T08:00:00",
  "next_run_at": "2026-03-08T08:00:00",
  "message_text": "Доброе утро! ☀️ Начнем продуктивный день!",
  "target_id": "123456789",
  "target_type": "telegram",
  "is_active": true,
  "is_completed": false,
  "run_count": 0,
  "created_at": "2026-03-07T10:00:00Z"
}
```

---

### GET /api/scheduler/tasks

Получить список задач пользователя.

**Запрос:**
```bash
curl "http://localhost:8000/api/scheduler/tasks?active_only=true" \
  -H "Authorization: Bearer <token>"
```

**Параметры запроса:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| active_only | bool | Показывать только активные задачи |

**Ответ (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440100",
      "name": "Утреннее приветствие",
      "action_type": "telegram_message",
      "schedule_type": "daily",
      "next_run_at": "2026-03-08T08:00:00",
      "is_active": true
    }
  ],
  "total": 1
}
```

---

### GET /api/scheduler/tasks/{task_id}

Получить детали задачи.

**Запрос:**
```bash
curl http://localhost:8000/api/scheduler/tasks/550e8400-e29b-41d4-a716-446655440100 \
  -H "Authorization: Bearer <token>"
```

---

### PUT /api/scheduler/tasks/{task_id}

Обновить задачу.

**Запрос:**
```bash
curl -X PUT http://localhost:8000/api/scheduler/tasks/550e8400-e29b-41d4-a716-446655440100 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false,
    "message_text": "Обновленный текст"
  }'
```

---

### DELETE /api/scheduler/tasks/{task_id}

Удалить задачу.

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/api/scheduler/tasks/550e8400-e29b-41d4-a716-446655440100 \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/scheduler/tasks/{task_id}/pause

Приостановить задачу.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/scheduler/tasks/550e8400-e29b-41d4-a716-446655440100/pause \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/scheduler/tasks/{task_id}/resume

Возобновить задачу.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/scheduler/tasks/550e8400-e29b-41d4-a716-446655440100/resume \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/scheduler/tasks/{task_id}/execute

Выполнить задачу немедленно.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/scheduler/tasks/550e8400-e29b-41d4-a716-446655440100/execute \
  -H "Authorization: Bearer <token>"
```

**Ответ (200 OK):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440100",
  "success": true,
  "message": "Message sent successfully",
  "executed_at": "2026-03-07T10:30:00Z"
}
```

---

### POST /api/scheduler/parse

Парсинг естественного языка для создания расписания.

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/scheduler/parse \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "завтра в 3 утра",
    "timezone": "Europe/Moscow"
  }'
```

**Ответ (200 OK):**
```json
{
  "success": true,
  "scheduled_at": "2026-03-08T03:00:00",
  "schedule_type": "once",
  "description": "Завтра в 03:00"
}
```

---

## Модели данных

### User
```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string | null",
  "telegram_id": "string | null",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Agent
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string | null",
  "system_prompt": "string | null",
  "model": "string",
  "owner_id": "uuid",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime",
  "skills": ["Skill[]"],
  "tools": ["Tool[]"]
}
```

### Skill
```json
{
  "id": "uuid",
  "name": "string",
  "display_name": "string",
  "description": "string",
  "category": "string",
  "prompt_template": "string",
  "parameters": "object",
  "is_builtin": "boolean",
  "created_at": "datetime"
}
```

### Tool
```json
{
  "id": "uuid",
  "name": "string",
  "display_name": "string",
  "description": "string",
  "type": "'http' | 'python'",
  "config": "object",
  "input_schema": "object",
  "is_builtin": "boolean",
  "created_at": "datetime"
}
```

### Message
```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "role": "'user' | 'assistant' | 'system'",
  "content": "string",
  "tool_calls": ["ToolCall[]"],
  "created_at": "datetime"
}
```

### ScheduledTask
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "agent_id": "uuid | null",
  "name": "string",
  "description": "string | null",
  "action_type": "'telegram_message' | 'email' | 'webhook' | 'agent_action'",
  "schedule_type": "'once' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'cron'",
  "scheduled_at": "datetime | null",
  "cron_expression": "string | null",
  "interval_minutes": "integer | null",
  "last_run_at": "datetime | null",
  "next_run_at": "datetime | null",
  "message_text": "string | null",
  "action_payload": "string | null",
  "target_id": "string | null",
  "target_type": "'telegram' | 'email' | 'webhook'",
  "is_active": "boolean",
  "is_completed": "boolean",
  "run_count": "integer",
  "max_runs": "integer | null",
  "created_at": "datetime",
  "updated_at": "datetime | null"
}
```

---

## Обработка ошибок

### Формат ошибки
```json
{
  "detail": "Описание ошибки",
  "code": "ERROR_CODE",
  "field": "field_name" // для validation errors
}
```

### HTTP статус коды
| Код | Описание |
|-----|----------|
| 200 OK | Успешный запрос |
| 201 Created | Ресурс создан |
| 204 No Content | Успешно, без контента |
| 400 Bad Request | Невалидный запрос |
| 401 Unauthorized | Требуется аутентификация |
| 403 Forbidden | Нет доступа |
| 404 Not Found | Ресурс не найден |
| 422 Validation Error | Ошибка валидации данных |
| 500 Internal Server Error | Внутренняя ошибка сервера |

### Примеры ошибок

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden:**
```json
{
  "detail": "Not enough permissions"
}
```

**404 Not Found:**
```json
{
  "detail": "Agent not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

API имеет ограничения на количество запросов:

- **Аутентифицированные**: 1000 запросов/час
- **Неаутентифицированные**: 60 запросов/час

Заголовки ответа:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1646640000
```

---

## Версионирование

API версионируется через URL:

```
/api/v1/agents      # Версия 1 (текущая)
/api/v2/agents      # Версия 2 (будущая)
```

Текущая версия работает без префикса v1.

---

## WebSocket (в разработке)

Для real-time чата будет доступен WebSocket endpoint:

```
ws://localhost:8000/ws/chat/{conversation_id}
```

**Сообщения:**
```json
// Отправка
{
  "type": "message",
  "content": "Привет!"
}

// Получение
{
  "type": "response",
  "content": "Привет! Чем могу помочь?",
  "done": true
}
```

---

## SDK и клиенты

### Python
```python
from aigent import Client

client = Client(api_key="your_token")
agents = client.agents.list()
response = client.chat.send(
    agent_id="...",
    message="Привет!"
)
```

### JavaScript/TypeScript
```typescript
import { AIgentClient } from '@aigent/sdk';

const client = new AIgentClient({ token: 'your_token' });
const agents = await client.agents.list();
const response = await client.chat.send({
  agent_id: '...',
  message: 'Привет!'
});
```

---

## Changelog

### v2.1 (2026-03-07)
- ✅ Добавлен модуль планировщика задач (Scheduler)
- ✅ API для управления запланированными задачами
- ✅ Интеграция с Telegram для отправки напоминаний
- ✅ Поддержка различных типов расписаний (once, hourly, daily, weekly, monthly)
- ✅ Парсинг естественного языка для создания расписаний

### v2.0 (2026-03-07)
- ✅ Добавлен Telegram Bot API
- ✅ Улучшена система аутентификации
- ✅ Добавлена пагинация для списков
- ✅ Улучшена документация ошибок

### v1.0 (2026-02-01)
- 🎉 Первый релиз
- ✅ CRUD для агентов
- ✅ CRUD для навыков
- ✅ CRUD для инструментов
- ✅ Базовый чат
