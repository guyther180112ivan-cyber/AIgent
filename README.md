# AIgent Platform - AI Agent Management System

> **Версия**: 2.0 (Март 2026)  
> **Статус**: ✅ Производственная готовость

## 🚀 О проекте

AIgent Platform - это полнофункциональная система управления AI-агентами с веб-интерфейсом и интеграцией Telegram бота. Платформа позволяет создавать, настраивать и общаться с AI-агентами через веб-интерфейс или Telegram.

## ✨ Текущий функционал

### 🤖 AI Агенты
- **Создание агентов**: Настраиваемые AI-агенты с уникальными системными промптами
- **Интеграция LLM**: Прямое подключение к OpenRouter API (более 200 моделей)
- **Управление навыками**: Привязка навыков к агентам
- **Управление инструментами**: Привязка инструментов для расширения функциональности

### 💬 Мультиканальный чат
- **Веб-интерфейс**: Полнофункциональный чат с историей сообщений
- **Telegram бот**: Полная интеграция с Telegram
  - Одноразовая привязка пользователя через `/link`
  - Персистентность данных между сессиями
  - История сообщений
  - Поддержка контекста диалога

### 🛠️ Система навыков (Skills)
- **Встроенные навыки**: Предустановленные навыки для общих задач
- **Кастомные навыки**: Возможность создания собственных навыков
- **Параметризация**: Настраиваемые параметры для навыков
- **Prompt-шаблоны**: Jinja2 шаблоны для динамических промптов

### 🔧 Система инструментов (Tools)
- **HTTP-инструменты**: Вызов внешних API
- **Кастомные инструменты**: Python-скрипты для специфических задач
- **Параметризация**: Типизированные входные параметры
- **Валидация**: Автоматическая валидация входных данных

### 🔐 Аутентификация
- **JWT токены**: Безопасная аутентификация
- **Регистрация/Вход**: Полный цикл аутентификации
- **Telegram OAuth**: Вход через Telegram

### 💾 Хранение данных
- **SQLite**: Легковесная база данных для разработки
- **PostgreSQL**: Поддержка PostgreSQL для production
- **Гибридная схема**: Cross-database UUID поддержка
- **Файловое хранилище**: JSON-файлы для данных Telegram бота

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                        КЛИЕНТЫ                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Веб-браузер   │   Telegram    │   API клиенты          │
│   localhost:3000│   @AIgentBot  │   (любой HTTP)         │
└────────┬────────┴────────┬────────┴────────────┬────────────┘
         │                 │                     │
         ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                       │
│  • React + TypeScript                                       │
│  • Tailwind CSS                                             │
│  • Прямое обращение к OpenRouter API                        │
│  • Локализация на русском языке                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                        │
│  • Python 3.13+                                             │
│  • FastAPI + SQLAlchemy                                     │
│  • Pydantic v2                                              │
│  • python-telegram-bot                                      │
├─────────────────────────────────────────────────────────────┤
│  API Layer:                                                 │
│  • /api/auth     - Аутентификация                           │
│  • /api/agents   - Управление агентами                      │
│  • /api/skills   - Управление навыками                      │
│  • /api/tools    - Управление инструментами                 │
│  • /api/chat     - Чат с агентами                           │
│  • /health       - Health check                             │
├─────────────────────────────────────────────────────────────┤
│  Runtime:                                                   │
│  • AgentRuntime    - Исполнение агентов                     │
│  • ToolExecutor    - Выполнение инструментов                │
│  • PromptComposer  - Компоновка промптов                    │
├─────────────────────────────────────────────────────────────┤
│  Telegram Bot:                                              │
│  • Автозапуск при старте backend                            │
│  • Персистентность через linked_users.json                  │
│  • Прямое обращение к OpenRouter                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     ВНЕШНИЕ СЕРВИСЫ                         │
│  • OpenRouter API  - LLM модели                             │
│  • Telegram API    - Бот платформа                          │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Требования

### Системные
- **Python**: 3.13+
- **Node.js**: 20+
- **npm**: 10+
- **OS**: Windows 10/11, Linux, macOS

### Python зависимости
```
fastapi==0.115.12
uvicorn[standard]==0.34.0
sqlalchemy==2.0.40
pydantic==2.11.3
pydantic-settings==2.8.1
python-telegram-bot==21.10
httpx==0.28.1
python-jose[cryptography]==3.4.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20
email-validator==2.2.0
aiofiles==24.1.0
```

### Node.js зависимости
```
next: 15.x
react: 19.x
typescript: 5.x
tailwindcss: 4.x
```

## 🚀 Быстрый старт

