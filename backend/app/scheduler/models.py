"""
Database models for the scheduler module.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship

from ..core.database import Base, GUID


class ScheduledTask(Base):
    """
    Model for scheduled tasks.
    
    Stores information about tasks that should be executed
    at specific times or on recurring schedules.
    """
    
    __tablename__ = "scheduled_tasks"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(GUID(), ForeignKey("agents.id"), nullable=True, index=True)
    
    # Task information
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    action_type = Column(String(50), nullable=False, default="telegram_message")
    # Possible values: telegram_message, email, webhook, agent_action
    
    # Scheduling information
    schedule_type = Column(String(20), nullable=False, default="once")
    # Possible values: once, hourly, daily, weekly, monthly, cron
    
    # When to run (for one-time tasks)
    scheduled_at = Column(DateTime, nullable=True)
    
    # Cron expression (for recurring tasks)
    cron_expression = Column(String(100), nullable=True)
    
    # Recurring task settings
    interval_minutes = Column(Integer, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    
    # Task content
    message_text = Column(Text, nullable=True)
    action_payload = Column(Text, nullable=True)  # JSON string with additional data
    
    # Target information (e.g., telegram chat_id)
    target_id = Column(String(100), nullable=True)
    target_type = Column(String(50), nullable=True, default="telegram")
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_completed = Column(Boolean, default=False)
    run_count = Column(Integer, default=0)
    max_runs = Column(Integer, nullable=True)  # null = unlimited
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="scheduled_tasks")
    agent = relationship("Agent", back_populates="scheduled_tasks")
    
    def __repr__(self):
        return f"<ScheduledTask(id={self.id}, name={self.name}, type={self.schedule_type})>"
    
    def to_dict(self):
        """Convert task to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "name": self.name,
            "description": self.description,
            "action_type": self.action_type,
            "schedule_type": self.schedule_type,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "cron_expression": self.cron_expression,
            "interval_minutes": self.interval_minutes,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "message_text": self.message_text,
            "action_payload": self.action_payload,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "run_count": self.run_count,
            "max_runs": self.max_runs,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
