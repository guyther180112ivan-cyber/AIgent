from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid


class Skill(Base):
    """Base skill model representing available skills in the system."""
    
    __tablename__ = "skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    system_prompt_template = Column(Text, nullable=False)
    default_config = Column(JSON, nullable=False, default={})
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=False, default=[])
    is_builtin = Column(Boolean, default=False, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # Higher number = higher priority
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user_skills = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")


class UserSkill(Base):
    """Junction table for user-skill relationships with configuration."""
    
    __tablename__ = "user_skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    config = Column(JSON, nullable=False, default={})
    is_enabled = Column(Boolean, default=True, nullable=False)
    proficiency_level = Column(Integer, default=1, nullable=False)  # 1-5 scale
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    custom_priority = Column(Integer, nullable=True)  # User-defined priority override
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")
    
    # Unique constraint
    __table_args__ = (
        {"schema": None},
    )


class SkillCategory(Base):
    """Skill categories for organization."""
    
    __tablename__ = "skill_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Icon name
    color = Column(String(7), nullable=True)  # Hex color
    parent_id = Column(UUID(as_uuid=True), ForeignKey("skill_categories.id"), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("SkillCategory", remote_side=[id])
    children = relationship("SkillCategory", back_populates="parent")


class SkillTemplate(Base):
    """Templates for creating new skills."""
    
    __tablename__ = "skill_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    system_prompt_template = Column(Text, nullable=False)
    config_schema = Column(JSON, nullable=False, default={})  # JSON schema for configuration
    category = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=False, default=[])
    is_public = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    rating = Column(Integer, default=0, nullable=False)  # 1-5 scale
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by_user = relationship("User")


class SkillUsageLog(Base):
    """Log of skill usage for analytics."""
    
    __tablename__ = "skill_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    execution_time_ms = Column(Integer, nullable=False)
    tokens_generated = Column(Integer, nullable=False)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    context = Column(JSON, nullable=False, default={})  # Additional context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    skill = relationship("Skill")
    conversation = relationship("Conversation")
    message = relationship("Message")
