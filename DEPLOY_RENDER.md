# Деплой AIgent на Render

## Вариант 1: Backend на Python + Frontend отдельно

### Backend на Render (Python)

1. **New +** → **Web Service**
2. Подключите репозиторий
3. Настройте:
   - **Name**: `aigent-backend`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements-minimal.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: `Python 3`

4. Добавьте переменные окружения:
   ```
   SECRET_KEY=любой-секретный-ключ
   OPENROUTER_API_KEY=ваш-api-ключ
   TELEGRAM_BOT_TOKEN=ваш-telegram-токен
   DATABASE_URL=sqlite:///./aigent.db
   ```

### Frontend на Vercel (рекомендуется)

1. Зайдите на [Vercel](https://vercel.com)
2. Import GitHub репозиторий
3. Настройте:
   - Framework Preset: `Next.js`
   - Root Directory: `frontend`
4. Добавьте переменную:
   ```
   NEXT_PUBLIC_API_URL=https://aigent-backend.onrender.com
   ```

## Вариант 2: Всё на Render (Python)

### Backend + Статические файлы

1. **New +** → **Web Service**
2. Настройте:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements-minimal.txt`
   - **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. Для фронтенда создайте отдельный Static Site:
   - **New +** → **Static Site**
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish directory**: `out`

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| SECRET_KEY | Секретный ключ |
| DATABASE_URL | SQLite: `sqlite:///./aigent.db` |
| OPENROUTER_API_KEY | API ключ OpenRouter |
| TELEGRAM_BOT_TOKEN | Токен Telegram |

## После деплоя

Установите Telegram webhook:
```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://aigent-backend.onrender.com/api/v1/telegram/webhook
```
