# Деплой AIgent на Render (Упрощённый)

## Требования

- Аккаунт на [render.com](https://render.com)
- Репозиторий на GitHub

## Быстрый деплой (один сервис, SQLite)

### 1. Создайте Web Service на Render

1. Войдите в [Render Dashboard](https://dashboard.render.com)
2. Нажмите **New +** → **Web Service**
3. Подключите ваш GitHub репозиторий
4. Настройте:
   - **Name**: `aigent`
   - **Root Directory**: оставьте пустым (корень репозитория)
   - **Build Command**: `echo "Using Dockerfile"`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: `Python 3.11`

### 2. Добавьте переменные окружения

Нажмите **Advanced** → **Add Environment Variables**:

```
SECRET_KEY=любой-секретный-ключ-минимум-32-символа
OPENROUTER_API_KEY=ваш-openrouter-api-ключ
TELEGRAM_BOT_TOKEN=ваш-telegram-токен
DEBUG=false
```

### 3. Нажмите Create Web Service

Дождитесь сборки (может занять 5-10 минут).

## Локальный запуск

```bash
cd backend
pip install -r requirements-minimal.txt
cp .env.example .env
# Отредактируйте .env файл
uvicorn app.main:app --reload
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| SECRET_KEY | Секретный ключ | сгенерированный |
| DATABASE_URL | SQLite (файл) | sqlite:///./aigent.db |
| OPENROUTER_API_KEY | API ключ OpenRouter | - |
| TELEGRAM_BOT_TOKEN | Токен Telegram бота | - |
| DEBUG | Режим отладки | false |

## Как это работает

- **SQLite**: база данных создаётся автоматически в файле `aigent.db`
- **Без Redis**: кэширование в памяти
- **Один сервис**: фронтенд обслуживается Python/uvicorn (или используйте отдельный хостинг)

## Обновление Telegram Webhook

После деплоя установите webhook:
```
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://ваш-сайт.onrender.com/api/v1/telegram/webhook
```

## Проблемы и решения

### Ошибка 500 при запуске
- Проверьте переменные окружения в Render Dashboard

### Telegram не работает
- Проверьте TELEGRAM_BOT_TOKEN
- Убедитесь что webhook установлен

### База данных не сохраняется
- SQLite файл создаётся в /app/aigent.db
- На Free плане данные могут быть удалены при перезагрузке
