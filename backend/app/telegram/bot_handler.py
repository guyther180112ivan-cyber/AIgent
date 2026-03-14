import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import aiofiles
import tempfile
import os

from .models import TelegramLink
from .voice_processor import VoiceProcessor
from .auth_manager import TelegramAuthManager
from ..runtime.agent_runtime import AgentRuntime
from ..core.database import get_db
from ..models import User, Conversation, Message
from .exceptions import TelegramBotError, UserNotLinkedError, VoiceProcessingError

logger = logging.getLogger(__name__)


class TelegramBotHandler:
    """
    Main Telegram bot handler for AI agent interaction.
    """
    
    def __init__(self, bot_token: str, agent_runtime: AgentRuntime):
        self.bot_token = bot_token
        self.agent_runtime = agent_runtime
        self.voice_processor = VoiceProcessor()
        self.auth_manager = TelegramAuthManager()
        
        # Initialize bot
        self.application = Application.builder().token(bot_token).build()
        self.bot = self.application.bot
        
        # Register handlers
        self._register_handlers()
        
        # Bot state
        self._user_states: Dict[int, Dict[str, Any]] = {}
    
    def _register_handlers(self):
        """Register Telegram bot handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("help", self.handle_help))
        self.application.add_handler(CommandHandler("link", self.handle_link))
        self.application.add_handler(CommandHandler("unlink", self.handle_unlink))
        self.application.add_handler(CommandHandler("status", self.handle_status))
        self.application.add_handler(CommandHandler("skills", self.handle_skills))
        self.application.add_handler(CommandHandler("settings", self.handle_settings))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))
        self.application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio_message))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CommandHandler("callback", self.handle_callback_query))
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        try:
            # Check if user is already linked
            with get_db() as db:
                telegram_link = db.query(TelegramLink).filter(
                    TelegramLink.telegram_user_id == user_id,
                    TelegramLink.is_active == True
                ).first()
                
                if telegram_link:
                    await self._send_welcome_message(update, linked=True)
                else:
                    await self._send_link_instructions(update)
                    
        except Exception as e:
            logger.error(f"Error in start handler: {str(e)}")
            await update.message.reply_text("Sorry, an error occurred. Please try again.")
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
🤖 *AI Agent Bot Help*

*Commands:*
/start - Start using the bot
/link - Link your account
/unlink - Unlink your account
/status - Check your agent status
/skills - Manage your skills
/settings - Bot settings

*Features:*
• Chat with your personal AI agent
• Send voice messages (voice-to-text)
• Manage skills and tools
• Get personalized responses

*Need help?*
Contact support or visit our website.
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode="Markdown"
        )
    
    async def handle_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /link command."""
        user_id = update.effective_user.id
        
        try:
            # Generate link token
            link_token = await self.auth_manager.generate_link_token(user_id)
            
            # Create link URL
            link_url = f"https://your-platform.com/telegram/link?token={link_token}"
            
            # Send instructions
            keyboard = [[InlineKeyboardButton("🔗 Link Account", url=link_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🔗 *Link Your Account*\n\n"
                "To link your Telegram account with your AI agent platform:\n\n"
                "1. Click the button below\n"
                "2. Sign in to your platform account\n"
                "3. Confirm the linking\n\n"
                "Your account will be linked and you can start chatting!",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error generating link token: {str(e)}")
            await update.message.reply_text("Sorry, couldn't generate link. Please try again.")
    
    async def handle_unlink(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unlink command."""
        user_id = update.effective_user.id
        
        try:
            with get_db() as db:
                telegram_link = db.query(TelegramLink).filter(
                    TelegramLink.telegram_user_id == user_id,
                    TelegramLink.is_active == True
                ).first()
                
                if telegram_link:
                    # Deactivate link
                    telegram_link.is_active = False
                    telegram_link.updated_at = datetime.utcnow()
                    db.commit()
                    
                    await update.message.reply_text(
                        "✅ Your account has been unlinked. "
                        "Use /link to connect again."
                    )
                else:
                    await update.message.reply_text(
                        "❌ No active link found. Use /link to connect your account."
                    )
                    
        except Exception as e:
            logger.error(f"Error unlinking account: {str(e)}")
            await update.message.reply_text("Sorry, couldn't unlink account. Please try again.")
    
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        user_id = update.effective_user.id
        
        try:
            # Get platform user
            platform_user = await self.auth_manager.get_user_by_telegram_id(user_id)
            if not platform_user:
                await update.message.reply_text(
                    "❌ Account not linked. Use /link to connect your account."
                )
                return
            
            # Get agent status
            agent_status = await self.agent_runtime.get_agent_status(platform_user.id)
            
            if agent_status["status"] == "no_agent":
                await update.message.reply_text(
                    "❌ No agent found. Please create an agent on the platform first."
                )
                return
            
            # Format status message
            status_text = f"""
🤖 *Agent Status*

*Name:* {agent_status['agent_name']}
*Model:* {agent_status['model']}
*Skills:* {agent_status['skills_count']} active
*Tools:* {agent_status['tools_count']} active
*Last Updated:* {agent_status.get('last_updated', 'Unknown')}

✅ Your agent is ready to chat!
            """
            
            await update.message.reply_text(
                status_text,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            await update.message.reply_text("Sorry, couldn't get status. Please try again.")
    
    async def handle_skills(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /skills command."""
        user_id = update.effective_user.id
        
        try:
            # Get platform user
            platform_user = await self.auth_manager.get_user_by_telegram_id(user_id)
            if not platform_user:
                await update.message.reply_text(
                    "❌ Account not linked. Use /link to connect your account."
                )
                return
            
            # Get user skills
            with get_db() as db:
                from ..skills.models import UserSkill, Skill
                
                user_skills = db.query(UserSkill, Skill).join(Skill).filter(
                    UserSkill.user_id == platform_user.id,
                    UserSkill.is_enabled == True,
                    Skill.is_active == True
                ).all()
            
            if not user_skills:
                await update.message.reply_text(
                    "📝 *No active skills*\n\n"
                    "You don't have any active skills. "
                    "Visit the platform to add skills to your agent.",
                    parse_mode="Markdown"
                )
                return
            
            # Format skills message
            skills_text = "🎯 *Active Skills*\n\n"
            
            for user_skill, skill in user_skills:
                proficiency_emoji = "⭐" * user_skill.proficiency_level
                skills_text += f"• {skill.name} {proficiency_emoji}\n"
                skills_text += f"  {skill.description}\n\n"
            
            skills_text += f"Total: {len(user_skills)} active skills"
            
            await update.message.reply_text(
                skills_text,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error getting skills: {str(e)}")
            await update.message.reply_text("Sorry, couldn't get skills. Please try again.")
    
    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command."""
        keyboard = [
            [InlineKeyboardButton("🔊 Voice Settings", callback_data="settings_voice")],
            [InlineKeyboardButton("💬 Chat Settings", callback_data="settings_chat")],
            [InlineKeyboardButton("ℹ️ About", callback_data="settings_about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚙️ *Settings*\n\n"
            "Choose a setting category:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        try:
            # Get platform user
            platform_user = await self.auth_manager.get_user_by_telegram_id(user_id)
            if not platform_user:
                await update.message.reply_text(
                    "❌ Account not linked. Use /link to connect your account."
                )
                return
            
            # Show typing indicator
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing"
            )
            
            # Process message with agent
            response = await self._process_message(
                user_id=platform_user.id,
                telegram_chat_id=update.effective_chat.id,
                message_content=message_text,
                message_type="text"
            )
            
            # Send response
            await self._send_agent_response(update, response)
            
        except Exception as e:
            logger.error(f"Error processing text message: {str(e)}")
            await update.message.reply_text(
                "Sorry, I encountered an error processing your message. Please try again."
            )
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages."""
        user_id = update.effective_user.id
        voice_file = update.message.voice
        
        try:
            # Get platform user
            platform_user = await self.auth_manager.get_user_by_telegram_id(user_id)
            if not platform_user:
                await update.message.reply_text(
                    "❌ Account not linked. Use /link to connect your account."
                )
                return
            
            # Show processing indicator
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="record_voice"
            )
            
            # Download voice file
            voice_file_path = await self._download_voice_file(voice_file)
            
            try:
                # Transcribe voice to text
                transcribed_text = await self.voice_processor.transcribe_audio(voice_file_path)
                
                if not transcribed_text:
                    await update.message.reply_text(
                        "🎤 Sorry, I couldn't understand the audio. Please try again."
                    )
                    return
                
                # Show typing indicator
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id,
                    action="typing"
                )
                
                # Process transcribed text with agent
                response = await self._process_message(
                    user_id=platform_user.id,
                    telegram_chat_id=update.effective_chat.id,
                    message_content=transcribed_text,
                    message_type="voice"
                )
                
                # Send response with voice note indicator
                response_text = f"🎤 *Voice message:* \"{transcribed_text}\"\n\n{response['response']}"
                await self._send_agent_response(update, response, response_text)
                
            finally:
                # Clean up temporary file
                if os.path.exists(voice_file_path):
                    os.remove(voice_file_path)
            
        except Exception as e:
            logger.error(f"Error processing voice message: {str(e)}")
            await update.message.reply_text(
                "Sorry, I encountered an error processing your voice message. Please try again."
            )
    
    async def handle_audio_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio files."""
        # Similar to voice message handling
        await self.handle_voice_message(update, context)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "settings_voice":
            await self._handle_voice_settings(query)
        elif data == "settings_chat":
            await self._handle_chat_settings(query)
        elif data == "settings_about":
            await self._handle_about_settings(query)
    
    async def _process_message(
        self,
        user_id: str,
        telegram_chat_id: int,
        message_content: str,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """Process message through Agent Runtime."""
        try:
            # Get or create conversation
            conversation_id = await self._get_or_create_conversation(user_id, telegram_chat_id)
            
            # Process with agent runtime
            response = await self.agent_runtime.process_message(
                user_id=user_id,
                conversation_id=conversation_id,
                message_content=message_content,
                channel_type="telegram"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise TelegramBotError(f"Failed to process message: {str(e)}")
    
    async def _get_or_create_conversation(self, user_id: str, telegram_chat_id: int) -> str:
        """Get or create conversation for Telegram chat."""
        with get_db() as db:
            # Look for existing conversation
            conversation = db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.channel_type == "telegram",
                Conversation.channel_id == str(telegram_chat_id),
                Conversation.deleted_at.is_(None)
            ).first()
            
            if not conversation:
                # Create new conversation
                conversation = Conversation(
                    user_id=user_id,
                    channel_type="telegram",
                    channel_id=str(telegram_chat_id),
                    title=f"Telegram Chat {telegram_chat_id}",
                    metadata={"telegram_chat_id": telegram_chat_id}
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
            
            return str(conversation.id)
    
    async def _download_voice_file(self, voice_file) -> str:
        """Download voice file from Telegram."""
        try:
            # Get file info
            file_info = await self.bot.get_file(voice_file.file_id)
            
            # Download to temporary file
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"voice_{voice_file.file_id}.ogg")
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(await file_info.download_as_bytearray())
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading voice file: {str(e)}")
            raise VoiceProcessingError(f"Failed to download voice file: {str(e)}")
    
    async def _send_agent_response(self, update: Update, response: Dict[str, Any], custom_text: Optional[str] = None):
        """Send agent response to user."""
        response_text = custom_text or response['response']
        
        # Handle long messages
        if len(response_text) > 4096:  # Telegram message limit
            # Split message
            parts = [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]
            
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    await update.message.reply_text(part)
                else:
                    await update.message.reply_text(part + "...")
        else:
            await update.message.reply_text(response_text)
    
    async def _send_welcome_message(self, update: Update, linked: bool = False):
        """Send welcome message."""
        if linked:
            welcome_text = """
🎉 *Welcome Back!*

Your AI agent is ready to chat!

Just send me a message and I'll respond with your personalized AI agent.

Use /help to see all available commands.
            """
        else:
            welcome_text = """
🤖 *Welcome to AI Agent Bot!*

I'm your personal AI assistant. To get started:

1. Link your account with /link
2. Start chatting with your agent

Use /help to see all commands.
            """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown"
        )
    
    async def _send_link_instructions(self, update: Update):
        """Send account linking instructions."""
        keyboard = [[InlineKeyboardButton("🔗 Link Account", callback_data="link_account")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔗 *Link Your Account*\n\n"
            "To use your personal AI agent, you need to link your Telegram account.\n\n"
            "Use /link to get your unique link token.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    async def _handle_voice_settings(self, query):
        """Handle voice settings callback."""
        await query.edit_message_text(
            "🔊 *Voice Settings*\n\n"
            "Voice recognition is currently enabled.\n"
            "Voice settings can be configured on the platform.",
            parse_mode="Markdown"
        )
    
    async def _handle_chat_settings(self, query):
        """Handle chat settings callback."""
        await query.edit_message_text(
            "💬 *Chat Settings*\n\n"
            "Chat settings can be configured on the platform:\n"
            "• Response style\n"
            "• Active skills\n"
            "• Agent personality",
            parse_mode="Markdown"
        )
    
    async def _handle_about_settings(self, query):
        """Handle about settings callback."""
        await query.edit_message_text(
            "ℹ️ *About*\n\n"
            "AI Agent Bot v1.0\n\n"
            "Your personal AI assistant, powered by advanced language models "
            "and customizable skills.\n\n"
            "Visit our platform for more features!",
            parse_mode="Markdown"
        )
    
    async def start_webhook(self, webhook_url: str):
        """Start the bot with webhook."""
        await self.application.bot.set_webhook(url=webhook_url)
        await self.application.run_webhook(
            listen_url="0.0.0.0",
            port=8443,
            secret_token="your-secret-token"
        )
    
    async def start_polling(self):
        """Start the bot with polling."""
        await self.application.run_polling()
    
    def get_user_state(self, user_id: int) -> Dict[str, Any]:
        """Get user state."""
        return self._user_states.get(user_id, {})
    
    def set_user_state(self, user_id: int, state: Dict[str, Any]):
        """Set user state."""
        self._user_states[user_id] = state
    
    def clear_user_state(self, user_id: int):
        """Clear user state."""
        self._user_states.pop(user_id, None)
