# PostgreSQL Schema Explanation

## Overview

Эта схема базы данных разработана для платформы с одним ИИ-агентом на пользователя. Ключевая концепция - у каждого пользователя есть один агент, который настраивается через навыки (skills) и инструменты (tools).

## Основные принципы

### 1. UUID Primary Keys
Все таблицы используют UUID в качестве первичных ключей для:
- Глобальной уникальности
- Безопасности (невозможно перебрать ID)
- Масштабируемости

### 2. Soft Delete
Все основные таблицы имеют поле `deleted_at` для мягкого удаления:
- Сохранение истории
- Возможность восстановления
- Аналитика удаленных данных

### 3. Индексы для производительности
Созданы индексы для:
- Частых запросов по user_id
- Поиска по имени/slug
- Фильтрации активных записей
- Сортировки по времени

## Детальное описание таблиц

### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);
```

**Назначение:** Основная таблица пользователей
**Ключевые поля:**
- `email`, `username` - уникальные идентификаторы
- `hashed_password` - хешированный пароль
- `deleted_at` - мягкое удаление
- `is_active` - блокировка пользователя

### Agents
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL DEFAULT 'You are a helpful AI assistant.',
    model_name VARCHAR(100) NOT NULL DEFAULT 'gpt-3.5-turbo',
    configuration JSONB NOT NULL DEFAULT '{}',
    ...
);
```

**Назначение:** ИИ-агент пользователя (один на пользователя)
**Ключевые поля:**
- `user_id` - уникальная связь с пользователем
- `system_prompt` - динамический промпт агента
- `model_name` - используемая LLM модель
- `configuration` - JSON с настройками агента

### Skills
```sql
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    system_prompt_template TEXT NOT NULL,
    default_config JSONB NOT NULL DEFAULT '{}',
    is_builtin BOOLEAN DEFAULT FALSE NOT NULL,
    ...
);
```

**Назначение:** Доступные в системе навыки
**Ключевые поля:**
- `name`, `slug` - уникальные идентификаторы навыка
- `system_prompt_template` - шаблон промпта навыка
- `default_config` - конфигурация по умолчанию
- `is_builtin` - встроенный или пользовательский

### User Skills
```sql
CREATE TABLE user_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    config JSONB NOT NULL DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    ...
    UNIQUE(user_id, skill_id)
);
```

**Назначение:** Связь пользователей с навыками
**Ключевые поля:**
- `user_id`, `skill_id` - уникальная пара
- `config` - персонализированная конфигурация
- `is_enabled` - включен ли навык

### Tools
```sql
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    function_schema JSONB NOT NULL,
    default_config JSONB NOT NULL DEFAULT '{}',
    is_builtin BOOLEAN DEFAULT FALSE NOT NULL,
    ...
);
```

**Назначение:** Доступные инструменты (function calling)
**Ключевые поля:**
- `function_schema` - JSON schema для function calling
- `default_config` - конфигурация по умолчанию
- `is_builtin` - встроенный или пользовательский

### User Tools
```sql
CREATE TABLE user_tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    config JSONB NOT NULL DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    ...
    UNIQUE(user_id, tool_id)
);
```

**Назначение:** Связь пользователей с инструментами
**Ключевые поля:**
- `config` - персонализированная конфигурация
- `is_enabled` - включен ли инструмент

### Conversations
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_type VARCHAR(50) NOT NULL, -- 'web', 'telegram', 'voice'
    channel_id VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    metadata JSONB NOT NULL DEFAULT '{}',
    ...
);
```

**Назначение:** Диалоги агента с пользователями
**Ключевые поля:**
- `channel_type` - тип канала общения
- `channel_id` - ID канала (chat_id, session_id)
- `metadata` - дополнительная информация о канале

### Messages
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    ...
);
```

**Назначение:** Сообщения в диалогах
**Ключевые поля:**
- `role` - роль отправителя
- `content` - содержимое сообщения
- `metadata` - техническая информация

### Tool Calls
```sql
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    arguments JSONB NOT NULL,
    result TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    ...
);
```

**Назначение:** Вызовы инструментов из сообщений
**Ключевые поля:**
- `tool_name` - название вызванного инструмента
- `arguments` - аргументы вызова
- `status` - статус выполнения

