# Telegram Bot Documentation

> Руководство по использованию и настройке Telegram бота AIgent Platform | Версия 2.0

## Обзор

Telegram бот интегрирован в AIgent Platform и предоставляет доступ к AI-агентам через мессенджер Telegram. Бот работает как фоновый процесс внутри backend сервиса.

## Архитектура

```
Пользователь (Telegram)
    │
    │ HTTPS (Telegram Bot API)
    ▼
Telegram Cloud
    │
    │ Webhook / Long Polling
    ▼
┌─────────────────────────────────────┐
│  Backend (FastAPI)                  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Telegram Bot (polling)      │  │
│  │  • Update Handler            │  │
│  │  • Command Router            │  │
│  │  • Message Processor         │  │
│  └──────────────────────────────┘  │
│              │                      │
│              ▼                      │
│  ┌──────────────────────────────┐  │
│  │  User Linking System         │  │
│  │  • linked_users.json         │  │
│  │  • One-time linking          │  │
│  └──────────────────────────────┘  │
│              │                      │
│              ▼                      │
│  ┌──────────────────────────────┐  │
│  │  OpenRouter Integration      │  │
│  │  • Direct API calls          │  │
│  │  • Context management        │  │
│  │  • Response streaming        │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Настройка

### 1. Создание бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Введите название бота (например, "AIgent Assistant")
4. Введите username бота (должен заканчиваться на 'bot', например, 'aigent_assistant_bot')
5. Получите **токен бота** (вида: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Конфигурация

Добавьте токен в файл `backend/.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Запуск

Бот запускается автоматически вместе с backend:

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Проверка статуса бота:
```bash
curl http://localhost:8000/health
# Ответ: {"status": "healthy", "telegram_bot": "running"}
```

## Команды бота

### /start
Приветственное сообщение с инструкциями.

**Ответ бота:**
```
🤖 Привет! Я AIgent Bot - ваш персональный AI-ассистент.

📝 Доступные команды:
/link - Привязать ваш аккаунт (одноразово)
/newchat - Начать новый чат
/help - Показать справку

💡 Просто отправьте сообщение, чтобы начать общение с AI!
```

### /link
Привязка Telegram аккаунта к системе.

**Процесс:**
1. Пользователь отправляет `/link`
2. Бот генерирует код привязки или запрашивает ID
3. Пользователь подтверждает привязку
4. Данные сохраняются в `linked_users.json`

**Формат данных:**
```json
{
  "123456789": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "telegram_id": "123456789",
    "username": "johndoe",
    "linked_at": "2026-03-07T10:00:00Z",
    "context": {
      "messages": [...],
      "preferences": {...}
    }
  }
}
```

**Важно:** Привязка выполняется одноразово и сохраняется между перезапусками.

### /newchat
Начать новую беседу (очистить контекст).

**Ответ бота:**
```
✅ Новый чат начат! Контекст предыдущего разговера очищен.

💬 Можете задавать вопросы!
```

### /help
Справка по использованию бота.

### /status
Проверка статуса привязки.

**Ответ бота:**
```
📊 Статус аккаунта:
• Привязка: ✅ Активна
• Пользователь: johndoe
• ID: 123456789
• Дата привязки: 2026-03-07

✅ Можете отправлять сообщения!
```

## Использование

### Первый запуск

1. Найдите бота в Telegram по username (например, `@aigent_assistant_bot`)
2. Нажмите "Start" или отправьте `/start`
3. Отправьте `/link` для привязки аккаунта
4. После успешной привязки отправляйте сообщения

### Пример диалога

**Пользователь:** `/link`

**Бот:**
```
🔗 Привязка аккаунта

Ваш Telegram ID: 123456789
Для завершения привязки используйте веб-интерфейс:
1. Зайдите в настройки профиля
2. Нажмите "Привязать Telegram"
3. Введите код: LINK-123456

Или отправьте мне email и пароль для автоматической привязки.
```

**Пользователь:** `Привет! Расскажи о себе`

**Бот:**
```
Привет! 👋 Я AI-ассистент, интегрированный с AIgent Platform.

Мои возможности:
• Отвечать на вопросы
• Помогать с программированием
• Анализировать текст
• И многое другое!

Сейчас я использую модель: openrouter/free
```

**Пользователь:** `/newchat`

**Бот:**
```
✅ Начат новый чат. Контекст очищен!
```

## Контекст и память

### Сохранение контекста

Бот сохраняет:
- Историю сообщений (до 20 последних)
- Предпочтения пользователя
- Настройки модели
- Данные о привязке

### Файл хранения

Данные сохраняются в `backend/linked_users.json`:

```json
{
  "123456789": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "telegram_id": "123456789",
    "username": "johndoe",
    "first_name": "John",
    "linked_at": "2026-03-07T10:00:00Z",
    "context": {
      "current_conversation": [
        {"role": "user", "content": "Привет!", "timestamp": "..."},
        {"role": "assistant", "content": "Здравствуйте!", "timestamp": "..."}
      ],
      "preferences": {
        "language": "ru",
        "model": "openrouter/free"
      }
    },
    "stats": {
      "total_messages": 150,
      "last_activity": "2026-03-07T15:30:00Z"
    }
  }
}
```

## Техническая реализация

### Структура кода

