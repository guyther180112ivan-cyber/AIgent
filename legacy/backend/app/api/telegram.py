from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..core.database import get_db
from ..core.config import settings
from ..telegram import TelegramBotHandler, TelegramAuthError
from ..runtime.agent_runtime import AgentRuntime
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Global bot handler instance (will be initialized on startup)
bot_handler: TelegramBotHandler = None


def initialize_bot(agent_runtime: AgentRuntime):
    """Initialize the Telegram bot handler."""
    global bot_handler
    
    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not configured")
        return
    
    try:
        bot_handler = TelegramBotHandler(
            bot_token=settings.telegram_bot_token,
            agent_runtime=agent_runtime
        )
        logger.info("Telegram bot handler initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {str(e)}")
        raise


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram webhook updates.
    """
    if not bot_handler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot not initialized"
        )
    
    try:
        # Get update data
        update_data = await request.json()
        logger.info(f"Received Telegram update: {update_data}")
        
        # Process update through bot handler
        import asyncio
        from telegram import Update
        from telegram.ext import Application
        
        # Create Update object from JSON
        update = Update.de_json(update_data, bot_handler.bot)
        
        # Process update
        await bot_handler.application.process_update(update)
        
        return Response(status_code=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


@router.post("/link")
async def link_telegram_account(
    token: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link Telegram account with platform account using link token.
    """
    try:
        if not bot_handler:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Telegram bot not initialized"
            )
        
        # Verify link token
        telegram_user_id = await bot_handler.auth_manager.verify_link_token(token)
        
        if not telegram_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired link token"
            )
        
        # Link accounts
        success = await bot_handler.auth_manager.link_accounts(
            platform_user_id=str(current_user.id),
            telegram_user_id=telegram_user_id
        )
        
        if success:
            return {"message": "Account linked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to link account"
            )
            
    except TelegramAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error linking Telegram account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link account"
        )


@router.post("/unlink")
async def unlink_telegram_account(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unlink Telegram account from platform account.
    """
    try:
        if not bot_handler:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Telegram bot not initialized"
            )
        
        # Unlink accounts
        success = await bot_handler.auth_manager.unlink_accounts(str(current_user.id))
        
        if success:
            return {"message": "Account unlinked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No linked Telegram account found"
            )
            
    except Exception as e:
        logger.error(f"Error unlinking Telegram account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink account"
        )


@router.get("/status")
async def get_telegram_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Telegram linking status for current user.
    """
    try:
        if not bot_handler:
            return {
                "linked": False,
                "message": "Telegram bot not available"
            }
        
        # Check if user is linked
        is_linked = await bot_handler.auth_manager.is_user_linked(str(current_user.id))
        
        if is_linked:
            link = await bot_handler.auth_manager.get_telegram_link_by_user(str(current_user.id))
            return {
                "linked": True,
                "telegram_user_id": link.telegram_user_id,
                "telegram_username": link.telegram_username,
                "linked_at": link.created_at.isoformat()
            }
        else:
            return {
                "linked": False,
                "message": "Account not linked"
            }
            
    except Exception as e:
        logger.error(f"Error getting Telegram status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Telegram status"
        )


@router.get("/link-token")
async def generate_link_token(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new link token for Telegram account linking.
    """
    try:
        if not bot_handler:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Telegram bot not initialized"
            )
        
        # Check if already linked
        is_linked = await bot_handler.auth_manager.is_user_linked(str(current_user.id))
        
        if is_linked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account already linked to Telegram"
            )
        
        # Generate link token
        token = await bot_handler.auth_manager.generate_link_token(0)  # Will be updated when user clicks link
        
        return {
            "link_token": token,
            "link_url": f"https://t.me/{bot_handler.bot.username}?start={token}"
        }
        
    except Exception as e:
        logger.error(f"Error generating link token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate link token"
        )


@router.get("/info")
async def get_bot_info():
    """
    Get Telegram bot information.
    """
    if not bot_handler:
        return {
            "available": False,
            "message": "Telegram bot not configured"
        }
    
    try:
        bot_info = await bot_handler.bot.get_me()
        return {
            "available": True,
            "bot_name": bot_info.username,
            "bot_id": bot_info.id,
            "can_join_groups": bot_info.can_join_groups,
            "can_read_all_group_messages": bot_info.can_read_all_group_messages,
            "supports_inline_queries": bot_info.supports_inline_queries
        }
    except Exception as e:
        logger.error(f"Error getting bot info: {str(e)}")
        return {
            "available": False,
            "error": str(e)
        }


@router.post("/test-webhook")
async def test_webhook():
    """
    Test webhook endpoint (for development).
    """
    return {"message": "Webhook endpoint is working"}