### Telegram Links
```sql
CREATE TABLE telegram_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_user_id BIGINT NOT NULL,
    telegram_username VARCHAR(255),
    telegram_chat_id BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    ...
);
```

**Назначение:** Связь аккаунтов пользователей с Telegram
**Ключевые поля:**
- `telegram_user_id` - ID пользователя в Telegram
- `telegram_chat_id` - ID чата для общения
- `is_active` - активна ли связь

### Voice Settings
```sql
CREATE TABLE voice_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stt_provider VARCHAR(50) NOT NULL DEFAULT 'openai',
    tts_provider VARCHAR(50) NOT NULL DEFAULT 'openai',
    stt_config JSONB NOT NULL DEFAULT '{}',
    tts_config JSONB NOT NULL DEFAULT '{}',
    voice_id VARCHAR(100),
    language_code VARCHAR(10) DEFAULT 'en-US',
    ...
);
```

**Назначение:** Настройки голосового взаимодействия
**Ключевые поля:**
- `stt_provider`, `tts_provider` - провайдеры распознавания/синтеза
- `voice_id` - предпочитаемый голос
- `language_code` - язык общения

## Индексы

### Основные индексы
```sql
-- Users
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;

-- Agents
CREATE INDEX idx_agents_user_id ON agents(user_id) WHERE deleted_at IS NULL;

-- Skills
CREATE INDEX idx_skills_name ON skills(name) WHERE deleted_at IS NULL;
CREATE INDEX idx_skills_slug ON skills(slug) WHERE deleted_at IS NULL;

-- User Skills
CREATE INDEX idx_user_skills_user_id ON user_skills(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_skills_enabled ON user_skills(is_enabled) WHERE deleted_at IS NULL;
```

### Частые запросы
Индексы оптимизированы под типичные запросы:
- Получение агента пользователя
- Поиск навыков/инструментов
- Фильтрация активных элементов
- История диалогов

## Views (Представления)

### Active Users
```sql
CREATE VIEW active_users AS
SELECT * FROM users 
WHERE deleted_at IS NULL AND is_active = TRUE;
```

### User Enabled Skills
```sql
CREATE VIEW user_enabled_skills AS
SELECT u.id as user_id, u.username, s.id as skill_id, s.name, s.description, us.config
FROM users u
JOIN user_skills us ON u.id = us.user_id
JOIN skills s ON us.skill_id = s.id
WHERE u.deleted_at IS NULL 
  AND us.deleted_at IS NULL 
  AND s.deleted_at IS NULL
  AND us.is_enabled = TRUE
  AND s.is_active = TRUE;
```

Представления упрощают сложные запросы для получения активных навыков и инструментов пользователя.

## Triggers (Триггеры)

### Updated At Trigger
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';
```

Автоматическое обновление поля `updated_at` при изменении записи.

## Constraints (Ограничения)

### One Agent Per User
```sql
ALTER TABLE agents ADD CONSTRAINT one_agent_per_user 
UNIQUE (user_id) WHERE deleted_at IS NULL;
```

Гарантирует, что у каждого пользователя только один агент.

### Check Constraints
```sql
ALTER TABLE messages ADD CONSTRAINT check_message_role 
CHECK (role IN ('user', 'assistant', 'system'));

ALTER TABLE conversations ADD CONSTRAINT check_channel_type 
CHECK (channel_type IN ('web', 'telegram', 'voice'));
```

Проверяют корректность значений в enum полях.

## Встроенные данные

### Default Skills
- General Assistant - базовые возможности ассистента
- Code Helper - помощь в программировании
- Creative Writer - творческое письмо
- Data Analyst - анализ данных

### Default Tools
- Web Search - поиск в интернете
- Calculator - математические вычисления
- Weather - информация о погоде

## Безопасность

1. **UUID** - предотвращает перебор ID
2. **Soft Delete** - сохраняет историю
3. **Foreign Keys** - целостность данных
4. **Unique Constraints** - предотвращение дубликатов
5. **Check Constraints** - валидация данных

## Масштабируемость

1. **Индексы** - оптимизация запросов
2. **JSONB** - гибкая конфигурация
3. **Partitioning** - возможное разделение больших таблиц
4. **Views** - упрощение сложных запросов

Эта схема обеспечивает надежную основу для платформы с возможностью масштабирования и расширения функциональности.
