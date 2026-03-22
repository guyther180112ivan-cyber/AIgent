from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import os


class Settings(BaseSettings):
    app_name: str = "AIgent Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    
    database_url: str = "sqlite:///./aigent.db"
    
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30 * 24 * 60
    
    allowed_origins: Union[List[str], str] = ["http://localhost:3000", "https://*.onrender.com"]
    
    openrouter_api_key: Optional[str] = None
    default_model: str = "openrouter/free"
    
    telegram_bot_token: Optional[str] = None
    telegram_webhook_url: Optional[str] = None
    
    stt_provider: str = "openai"
    tts_provider: str = "openai"
    openai_api_key: Optional[str] = None
    
    redis_url: Optional[str] = None
    
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


settings = Settings()
