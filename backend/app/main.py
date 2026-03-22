from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
import sys
import os

from .core.config import settings
from .core.database import engine, Base, SessionLocal
from .api import auth, agents, skills, tools, conversations, chat
from .scheduler import router as scheduler_router, SchedulerService, set_scheduler_service
import uvicorn

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Global variables to store background tasks
telegram_bot_task = None
scheduler_task = None
scheduler_service = None


async def run_telegram_bot():
    """Run Telegram bot as background task"""
    try:
        import telegram_bot
        logger.info("Starting Telegram bot...")
        await telegram_bot.main()
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global telegram_bot_task, scheduler_task, scheduler_service
    
    # Startup
    logger.info("Starting AIgent Platform...")
    
    # Start Telegram bot in background task
    telegram_bot_task = asyncio.create_task(run_telegram_bot())
    logger.info("Telegram bot task created")
    
    # Start Scheduler service
    db = SessionLocal()
    try:
        scheduler_service = SchedulerService(db)
        await scheduler_service.start()
        set_scheduler_service(scheduler_service)
        logger.info("Scheduler service started")
    except Exception as e:
        logger.error(f"Failed to start scheduler service: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AIgent Platform...")
    
    # Stop Telegram bot
    if telegram_bot_task and not telegram_bot_task.done():
        telegram_bot_task.cancel()
        try:
            await telegram_bot_task
        except asyncio.CancelledError:
            pass
    logger.info("Telegram bot stopped")
    
    # Stop Scheduler service
    if scheduler_service:
        await scheduler_service.stop()
        logger.info("Scheduler service stopped")
    
    db.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["skills"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(scheduler_router)


@app.get("/")
async def root():
    return {
        "message": "AIgent Platform API",
        "version": settings.app_version,
        "telegram_bot": "running" if telegram_bot_task and not telegram_bot_task.done() else "stopped",
        "scheduler": "running" if scheduler_service and scheduler_service.is_running else "stopped"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "telegram_bot": "running" if telegram_bot_task and not telegram_bot_task.done() else "stopped",
        "scheduler": "running" if scheduler_service and scheduler_service.is_running else "stopped"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