```python
# backend/telegram_bot.py

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes
import json
import os

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.app = Application.builder().token(self.token).build()
        self.linked_users_file = "linked_users.json"
        self.linked_users = self.load_linked_users()
        
    def load_linked_users(self) -> dict:
        """Загрузка привязанных пользователей"""
        if os.path.exists(self.linked_users_file):
            with open(self.linked_users_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_linked_users(self):
        """Сохранение привязанных пользователей"""
        with open(self.linked_users_file, 'w') as f:
            json.dump(self.linked_users, f, indent=2)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик /start"""
        await update.message.reply_text(
            "🤖 Привет! Я AIgent Bot!\n\n"
            "Отправь /link для привязки аккаунта"
        )
    
    async def link_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик /link"""
        telegram_id = str(update.effective_user.id)
        
        if telegram_id in self.linked_users:
            await update.message.reply_text("✅ Ваш аккаунт уже привязан!")
            return
        
        # Создание новой привязки
        self.linked_users[telegram_id] = {
            "telegram_id": telegram_id,
            "username": update.effective_user.username,
            "linked_at": datetime.now().isoformat(),
            "context": {"messages": []}
        }
        self.save_linked_users()
        
        await update.message.reply_text(
            "✅ Аккаунт успешно привязан!\n"
            "Теперь можете отправлять сообщения."
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        telegram_id = str(update.effective_user.id)
        
        # Проверка привязки
        if telegram_id not in self.linked_users:
            await update.message.reply_text(
                "❌ Сначала привяжите аккаунт командой /link"
            )
            return
        
        user_message = update.message.text
        
        # Отправка "typing" статуса
        await update.message.chat.send_action(action="typing")
        
        # Получение контекста
        user_context = self.linked_users[telegram_id].get("context", {})
        messages = user_context.get("messages", [])
        
        # Добавление сообщения пользователя
        messages.append({"role": "user", "content": user_message})
        
        # Вызов OpenRouter API
        response = await self.call_openrouter(messages)
        
        # Добавление ответа ассистента
        messages.append({"role": "assistant", "content": response})
        
        # Ограничение истории (последние 20 сообщений)
        messages = messages[-20:]
        
        # Сохранение контекста
        self.linked_users[telegram_id]["context"]["messages"] = messages
        self.save_linked_users()
        
        # Отправка ответа
        await update.message.reply_text(response)
    
    async def call_openrouter(self, messages: list) -> str:
        """Вызов OpenRouter API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openrouter/free",
                    "messages": messages
                }
            )
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("link", self.link_command))
        self.app.add_handler(CommandHandler("newchat", self.newchat_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def run(self):
        """Запуск бота"""
        self.setup_handlers()
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
```

### Интеграция с FastAPI

```python
# backend/app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    telegram_bot_task = asyncio.create_task(run_telegram_bot())
    yield
    # Shutdown
    if telegram_bot_task:
        telegram_bot_task.cancel()

app = FastAPI(lifespan=lifespan)

async def run_telegram_bot():
    """Запуск Telegram бота как background task"""
    bot = TelegramBot()
    await bot.run()
```

## Ограничения

### Rate Limits
- Telegram API: 30 сообщений/секунду
- OpenRouter Free tier: 20 запросов/минута
- Контекст: максимум 20 сообщений

### Размер сообщений
- Telegram: 4096 символов на сообщение
- OpenRouter: зависит от модели (обычно 4K-128K токенов)

## Безопасность

### Защита данных
- Токены хранятся в `.env` (не в коде)
- `linked_users.json` должен быть в `.gitignore`
- Данные пользователей не передаются третьим лицам

### Проверка привязки
```python
def is_user_linked(telegram_id: str) -> bool:
    return telegram_id in linked_users

def get_user_context(telegram_id: str) -> dict:
    if not is_user_linked(telegram_id):
        raise UnauthorizedError()
    return linked_users[telegram_id].get("context", {})
```

## Отладка

### Логи бота
Логи выводятся в консоль backend:
```
2026-03-07 10:00:00 - telegram_bot - INFO - Bot started
2026-03-07 10:00:01 - telegram_bot - INFO - Received message from user 123456789
2026-03-07 10:00:02 - telegram_bot - INFO - Calling OpenRouter API
2026-03-07 10:00:03 - telegram_bot - INFO - Response sent
```

### Тестирование вручную
```bash
# Получить информацию о боте
curl https://api.telegram.org/bot<TOKEN>/getMe

# Отправить тестовое сообщение
curl -X POST https://api.telegram.org/bot<TOKEN>/sendMessage \
  -d "chat_id=<CHAT_ID>" \
  -d "text=Test message"
```

## Troubleshooting

### Ошибка: Conflict in getUpdates
**Причина:** Запущено несколько экземпляров бота
**Решение:** Остановите все процессы Python и запустите только один backend

```bash
# Windows
taskkill /F /IM python.exe

# Linux/Mac
pkill -f uvicorn
```

### Ошибка: Bot token invalid
**Причина:** Неверный токен
**Решение:** Проверьте токен в `backend/.env`

### Ошибка: Unauthorized
**Причина:** Пользователь не привязан
**Решение:** Пользователь должен отправить `/link`

### Ошибка: OpenRouter API error
**Причина:** Неверный API ключ или превышен лимит
**Решение:** Проверьте `OPENROUTER_API_KEY` в `.env`

## Дополнительные возможности (в разработке)

### Voice messages
```python
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка голосовых сообщений"""
    voice_file = await update.message.voice.get_file()
    # STT (Speech-to-Text) -> OpenRouter -> TTS или текст
```

### Inline режим
```python
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка inline запросов (@bot query)"""
    query = update.inline_query.query
    results = await search_agents(query)
    await update.inline_query.answer(results)
```

### Webhook (для production)
```python
# Вместо polling
await app.updater.start_webhook(
    listen="0.0.0.0",
    port=8443,
    webhook_url="https://api.aigent.com/webhook"
)
```

## Ссылки

- [python-telegram-bot документация](https://python-telegram-bot.readthedocs.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenRouter API](https://openrouter.ai/docs)
