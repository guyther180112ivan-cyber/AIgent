"""
Scheduler service for executing scheduled tasks.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import ScheduledTask
from .schemas import ScheduleType, ActionType, TaskExecutionResult

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for managing and executing scheduled tasks.
    
    Runs as a background task and periodically checks for tasks
    that need to be executed.
    """
    
    def __init__(self, db: Session, telegram_bot=None):
        self.db = db
        self.telegram_bot = telegram_bot
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.check_interval = 60  # Check every 60 seconds
        
    async def start(self):
        """Start the scheduler service."""
        if self.is_running:
            logger.warning("Scheduler service is already running")
            return
            
        self.is_running = True
        self._task = asyncio.create_task(self._run_scheduler_loop())
        logger.info("Scheduler service started")
        
    async def stop(self):
        """Stop the scheduler service."""
        if not self.is_running:
            return
            
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler service stopped")
        
    async def _run_scheduler_loop(self):
        """Main scheduler loop."""
        while self.is_running:
            try:
                await self._check_and_execute_tasks()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                
            await asyncio.sleep(self.check_interval)
            
    async def _check_and_execute_tasks(self):
        """Check for due tasks and execute them."""
        now = datetime.utcnow()
        
        # Find tasks that are due
        tasks = self.db.query(ScheduledTask).filter(
            and_(
                ScheduledTask.is_active == True,
                ScheduledTask.is_completed == False,
                or_(
                    ScheduledTask.next_run_at <= now,
                    and_(
                        ScheduledTask.next_run_at == None,
                        ScheduledTask.scheduled_at <= now
                    )
                )
            )
        ).all()
        
        for task in tasks:
            try:
                await self._execute_task(task)
            except Exception as e:
                logger.error(f"Error executing task {task.id}: {e}")
                
    async def _execute_task(self, task: ScheduledTask) -> TaskExecutionResult:
        """Execute a single scheduled task."""
        logger.info(f"Executing task {task.id}: {task.name}")
        
        result = TaskExecutionResult(
            task_id=str(task.id),
            success=False,
            message="",
            executed_at=datetime.utcnow()
        )
        
        try:
            if task.action_type == ActionType.TELEGRAM_MESSAGE.value:
                await self._send_telegram_message(task)
                result.success = True
                result.message = "Message sent successfully"
            elif task.action_type == ActionType.WEBHOOK.value:
                await self._call_webhook(task)
                result.success = True
                result.message = "Webhook called successfully"
            elif task.action_type == ActionType.AGENT_ACTION.value:
                await self._execute_agent_action(task)
                result.success = True
                result.message = "Agent action executed successfully"
            else:
                result.message = f"Unknown action type: {task.action_type}"
                
        except Exception as e:
            result.success = False
            result.message = f"Execution failed: {str(e)}"
            result.error = str(e)
            logger.error(f"Task execution failed: {e}")
            
        # Update task status
        task.last_run_at = datetime.utcnow()
        task.run_count += 1
        
        # Check if task should be completed
        if task.max_runs and task.run_count >= task.max_runs:
            task.is_completed = True
            task.is_active = False
        else:
            # Calculate next run time
            task.next_run_at = self._calculate_next_run(task)
            
        self.db.commit()
        
        return result
        
    async def _send_telegram_message(self, task: ScheduledTask):
        """Send a message via Telegram."""
        if not task.target_id:
            raise ValueError("No target_id specified for Telegram message")
            
        # Import telegram_bot here to avoid circular imports
        try:
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            import telegram_bot
            
            # Use the telegram bot to send message
            success = await telegram_bot.send_message(
                chat_id=int(task.target_id),
                text=task.message_text or "Напоминание от AIgent Bot ⏰"
            )
            
            if not success:
                raise Exception("Failed to send Telegram message")
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            raise
        
    async def _call_webhook(self, task: ScheduledTask):
        """Call a webhook URL."""
        if not task.action_payload:
            raise ValueError("No action_payload specified for webhook")
            
        payload = json.loads(task.action_payload)
        url = payload.get("url")
        method = payload.get("method", "POST")
        headers = payload.get("headers", {})
        data = payload.get("data", {})
        
        if not url:
            raise ValueError("No URL specified in action_payload")
            
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            
    async def _execute_agent_action(self, task: ScheduledTask):
        """Execute an action through an agent."""
        # This would integrate with the agent runtime
        # For now, just log the action
        logger.info(f"Agent action for task {task.id}: {task.message_text}")
        
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """Calculate the next run time for a recurring task."""
        if task.schedule_type == ScheduleType.ONCE.value:
            return None  # One-time tasks don't have next run
            
        now = datetime.utcnow()
        
        if task.schedule_type == ScheduleType.HOURLY.value:
            return now + timedelta(hours=1)
        elif task.schedule_type == ScheduleType.DAILY.value:
            return now + timedelta(days=1)
        elif task.schedule_type == ScheduleType.WEEKLY.value:
            return now + timedelta(weeks=1)
        elif task.schedule_type == ScheduleType.MONTHLY.value:
            # Approximate month
            return now + timedelta(days=30)
        elif task.schedule_type == ScheduleType.CRON.value and task.cron_expression:
            # Simple cron parsing (could be enhanced with croniter library)
            # For now, just add 1 hour as default
            return now + timedelta(hours=1)
        elif task.interval_minutes:
            return now + timedelta(minutes=task.interval_minutes)
            
        return None
        
    # Public API methods
    
    def create_task(self, task_data: dict, user_id: str) -> ScheduledTask:
        """Create a new scheduled task."""
        task = ScheduledTask(
            user_id=user_id,
            **task_data
        )
        
        # Calculate initial next_run_at
        if task.schedule_type != ScheduleType.ONCE.value:
            task.next_run_at = self._calculate_next_run(task)
        else:
            task.next_run_at = task.scheduled_at
            
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
        
    def get_task(self, task_id: str, user_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID."""
        return self.db.query(ScheduledTask).filter(
            and_(
                ScheduledTask.id == task_id,
                ScheduledTask.user_id == user_id
            )
        ).first()
        
    def get_user_tasks(self, user_id: str, active_only: bool = False) -> List[ScheduledTask]:
        """Get all tasks for a user."""
        query = self.db.query(ScheduledTask).filter(ScheduledTask.user_id == user_id)
        
        if active_only:
            query = query.filter(ScheduledTask.is_active == True)
            
        return query.order_by(ScheduledTask.created_at.desc()).all()
        
    def update_task(self, task_id: str, user_id: str, updates: dict) -> Optional[ScheduledTask]:
        """Update a scheduled task."""
        task = self.get_task(task_id, user_id)
        if not task:
            return None
            
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
                
        # Recalculate next_run_at if schedule changed
        if any(key in updates for key in ["schedule_type", "scheduled_at", "cron_expression", "interval_minutes"]):
            task.next_run_at = self._calculate_next_run(task)
            
        task.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        
        return task
        
    def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a scheduled task."""
        task = self.get_task(task_id, user_id)
        if not task:
            return False
            
        self.db.delete(task)
        self.db.commit()
        return True
        
    def pause_task(self, task_id: str, user_id: str) -> Optional[ScheduledTask]:
        """Pause a scheduled task."""
        return self.update_task(task_id, user_id, {"is_active": False})
        
    def resume_task(self, task_id: str, user_id: str) -> Optional[ScheduledTask]:
        """Resume a scheduled task."""
        task = self.get_task(task_id, user_id)
        if not task:
            return None
            
        task.is_active = True
        task.is_completed = False
        
        # Recalculate next run
        if task.schedule_type != ScheduleType.ONCE.value:
            task.next_run_at = self._calculate_next_run(task)
            
        self.db.commit()
        self.db.refresh(task)
        return task


# Global instance for dependency injection
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> Optional[SchedulerService]:
    """Get the global scheduler service instance."""
    return _scheduler_service


def set_scheduler_service(service: SchedulerService):
    """Set the global scheduler service instance."""
    global _scheduler_service
    _scheduler_service = service
