from pydantic import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # App
    app_name: str = "AIgent Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database (SQLite by default for easy deployment)
    database_url: str = "sqlite:///./aigent.db"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30 * 24 * 60  # 30 days
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "https://*.onrender.com"]
    
    # LLM
    openrouter_api_key: Optional[str] = None
    default_model: str = "openrouter/free"
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_webhook_url: Optional[str] = None
    
    # Voice
    stt_provider: str = "openai"
    tts_provider: str = "openai"
    openai_api_key: Optional[str] = None
    
    # Redis (optional)
    redis_url: Optional[str] = None
    
    # File storage
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
