# Quick Start Guide

> Быстрый старт AIgent Platform | Версия 2.0

## ⚡ Быстрый запуск (5 минут)

### Предварительные требования

- **Python** 3.13+ установлен
- **Node.js** 20+ установлен
- **Git** (опционально)

Проверьте версии:
```bash
python --version  # Python 3.13.x
node --version    # v20.x.x
npm --version     # 10.x.x
```

---

## 🚀 Запуск проекта

### Шаг 1: Настройка окружения

```bash
# Создать .env файл для backend
cd backend

# Windows (PowerShell)
Copy-Item .env.example .env

# Windows (CMD)
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### Шаг 2: Настройка переменных окружения

Откройте `backend/.env` и добавьте:

```env
# Обязательно
OPENROUTER_API_KEY=sk-or-v1-your-key-here
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Опционально (уже есть значения по умолчанию)
DEFAULT_MODEL=openrouter/free
debug=true
```

**Как получить:**
- **OpenRouter API Key**: https://openrouter.ai/keys
- **Telegram Bot Token**: Напишите [@BotFather](https://t.me/BotFather) → `/newbot`

### Шаг 3: Установка зависимостей

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

### Шаг 4: Запуск сервисов

**Терминал 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Терминал 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Шаг 5: Проверка работы

Откройте в браузере:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Проверьте health endpoint:
```bash
curl http://localhost:8000/health
# Должно вернуть: {"status": "healthy", "telegram_bot": "running"}
```

---

## 📁 Структура проекта

```
AIgent/
├── backend/                  # FastAPI Backend
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   ├── core/            # Config & Database
│   │   ├── models/          # SQLAlchemy models
│   │   ├── runtime/         # Agent runtime
│   │   ├── services/        # Business logic
│   │   ├── skills/          # Skills system
│   │   └── telegram/        # Telegram integration
│   ├── telegram_bot.py      # Standalone bot
│   ├── requirements.txt     # Python deps
│   └── .env                 # Environment variables
│
├── frontend/                 # Next.js Frontend
│   ├── app/                 # Next.js App Router
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   └── services/        # API clients
│   ├── package.json         # Node deps
│   └── next.config.js       # Next.js config
│
└── docs/                     # Documentation
    ├── README.md            # This file
    ├── ARCHITECTURE.md      # System architecture
    ├── API.md               # API documentation
    └── TELEGRAM_BOT.md      # Bot documentation
```

---

## 🛠️ Режим разработки

### Backend (с автоперезагрузкой)

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Флаги:**
- `--reload` - автоперезагрузка при изменении кода
- `--host 0.0.0.0` - доступ с любого IP
- `--port 8000` - порт сервера

### Frontend (с HMR)

```bash
cd frontend
npm run dev
```

Next.js запустится на `http://localhost:3000` с Hot Module Replacement.

---

## 🐳 Запуск через Docker (опционально)

### Требования
- Docker Desktop установлен

### Запуск всех сервисов

```bash
# Собрать и запустить
docker-compose up --build

# Или в фоне
docker-compose up -d --build
```

### Доступ
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

### Остановка
```bash
docker-compose down
```

---

## 🔧 Устранение неполадок

### Ошибка: Module not found

**Python:**
```bash
cd backend
pip install -r requirements.txt
```

**Node:**
```bash
cd frontend
npm install
```

### Ошибка: Port already in use

**Порт 8000 (backend):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Порт 3000 (frontend):**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

### Ошибка: ImportError

Если видите ошибки импорта, проверьте:
1. Установлены ли все зависимости
2. Запускаете ли из правильной директории

```bash
# Backend должен запускаться из папки backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Ошибка: Conflict in getUpdates (Telegram)

**Причина:** Запущено несколько экземпляров бота

**Решение:**
```bash
# Windows - убить все Python процессы
taskkill /F /IM python.exe

# Затем запустить заново
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Ошибка: Database locked (SQLite)

**Причина:** Несколько процессов используют одну БД

**Решение:** Убедитесь, что запущен только один backend процесс.

---

## ✅ Проверка функциональности

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "telegram_bot": "running"
}
```

### 2. API Documentation

Откройте http://localhost:8000/docs

Должна открыться Swagger UI со списком всех endpoints.

### 3. Frontend

Откройте http://localhost:3000

Должен отобразиться интерфейс чата на русском языке.

### 4. Telegram Bot

1. Найдите бота по username (из [@BotFather](https://t.me/BotFather))
2. Отправьте `/start`
3. Отправьте `/link` для привязки
4. Отправьте тестовое сообщение

---

## 📝 Переменные окружения

### Backend (.env)

| Переменная | Обязательная | Описание | По умолчанию |
|------------|--------------|----------|--------------|
| `OPENROUTER_API_KEY` | ✅ | API ключ OpenRouter | - |
| `TELEGRAM_BOT_TOKEN` | ✅ | Токен Telegram бота | - |
| `DATABASE_URL` | ❌ | URL базы данных | `sqlite:///./aigent.db` |
| `DEFAULT_MODEL` | ❌ | Модель LLM по умолчанию | `openrouter/free` |
| `DEBUG` | ❌ | Режим отладки | `true` |
| `JWT_SECRET` | ❌ | Секрет для JWT | `auto-generated` |
| `JWT_ALGORITHM` | ❌ | Алгоритм JWT | `HS256` |

### Frontend (.env.local)

```env
# Создайте frontend/.env.local если нужно
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🔄 Обновление проекта

### Получение обновлений

```bash
git pull origin main
```

### Обновление зависимостей

```bash
# Backend
cd backend
pip install -r requirements.txt --upgrade

# Frontend
cd frontend
npm update
```

---

## 🧪 Тестирование

### Backend тесты

```bash
cd backend
pytest
```

### Frontend тесты

```bash
cd frontend
npm test
```

---

## 📦 Production деплой

### Требования
- Сервер с Python 3.13+
- Node.js 20+
- PostgreSQL (рекомендуется)
- Nginx (reverse proxy)

### Backend (Production)

```bash
cd backend

# Установка зависимостей
pip install -r requirements.txt

# Настройка PostgreSQL
# Измените DATABASE_URL в .env

# Запуск с Gunicorn + Uvicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (Production)

```bash
cd frontend

# Сборка
npm run build

# Запуск
npm start
```

### Docker Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 💡 Полезные команды

### Backend

```bash
# Создать миграции
cd backend
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head

# Откатить миграции
alembic downgrade -1
```

### Frontend

```bash
# Линтинг
cd frontend
npm run lint

# Форматирование
npm run format

# Сборка
npm run build

# Анализ бандла
npm run analyze
```

---

## 🆘 Поддержка

Если у вас возникли проблемы:

1. Проверьте [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Проверьте логи сервисов
3. Создайте Issue на GitHub

---

## 📚 Дополнительная документация

- [README.md](README.md) - Общая информация о проекте
- [ARCHITECTURE.md](ARCHITECTURE.md) - Архитектура системы
- [API.md](API.md) - Документация API
- [TELEGRAM_BOT.md](TELEGRAM_BOT.md) - Документация Telegram бота

---

## 🎉 Готово!

Вы успешно запустили AIgent Platform!

**Что дальше:**
1. Откройте http://localhost:3000
2. Создайте своего первого AI-агента
3. Пообщайтесь с ним в чате
4. Попробуйте Telegram бота

**Удачной разработки!** 🚀
