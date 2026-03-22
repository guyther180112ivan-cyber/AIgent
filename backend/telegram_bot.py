#!/usr/bin/env python3
"""
Telegram Bot for AIgent Platform
Uses httpx for direct Telegram API calls (no Rust dependencies)
"""

import os
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Optional

import httpx

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"

USERS_FILE = os.path.join(os.path.dirname(__file__), "linked_users.json")

user_conversations: Dict[int, list] = {}
linked_users: Dict[int, dict] = {}
application = None
update_offset = 0


def load_linked_users():
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
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(linked_users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")


async def send_telegram_request(method: str, data: dict = None) -> dict:
    """Send request to Telegram API"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=data or {})
        return response.json()


async def send_message(chat_id: int, text: str) -> bool:
    """Send message to a specific chat"""
    try:
        result = await send_telegram_request("sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        })
        return result.get("ok", False)
    except Exception as e:
        logger.error(f"Failed to send message to chat {chat_id}: {e}")
        return False


async def get_updates(offset: int = 0, timeout: int = 0) -> list:
    """Get updates from Telegram"""
    result = await send_telegram_request("getUpdates", {
        "offset": offset,
        "timeout": timeout
    })
    if result.get("ok"):
        return result.get("result", [])
    return []


async def process_update(update: dict):
    """Process a single update"""
    global linked_users
    
    message = update.get("message")
    if not message:
        return
    
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    user = message.get("from")
    
    if not chat_id or not text:
        return
    
    user_id = user.get("id") if user else None
    user_name = user.get("first_name", "User") if user else "User"
    
    logger.info(f"Received message from {user_name}: {text}")
    
    if text.startswith("/start"):
        if user_id and user_id not in linked_users:
            linked_users[user_id] = {
                "telegram_id": user_id,
                "name": user_name,
                "username": user.get("username"),
                "linked_at": datetime.now().isoformat(),
                "is_active": True
            }
            save_linked_users()
            await send_message(chat_id, f"Привет, {user_name}! Вы привязаны к системе.")
        else:
            await send_message(chat_id, f"С возвращением, {user_name}! Вы уже привязаны.")
    
    elif text.startswith("/link"):
        if user_id and user_id not in linked_users:
            linked_users[user_id] = {
                "telegram_id": user_id,
                "name": user_name,
                "username": user.get("username"),
                "linked_at": datetime.now().isoformat(),
                "is_active": True
            }
            save_linked_users()
            await send_message(chat_id, "Вы успешно привязаны!")
        else:
            await send_message(chat_id, "Вы уже привязаны.")
    
    elif text.startswith("/help"):
        await send_message(chat_id, "Команды:\n/start - Начать\n/link - Привязать\n/clear - Очистить историю")
    
    elif text.startswith("/clear"):
        if user_id in user_conversations:
            user_conversations[user_id] = []
        await send_message(chat_id, "История очищена.")
    
    elif text.startswith("/status"):
        is_linked = user_id in linked_users
        await send_message(chat_id, f"Статус: {'Привязан' if is_linked else 'Не привязан'}")
    
    else:
        if user_id and user_id in linked_users:
            await handle_conversation(user_id, chat_id, text)
        else:
            await send_message(chat_id, "Отправьте /start для начала работы.")


async def handle_conversation(user_id: int, chat_id: int, text: str):
    """Handle conversation with linked user"""
    global user_conversations
    
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    user_conversations[user_id].append({"role": "user", "content": text})
    
    if len(user_conversations[user_id]) > 10:
        user_conversations[user_id] = user_conversations[user_id][-10:]
    
    response_text = await get_ai_response(user_conversations[user_id], user_id)
    
    user_conversations[user_id].append({"role": "assistant", "content": response_text})
    
    await send_message(chat_id, response_text)


async def get_ai_response(conversation: list, user_id: int) -> str:
    """Get response from OpenRouter"""
    if not OPENROUTER_API_KEY:
        return "AI не настроен. Установите OPENROUTER_API_KEY."
    
    messages = [
        {"role": "system", "content": "Вы - ИИ-ассистент. Отвечайте кратко и по делу."}
    ] + conversation
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": DEFAULT_MODEL,
                    "messages": messages
                }
            )
            result = response.json()
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        return "Произошла ошибка при обработке запроса."


async def polling_loop():
    """Main polling loop"""
    global update_offset
    
    logger.info("Starting Telegram bot polling...")
    
    while True:
        try:
            updates = await get_updates(offset=update_offset, timeout=5)
            
            for update in updates:
                update_id = update.get("update_id", 0)
                if update_id >= update_offset:
                    update_offset = update_id + 1
                await process_update(update)
                
        except Exception as e:
            logger.error(f"Polling error: {e}")
            await asyncio.sleep(5)


async def main():
    """Main async function"""
    global application
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    logger.info("Starting Telegram bot...")
    load_linked_users()
    
    await polling_loop()


if __name__ == "__main__":
    asyncio.run(main())
