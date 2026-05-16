"""
Pydantic schemas for the scheduler module.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, validator


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
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    action_type: ActionType = Field(default=ActionType.TELEGRAM_MESSAGE)
    schedule_type: ScheduleType = Field(default=ScheduleType.ONCE)
    
    scheduled_at: Optional[datetime] = Field(None)
    cron_expression: Optional[str] = Field(None, max_length=100)
    interval_minutes: Optional[int] = Field(None, ge=1)
    
    message_text: Optional[str] = Field(None)
    action_payload: Optional[str] = Field(None)
    
    target_id: Optional[str] = Field(None, max_length=100)
    target_type: TargetType = Field(default=TargetType.TELEGRAM)
    
    is_active: bool = Field(default=True)
    max_runs: Optional[int] = Field(None, ge=1)

    @validator('action_type', 'schedule_type', 'target_type', pre=True)
    def parse_enum(cls, v):
        """Convert string values to enum."""
        if isinstance(v, str):
            if v == 'action_type' and hasattr(ActionType, v.upper()):
                return ActionType[v.upper()]
            if 'schedule' in str(cls.__fields__.keys()) and hasattr(ScheduleType, v.upper()):
                return ScheduleType[v.upper()]
            if 'target' in str(cls.__fields__.keys()) and hasattr(TargetType, v.upper()):
                return TargetType[v.upper()]
        return v

    @validator('scheduled_at', pre=True)
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
    agent_id: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Утреннее приветствие",
                "action_type": "telegram_message",
                "schedule_type": "daily",
                "scheduled_at": "2026-03-08T08:00:00",
                "message_text": "Доброе утро!",
                "target_id": "123456789",
                "target_type": "telegram",
                "is_active": True,
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
    
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    is_completed: bool = False
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @validator('id', 'user_id', pre=True)
    def convert_uuid(cls, v):
        """Convert UUID to string."""
        if hasattr(v, '__str__'):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class ScheduledTaskList(BaseModel):
    """Schema for list of scheduled tasks."""
    items: List[ScheduledTaskResponse]
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
    timezone: Optional[str] = Field(default="Europe/Moscow")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "завтра в 3 утра",
                "timezone": "Europe/Moscow"
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