### 1. Клонирование и настройка

```bash
# Перейти в директорию проекта
cd AIgent

# Создать .env файл для backend
cp backend/.env.example backend/.env
```

### 2. Настройка переменных окружения

Отредактируйте `backend/.env`:

```env
# Обязательно
OPENROUTER_API_KEY=sk-or-v1-your-key-here
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather

# Опционально
DEFAULT_MODEL=openrouter/free
debug=true
```

### 3. Установка зависимостей

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 4. Запуск

**Backend (Терминал 1):**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend (Терминал 2):**
```bash
cd frontend
npm run dev
```

### 5. Доступ

- **Веб-интерфейс**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 Документация

- [QUICK_START.md](QUICK_START.md) - Пошаговое руководство по запуску
- [ARCHITECTURE.md](ARCHITECTURE.md) - Архитектурная документация
- [API.md](API.md) - Документация API endpoints
- [TELEGRAM_BOT.md](TELEGRAM_BOT.md) - Руководство по Telegram боту

## 🔧 API Endpoints

### Health Check
```
GET /health
Response: {"status": "healthy", "telegram_bot": "running"}
```

### Аутентификация
```
POST /api/auth/register    # Регистрация
POST /api/auth/login       # Вход
POST /api/auth/telegram    # Вход через Telegram
```

### Агенты
```
GET    /api/agents         # Список агентов
POST   /api/agents         # Создать агента
GET    /api/agents/{id}    # Получить агента
PUT    /api/agents/{id}    # Обновить агента
DELETE /api/agents/{id}    # Удалить агента
```

### Чат
```
POST /api/chat             # Отправить сообщение
GET  /api/chat/history     # История сообщений
```

## 🤖 Telegram Бот

### Команды
- `/start` - Приветствие и инструкции
- `/link` - Привязать Telegram к аккаунту (одноразово)
- `/newchat` - Начать новый чат
- `/help` - Справка

### Как использовать
1. Найдите бота в Telegram по токену
2. Отправьте `/link` для привязки
3. Отправляйте сообщения для общения с AI

## 🛠️ Разработка

### Структура проекта
```
AIgent/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Конфигурация и БД
│   │   ├── models/         # SQLAlchemy модели
│   │   ├── runtime/        # Runtime логика
│   │   ├── services/       # Сервисы
│   │   ├── skills/         # Система навыков
│   │   └── telegram/       # Telegram интеграция
│   ├── telegram_bot.py     # Standalone Telegram бот
│   └── requirements.txt
├── frontend/               # Next.js frontend
│   ├── app/               # App Router
│   ├── src/
│   │   ├── components/    # React компоненты
│   │   ├── pages/         # Страницы
│   │   └── services/      # API клиенты
│   └── package.json
└── docs/                  # Документация
```

### Режим разработки

**Backend с автоперезагрузкой:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend с HMR:**
```bash
cd frontend
npm run dev
```

## 🔐 Безопасность

- JWT токены с expires_in
- Пароли хешируются с bcrypt
- CORS настроен для localhost
- Валидация всех входных данных через Pydantic
- SQL-инъекции защищены через SQLAlchemy ORM

## 📝 Логирование

Все сервисы логируют в консоль:
- **Backend**: `logging` (Python)
- **Telegram Bot**: `logging` + telegram.ext логи
- **Frontend**: Консоль браузера

## 🐛 Отладка

### Проверка статуса
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Telegram бот логи
# Смотрите в консоли backend - логи бота выводятся там же
```

### Частые проблемы

**Ошибка: Conflict in getUpdates**
- Причина: Запущено несколько экземпляров бота
- Решение: Убедитесь, что запущен только один backend процесс

**Ошибка: Import UserSkill**
- Статус: ✅ Исправлено
- Исправление: `UserSkill` → `AgentSkill` в agent_runtime.py

**Ошибка: Missing List import**
- Статус: ✅ Исправлено  
- Исправление: Добавлен `from typing import List` в tool_executor.py

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте feature branch
3. Сделайте коммиты
4. Создайте Pull Request

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

## 👥 Авторы

- **AIgent Team** - Начальная разработка

## 🙏 Благодарности

- [OpenRouter](https://openrouter.ai/) - За доступ к LLM API
- [python-telegram-bot](https://python-telegram-bot.org/) - За отличную библиотеку
- [FastAPI](https://fastapi.tiangolo.com/) - За современный Python фреймворк
- [Next.js](https://nextjs.org/) - За React фреймворк

---

**Made with ❤️ by AIgent Team**

> **Примечание**: Это активно развивающийся проект. Функционал может изменяться.
