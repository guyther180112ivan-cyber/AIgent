import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from jose import JWTError, jwt

from .models import TelegramLink
from ..core.config import settings
from ..core.database import get_db
from ..models import User
from .exceptions import TelegramAuthError, UserNotLinkedError

logger = logging.getLogger(__name__)


class TelegramAuthManager:
    """
    Manages authentication and linking between Telegram users and platform users.
    """
    
    def __init__(self):
        self.link_token_expiry = timedelta(hours=24)
        self.secret_key = settings.secret_key
    
    async def generate_link_token(self, telegram_user_id: int) -> str:
        """
        Generate a link token for Telegram user to connect with platform account.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            Link token
        """
        try:
            # Generate secure token
            token_data = {
                "telegram_user_id": telegram_user_id,
                "exp": datetime.utcnow() + self.link_token_expiry,
                "iat": datetime.utcnow(),
                "type": "telegram_link"
            }
            
            token = jwt.encode(token_data, self.secret_key, algorithm=settings.algorithm)
            
            logger.info(f"Generated link token for Telegram user {telegram_user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error generating link token: {str(e)}")
            raise TelegramAuthError(f"Failed to generate link token: {str(e)}")
    
    async def verify_link_token(self, token: str) -> Optional[int]:
        """
        Verify link token and extract Telegram user ID.
        
        Args:
            token: Link token
            
        Returns:
            Telegram user ID or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[settings.algorithm])
            
            # Check token type
            if payload.get("type") != "telegram_link":
                logger.warning("Invalid token type")
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
                logger.warning("Link token expired")
                return None
            
            telegram_user_id = payload.get("telegram_user_id")
            if not telegram_user_id:
                logger.warning("No telegram_user_id in token")
                return None
            
            return telegram_user_id
            
        except JWTError as e:
            logger.warning(f"JWT error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying link token: {str(e)}")
            return None
    
    async def link_accounts(
        self,
        platform_user_id: str,
        telegram_user_id: int,
        telegram_username: Optional[str] = None,
        telegram_chat_id: Optional[int] = None
    ) -> bool:
        """
        Link platform user with Telegram user.
        
        Args:
            platform_user_id: Platform user UUID
            telegram_user_id: Telegram user ID
            telegram_username: Telegram username
            telegram_chat_id: Telegram chat ID
            
        Returns:
            True if successful
        """
        try:
            with get_db() as db:
                # Check if Telegram user is already linked
                existing_link = db.query(TelegramLink).filter(
                    TelegramLink.telegram_user_id == telegram_user_id,
                    TelegramLink.is_active == True
                ).first()
                
                if existing_link:
                    # Update existing link to new user
                    existing_link.is_active = False
                    existing_link.updated_at = datetime.utcnow()
                
                # Check if platform user already has Telegram link
                existing_platform_link = db.query(TelegramLink).filter(
                    TelegramLink.user_id == platform_user_id,
                    TelegramLink.is_active == True
                ).first()
                
                if existing_platform_link:
                    # Deactivate existing link
                    existing_platform_link.is_active = False
                    existing_platform_link.updated_at = datetime.utcnow()
                
                # Create new link
                new_link = TelegramLink(
                    user_id=platform_user_id,
                    telegram_user_id=telegram_user_id,
                    telegram_username=telegram_username,
                    telegram_chat_id=telegram_chat_id or telegram_user_id,  # Use user_id as chat_id for private messages
                    is_active=True
                )
                
                db.add(new_link)
                db.commit()
                
                logger.info(f"Linked platform user {platform_user_id} with Telegram user {telegram_user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error linking accounts: {str(e)}")
            db.rollback()
            raise TelegramAuthError(f"Failed to link accounts: {str(e)}")
    
    async def unlink_accounts(self, platform_user_id: str) -> bool:
        """
        Unlink platform user from Telegram.
        
        Args:
            platform_user_id: Platform user UUID
            
        Returns:
            True if successful
        """
        try:
            with get_db() as db:
                link = db.query(TelegramLink).filter(
                    TelegramLink.user_id == platform_user_id,
                    TelegramLink.is_active == True
                ).first()
                
                if link:
                    link.is_active = False
                    link.updated_at = datetime.utcnow()
                    db.commit()
                    
                    logger.info(f"Unlinked platform user {platform_user_id} from Telegram")
                    return True
                else:
                    logger.warning(f"No active link found for platform user {platform_user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error unlinking accounts: {str(e)}")
            db.rollback()
            raise TelegramAuthError(f"Failed to unlink accounts: {str(e)}")
    
    async def unlink_telegram_user(self, telegram_user_id: int) -> bool:
        """
        Unlink Telegram user from platform.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            True if successful
        """
        try:
            with get_db() as db:
                link = db.query(TelegramLink).filter(
                    TelegramLink.telegram_user_id == telegram_user_id,
                    TelegramLink.is_active == True
                ).first()
                
                if link:
                    link.is_active = False
                    link.updated_at = datetime.utcnow()
                    db.commit()
                    
                    logger.info(f"Unlinked Telegram user {telegram_user_id} from platform")
                    return True
                else:
                    logger.warning(f"No active link found for Telegram user {telegram_user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error unlinking Telegram user: {str(e)}")
            db.rollback()
            raise TelegramAuthError(f"Failed to unlink Telegram user: {str(e)}")
    
    async def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """
        Get platform user by Telegram user ID.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            Platform user or None if not linked
        """
        try:
            with get_db() as db:
                link = db.query(TelegramLink).filter(
                    TelegramLink.telegram_user_id == telegram_user_id,
                    TelegramLink.is_active == True
                ).first()
                
                if link:
                    user = db.query(User).filter(
                        User.id == link.user_id,
                        User.deleted_at.is_(None),
                        User.is_active == True
                    ).first()
                    return user
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by Telegram ID: {str(e)}")
            return None
    
    async def get_telegram_link_by_user(self, platform_user_id: str) -> Optional[TelegramLink]:
        """
        Get Telegram link by platform user ID.
        
        Args:
            platform_user_id: Platform user UUID
            
        Returns:
            Telegram link or None if not linked
        """
        try:
            with get_db() as db:
                link = db.query(TelegramLink).filter(
                    TelegramLink.user_id == platform_user_id,
                    TelegramLink.is_active == True
                ).first()
                
                return link
                
        except Exception as e:
            logger.error(f"Error getting Telegram link: {str(e)}")
            return None
    
    async def is_user_linked(self, platform_user_id: str) -> bool:
        """
        Check if platform user is linked to Telegram.
        
        Args:
            platform_user_id: Platform user UUID
            
        Returns:
            True if linked
        """
        link = await self.get_telegram_link_by_user(platform_user_id)
        return link is not None
    
    async def is_telegram_user_linked(self, telegram_user_id: int) -> bool:
        """
        Check if Telegram user is linked to platform.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            True if linked
        """
        user = await self.get_user_by_telegram_id(telegram_user_id)
        return user is not None
    
    async def update_telegram_info(
        self,
        platform_user_id: str,
        telegram_username: Optional[str] = None,
        telegram_chat_id: Optional[int] = None
    ) -> bool:
        """
        Update Telegram information for linked account.
        
        Args:
            platform_user_id: Platform user UUID
            telegram_username: New Telegram username
            telegram_chat_id: New Telegram chat ID
            
        Returns:
            True if successful
        """
        try:
            with get_db() as db:
                link = db.query(TelegramLink).filter(
                    TelegramLink.user_id == platform_user_id,
                    TelegramLink.is_active == True
                ).first()
                
                if link:
                    if telegram_username is not None:
                        link.telegram_username = telegram_username
                    if telegram_chat_id is not None:
                        link.telegram_chat_id = telegram_chat_id
                    
                    link.updated_at = datetime.utcnow()
                    db.commit()
                    
                    logger.info(f"Updated Telegram info for platform user {platform_user_id}")
                    return True
                else:
                    logger.warning(f"No active link found for platform user {platform_user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating Telegram info: {str(e)}")
            db.rollback()
            raise TelegramAuthError(f"Failed to update Telegram info: {str(e)}")
    
    async def get_linked_users_count(self) -> int:
        """
        Get count of linked users.
        
        Returns:
            Number of active links
        """
        try:
            with get_db() as db:
                count = db.query(TelegramLink).filter(
                    TelegramLink.is_active == True
                ).count()
                
                return count
                
        except Exception as e:
            logger.error(f"Error getting linked users count: {str(e)}")
            return 0
    
    async def get_user_link_history(self, platform_user_id: str) -> list:
        """
        Get link history for platform user.
        
        Args:
            platform_user_id: Platform user UUID
            
        Returns:
            List of link history
        """
        try:
            with get_db() as db:
                links = db.query(TelegramLink).filter(
                    TelegramLink.user_id == platform_user_id
                ).order_by(TelegramLink.created_at.desc()).all()
                
                history = []
                for link in links:
                    history.append({
                        "telegram_user_id": link.telegram_user_id,
                        "telegram_username": link.telegram_username,
                        "is_active": link.is_active,
                        "created_at": link.created_at.isoformat(),
                        "updated_at": link.updated_at.isoformat() if link.updated_at else None
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting link history: {str(e)}")
            return []
    
    async def cleanup_expired_links(self) -> int:
        """
        Clean up expired/inactive links (maintenance task).
        
        Returns:
            Number of cleaned up links
        """
        try:
            with get_db() as db:
                # Find links inactive for more than 30 days
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                expired_links = db.query(TelegramLink).filter(
                    TelegramLink.is_active == False,
                    TelegramLink.updated_at < cutoff_date
                ).all()
                
                count = len(expired_links)
                
                for link in expired_links:
                    db.delete(link)
                
                db.commit()
                
                if count > 0:
                    logger.info(f"Cleaned up {count} expired Telegram links")
                
                return count
                
        except Exception as e:
            logger.error(f"Error cleaning up expired links: {str(e)}")
            return 0
