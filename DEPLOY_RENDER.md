# Деплой AIgent на Render

## Требования

- Аккаунт на [render.com](https://render.com)
- Репозиторий на GitHub с проектом

## Шаги

### 1. Подготовка репозитория

Убедитесь что в корне проекта есть:
- `backend/Dockerfile` - для Python/FastAPI
- `frontend/Dockerfile` - для Next.js
- `docker-compose.yml` - для оркестрации

### 2. Создание Web Services на Render

#### Backend (FastAPI)

1. Войдите в [Render Dashboard](https://dashboard.render.com)
2. Нажмите **New +** → **Web Service**
3. Подключите ваш GitHub репозиторий
4. Настройте:
   - **Name**: `aigent-backend`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: `Python 3.11`

5. Добавьте переменные окружения:
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/aigent
   REDIS_URL=redis://host:6379
   SECRET_KEY=your-secret-key
   OPENAI_API_KEY=your-openai-key
   OPENROUTER_API_KEY=your-openrouter-key
   TELEGRAM_BOT_TOKEN=your-telegram-token
   ```

6. Нажмите **Create Web Service**

#### Frontend (Next.js)

1. Нажмите **New +** → **Web Service**
2. Подключите репозиторий
3. Настройте:
   - **Name**: `aigent-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run start`
   - **Environment**: `Node`

4. Добавьте переменные окружения:
   ```
   NEXT_PUBLIC_API_URL=https://aigent-backend.onrender.com
   NEXT_PUBLIC_WS_URL=wss://aigent-backend.onrender.com
   ```

### 3. Использование PostgreSQL и Redis

1. **PostgreSQL**:
   - Нажмите **New +** → **PostgreSQL**
   - Выберите план (Free: $0)
   - Скопируйте Internal Database URL в переменные окружения backend

2. **Redis** (опционально):
   - Нажмите **New +** → **Redis**
   - Выберите план Free
   - Скопируйте URL в переменные окружения

### 4. Настройка CORS

В `backend/app/main.py` добавьте домен фронтенда:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aigent-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Обновление Telegram Bot Webhook

После деплоя обновите webhook Telegram:
```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://aigent-backend.onrender.com/api/v1/telegram/webhook
```

### Бесплатные лимиты Render

- **Web Services**: 750 часов/месяц (останавливайте сервисы ночью)
- **PostgreSQL**: 1 БД, 90 дней жизни
- **Redis**: 30MB, 30 дней жизни

### Альтернатива: один Docker compose

Используйте Render's "Native Docker" с docker-compose.yml напрямую:
1. **New +** → **Web Service**
2. **Dockerfile Repository**: включите ваш репозиторий
3. Render автоматически определит docker-compose.yml

## Устранение проблем

### Ошибка сборки
- Проверьте логи в Render Dashboard
- Убедитесь что все зависимости в requirements.txt

### Ошибка подключения к БД
- Проверьте DATABASE_URL
- Дождитесь инициализации PostgreSQL (может занять 2-3 минуты)

### Telegram не работает
- Проверьте TELEGRAM_BOT_TOKEN
- Убедитесь что webhook установлен правильно
