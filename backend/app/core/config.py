from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = "AIgent Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    
    database_url: str = "sqlite:///./aigent.db"
    
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30 * 24 * 60
    
    allowed_origins: List[str] = ["http://localhost:3000", "https://*.onrender.com"]
    
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
    
    def __init__(self):
        self.app_name = os.getenv("APP_NAME", self.app_name)
        self.app_version = os.getenv("APP_VERSION", self.app_version)
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        self.database_url = os.getenv("DATABASE_URL", self.database_url)
        self.secret_key = os.getenv("SECRET_KEY", self.secret_key)
        self.algorithm = os.getenv("ALGORITHM", self.algorithm)
        
        expires = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
        if expires:
            self.access_token_expire_minutes = int(expires)
        
        origins = os.getenv("ALLOWED_ORIGINS")
        if origins:
            self.allowed_origins = [o.strip() for o in origins.strip('[]"').split(',')]
        
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.default_model = os.getenv("DEFAULT_MODEL", self.default_model)
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.redis_url = os.getenv("REDIS_URL")
        self.upload_dir = os.getenv("UPLOAD_DIR", self.upload_dir)
        
        max_size = os.getenv("MAX_FILE_SIZE")
        if max_size:
            self.max_file_size = int(max_size)


settings = Settings()
