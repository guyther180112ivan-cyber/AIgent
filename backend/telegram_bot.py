#!/usr/bin/env python3
"""
Telegram Bot for AIgent Platform
Runs as part of FastAPI application
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = "8585374186:AAEkMXN7ZCee02FzOK8rNLKIrMJUvWfpP28"
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"

# File to store linked users
USERS_FILE = os.path.join(os.path.dirname(__file__), "linked_users.json")

# In-memory storage
user_conversations: Dict[int, list] = {}
linked_users: Dict[int, dict] = {}
application: Optional[Application] = None


def load_linked_users():
    """Load linked users from file"""
    global linked_users
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                linked_users = {int(k): v for k, v in data.items()}
            logger.info(f"Loaded {len(linked_users)} linked users")
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            linked_users = {}


def save_linked_users():
    """Save linked users to file"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(linked_users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if user_id in linked_users:
        await update.message.reply_text(
            f"С возвращением, {user_name}!\n\n"
            f"Вы уже привязаны к системе.\n"
            f"Просто напишите сообщение, и я отвечу!"
        )
    else:
        welcome_text = (
            f"Привет, {user_name}!\n\n"
            f"Я ИИ-ассистент на базе OpenRouter.\n"
            f"Для начала работы необходимо привязать ваш аккаунт.\n\n"
            f"Отправьте /link для привязки"
        )
        await update.message.reply_text(welcome_text)


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /link command - one-time binding"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    username = update.effective_user.username or "unknown"
    
    if user_id in linked_users:
        await update.message.reply_text(
            "Вы уже привязаны к системе!\n"
            f"Дата привязки: {linked_users[user_id].get('linked_at', 'неизвестно')}"
        )
        return
    
    linked_users[user_id] = {
        "telegram_id": user_id,
        "name": user_name,
        "username": username,
        "linked_at": datetime.now().isoformat(),
        "is_active": True
    }
    
    save_linked_users()
    
    await update.message.reply_text(
        "Привязка выполнена успешно!\n\n"
        "Теперь вы можете:\n"
        "• Писать сообщения и получать ответы от ИИ\n"
        "• Использовать /clear для очистки истории\n"
        "• Использовать /help для справки"
    )


async def unlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unlink command"""
    user_id = update.effective_user.id
    
    if user_id in linked_users:
        linked_users[user_id]["is_active"] = False
        save_linked_users()
        await update.message.reply_text(
            "Ваш аккаунт отвязан.\n"
            "Отправьте /link чтобы привязаться снова."
        )
    else:
        await update.message.reply_text(
            "Вы еще не привязаны к системе.\n"
            "Отправьте /link для привязки."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "ИИ Агент Бот\n\n"
        "Команды:\n"
        "/start - Начать диалог\n"
        "/link - Привязать аккаунт (один раз)\n"
        "/unlink - Отвязать аккаунт\n"
        "/help - Показать справку\n"
        "/clear - Очистить историю разговора\n"
        "/status - Показать статус\n\n"
        "Просто напишите сообщение, и я отвечу!"
    )
    await update.message.reply_text(help_text)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command"""
    user_id = update.effective_user.id
    
    if user_id in user_conversations:
        user_conversations[user_id] = []
        await update.message.reply_text("История разговора очищена!")
    else:
        await update.message.reply_text("История разговора пуста.")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = update.effective_user.id
    
    if user_id in linked_users:
        user_data = linked_users[user_id]
        status_text = (
            "Статус аккаунта:\n"
            f"Привязан: Да\n"
            f"Имя: {user_data.get('name', 'неизвестно')}\n"
            f"Дата привязки: {user_data.get('linked_at', 'неизвестно')[:10]}\n"
            f"Активен: {'Да' if user_data.get('is_active', True) else 'Нет'}"
        )
    else:
        status_text = (
            "Статус аккаунта:\n"
            "Привязан: Нет\n\n"
            "Отправьте /link для привязки"
        )
    
    await update.message.reply_text(status_text)


async def get_openrouter_response(messages: list) -> str:
    """Get response from OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://aigent-platform.com",
        "X-Title": "AIgent Telegram Bot"
    }
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code}")
                return f"Ошибка API: {response.status_code}"
            
            data = response.json()
            
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"]
            else:
                return "Не удалось получить ответ от ИИ"
                
        except Exception as e:
            logger.error(f"Error calling OpenRouter: {str(e)}")
            return f"Ошибка: {str(e)}"


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from linked users only"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    if user_id not in linked_users or not linked_users[user_id].get("is_active", True):
        await update.message.reply_text(
            "Вы не привязаны к системе.\n"
            "Отправьте /link для привязки."
        )
        return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    if user_id not in user_conversations:
        user_conversations[user_id] = [
            {"role": "system", "content": "Вы - полезный ИИ-ассистент. Отвечайте на русском языке."}
        ]
    
    user_conversations[user_id].append({"role": "user", "content": user_message})
    
    if len(user_conversations[user_id]) > 21:
        user_conversations[user_id] = [user_conversations[user_id][0]] + user_conversations[user_id][-20:]
    
    response = await get_openrouter_response(user_conversations[user_id])
    
    user_conversations[user_id].append({"role": "assistant", "content": response})
    
    await update.message.reply_text(response)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )


async def setup_bot():
    """Setup and return bot application"""
    global application
    
    # Load linked users
    load_linked_users()
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("link", link_command))
    application.add_handler(CommandHandler("unlink", unlink_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("status", status_command))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    application.add_error_handler(error_handler)
    
    return application


async def send_message(chat_id: int, text: str) -> bool:
    """
    Send a message to a specific chat.
    Used by the scheduler service for scheduled messages.
    
    Args:
        chat_id: Telegram chat ID
        text: Message text
        
    Returns:
        bool: True if message was sent successfully
    """
    global application
    
    if not application:
        logger.error("Telegram bot application not initialized")
        return False
        
    try:
        await application.bot.send_message(chat_id=chat_id, text=text)
        logger.info(f"Scheduled message sent to chat {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message to chat {chat_id}: {e}")
        return False


async def main():
    """Main async function to run the bot"""
    global application
    
    logger.info("Setting up Telegram bot...")
    await setup_bot()
    
    logger.info("Starting Telegram bot polling...")
    await application.initialize()
    await application.start()
    
    # Start polling
    await application.updater.start_polling(drop_pending_updates=True)
    
    logger.info("Telegram bot started successfully!")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Telegram bot received stop signal")
        raise
    finally:
        logger.info("Stopping Telegram bot...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        logger.info("Telegram bot stopped")


# Standalone mode
if __name__ == "__main__":
    import time
    
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\nBot stopped by user")
            break
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            print(f"Bot crashed: {e}")
            print("Restarting in 5 seconds...")
            time.sleep(5)
