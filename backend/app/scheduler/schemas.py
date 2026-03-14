"""
Pydantic schemas for the scheduler module.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ScheduleType(str, Enum):
    """Types of scheduling."""
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


class ActionType(str, Enum):
    """Types of actions that can be scheduled."""
    TELEGRAM_MESSAGE = "telegram_message"
    EMAIL = "email"
    WEBHOOK = "webhook"
    AGENT_ACTION = "agent_action"


class TargetType(str, Enum):
    """Types of targets for scheduled actions."""
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"


class ScheduledTaskBase(BaseModel):
    """Base schema for scheduled tasks."""
    name: str = Field(..., min_length=1, max_length=200, description="Task name")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    action_type: ActionType = Field(default=ActionType.TELEGRAM_MESSAGE, description="Type of action")
    schedule_type: ScheduleType = Field(default=ScheduleType.ONCE, description="Type of scheduling")
    
    # Scheduling
    scheduled_at: Optional[datetime] = Field(None, description="When to run (for one-time tasks)")
    cron_expression: Optional[str] = Field(None, max_length=100, description="Cron expression for recurring tasks")
    interval_minutes: Optional[int] = Field(None, ge=1, description="Interval in minutes for recurring tasks")
    
    # Task content
    message_text: Optional[str] = Field(None, description="Message text to send")
    action_payload: Optional[str] = Field(None, description="JSON string with additional action data")
    
    # Target
    target_id: Optional[str] = Field(None, max_length=100, description="Target ID (e.g., Telegram chat_id)")
    target_type: TargetType = Field(default=TargetType.TELEGRAM, description="Type of target")
    
    # Limits
    is_active: bool = Field(default=True, description="Whether the task is active")
    max_runs: Optional[int] = Field(None, ge=1, description="Maximum number of runs (null = unlimited)")

    @field_validator('action_type', 'schedule_type', 'target_type', mode='before')
    @classmethod
    def parse_enum_from_string(cls, v):
        """Convert string values to enum."""
        if isinstance(v, str):
            # Try to find matching enum value
            if 'action_type' in cls.__fields__ and hasattr(ActionType, v.upper()):
                return ActionType[v.upper()]
            if 'schedule_type' in cls.__fields__ and hasattr(ScheduleType, v.upper()):
                return ScheduleType[v.upper()]
            if 'target_type' in cls.__fields__ and hasattr(TargetType, v.upper()):
                return TargetType[v.upper()]
        return v

    @field_validator('scheduled_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from string."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except:
                try:
                    return datetime.strptime(v, '%Y-%m-%dT%H:%M')
                except:
                    pass
        return v


class ScheduledTaskCreate(ScheduledTaskBase):
    """Schema for creating a scheduled task."""
    agent_id: Optional[str] = Field(None, description="Optional agent ID to use for the task")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Утреннее приветствие",
                "description": "Отправляет доброе утро каждый день в 8:00",
                "action_type": "telegram_message",
                "schedule_type": "daily",
                "scheduled_at": "2026-03-08T08:00:00",
                "message_text": "Доброе утро! ☀️ Начнем продуктивный день!",
                "target_id": "123456789",
                "target_type": "telegram",
                "is_active": True,
            }
        }
    }


class ScheduledTaskUpdate(BaseModel):
    """Schema for updating a scheduled task."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    message_text: Optional[str] = None
    action_payload: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    cron_expression: Optional[str] = Field(None, max_length=100)
    interval_minutes: Optional[int] = Field(None, ge=1)
    max_runs: Optional[int] = Field(None, ge=1)


class ScheduledTaskResponse(ScheduledTaskBase):
    """Schema for scheduled task response."""
    id: str
    user_id: str
    agent_id: Optional[str] = None
    
    # Runtime info
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    is_completed: bool = False
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @field_validator('id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string."""
        if hasattr(v, '__str__'):
            return str(v)
        return v
    
    model_config = {"from_attributes": True}


class ScheduledTaskList(BaseModel):
    """Schema for list of scheduled tasks."""
    items: list[ScheduledTaskResponse]
    total: int


class TaskExecutionResult(BaseModel):
    """Schema for task execution result."""
    task_id: str
    success: bool
    message: str
    executed_at: datetime
    error: Optional[str] = None


class ScheduleParseRequest(BaseModel):
    """Request to parse natural language schedule."""
    text: str = Field(..., description="Natural language description of schedule")
    timezone: Optional[str] = Field(default="Europe/Moscow", description="User timezone")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "завтра в 3 утра",
                "timezone": "Europe/Moscow"
            }
        }
    }


class ScheduleParseResponse(BaseModel):
    """Response with parsed schedule information."""
    success: bool
    scheduled_at: Optional[datetime] = None
    schedule_type: Optional[ScheduleType] = None
    cron_expression: Optional[str] = None
    interval_minutes: Optional[int] = None
    description: Optional[str] = None
    error: Optional[str] = None
