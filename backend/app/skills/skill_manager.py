import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from .models import Skill, UserSkill, SkillCategory, SkillUsageLog
from .prompt_merger import PromptMerger
from .exceptions import (
    SkillNotFoundError,
    SkillAlreadyExistsError,
    SkillConfigurationError,
    SkillPermissionError
)

logger = logging.getLogger(__name__)


class SkillManager:
    """
    Manages skills for users including loading, enabling/disabling, and configuration.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.prompt_merger = PromptMerger()
        
        # Cache for user skills
        self._user_skills_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update: Dict[str, datetime] = {}
    
    async def get_user_skills(
        self,
        user_id: str,
        enabled_only: bool = True,
        include_builtin: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all skills for a user with their configurations.
        
        Args:
            user_id: User UUID
            enabled_only: Only return enabled skills
            include_builtin: Include built-in skills
            
        Returns:
            List of skill dictionaries with configurations
        """
        # Check cache first
        cache_key = f"{user_id}_{enabled_only}_{include_builtin}"
        if self._is_cache_valid(cache_key):
            return self._user_skills_cache[cache_key]
        
        try:
            # Build query
            query = self.db.query(UserSkill, Skill).join(Skill).filter(
                UserSkill.user_id == user_id,
                UserSkill.deleted_at.is_(None),
                Skill.deleted_at.is_(None),
                Skill.is_active == True
            )
            
            if enabled_only:
                query = query.filter(UserSkill.is_enabled == True)
            
            if not include_builtin:
                query = query.filter(Skill.is_builtin == False)
            
            # Execute query
            results = query.all()
            
            # Convert to skill dictionaries
            skills = []
            for user_skill, skill in results:
                skill_dict = {
                    "id": str(skill.id),
                    "user_skill_id": str(user_skill.id),
                    "name": skill.name,
                    "slug": skill.slug,
                    "description": skill.description,
                    "system_prompt_template": skill.system_prompt_template,
                    "config": user_skill.config,
                    "default_config": skill.default_config,
                    "is_enabled": user_skill.is_enabled,
                    "is_builtin": skill.is_builtin,
                    "category": skill.category,
                    "tags": skill.tags,
                    "priority": user_skill.custom_priority or skill.priority,
                    "proficiency_level": user_skill.proficiency_level,
                    "usage_count": user_skill.usage_count,
                    "last_used_at": user_skill.last_used_at.isoformat() if user_skill.last_used_at else None,
                    "created_at": user_skill.created_at.isoformat()
                }
                skills.append(skill_dict)
            
            # Sort by priority (descending) and then by name
            skills.sort(key=lambda x: (-x["priority"], x["name"]))
            
            # Cache the result
            self._user_skills_cache[cache_key] = skills
            self._last_cache_update[cache_key] = datetime.utcnow()
            
            return skills
            
        except Exception as e:
            logger.error(f"Error loading user skills for {user_id}: {str(e)}")
            raise SkillConfigurationError(f"Failed to load user skills: {str(e)}")
    
    async def enable_skill(
        self,
        user_id: str,
        skill_id: str,
        config: Optional[Dict[str, Any]] = None,
        proficiency_level: int = 1
    ) -> Dict[str, Any]:
        """
        Enable a skill for a user.
        
        Args:
            user_id: User UUID
            skill_id: Skill UUID
            config: Skill configuration
            proficiency_level: Proficiency level (1-5)
            
        Returns:
            Updated skill dictionary
        """
        try:
            # Check if skill exists
            skill = self.db.query(Skill).filter(
                Skill.id == skill_id,
                Skill.deleted_at.is_(None),
                Skill.is_active == True
            ).first()
            
            if not skill:
                raise SkillNotFoundError(f"Skill {skill_id} not found")
            
            # Check if user already has this skill
            user_skill = self.db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_id,
                UserSkill.deleted_at.is_(None)
            ).first()
            
            if user_skill:
                # Update existing user skill
                user_skill.is_enabled = True
                if config:
                    user_skill.config = config
                if proficiency_level:
                    user_skill.proficiency_level = max(1, min(5, proficiency_level))
                user_skill.updated_at = datetime.utcnow()
            else:
                # Create new user skill
                user_skill = UserSkill(
                    user_id=user_id,
                    skill_id=skill_id,
                    config=config or skill.default_config,
                    is_enabled=True,
                    proficiency_level=max(1, min(5, proficiency_level)
                )
                self.db.add(user_skill)
            
            self.db.commit()
            self.db.refresh(user_skill)
            
            # Invalidate cache
            self.invalidate_cache(user_id)
            
            # Return updated skill
            return await self._get_user_skill_dict(user_skill, skill)
            
        except Exception as e:
            logger.error(f"Error enabling skill {skill_id} for user {user_id}: {str(e)}")
            self.db.rollback()
            raise SkillConfigurationError(f"Failed to enable skill: {str(e)}")
    
    async def disable_skill(self, user_id: str, skill_id: str) -> bool:
        """
        Disable a skill for a user.
        
        Args:
            user_id: User UUID
            skill_id: Skill UUID
            
        Returns:
            True if successful
        """
        try:
            user_skill = self.db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_id,
                UserSkill.deleted_at.is_(None)
            ).first()
            
            if not user_skill:
                raise SkillNotFoundError(f"User skill {skill_id} not found")
            
            user_skill.is_enabled = False
            user_skill.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Invalidate cache
            self.invalidate_cache(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error disabling skill {skill_id} for user {user_id}: {str(e)}")
            self.db.rollback()
            raise SkillConfigurationError(f"Failed to disable skill: {str(e)}")
    
    async def update_skill_config(
        self,
        user_id: str,
        skill_id: str,
        config: Dict[str, Any],
        proficiency_level: Optional[int] = None,
        custom_priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update skill configuration for a user.
        
        Args:
            user_id: User UUID
            skill_id: Skill UUID
            config: New configuration
            proficiency_level: New proficiency level
            custom_priority: Custom priority override
            
        Returns:
            Updated skill dictionary
        """
        try:
            user_skill = self.db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_id,
                UserSkill.deleted_at.is_(None)
            ).first()
            
            if not user_skill:
                raise SkillNotFoundError(f"User skill {skill_id} not found")
            
            # Update configuration
            user_skill.config = config
            if proficiency_level is not None:
                user_skill.proficiency_level = max(1, min(5, proficiency_level))
            if custom_priority is not None:
                user_skill.custom_priority = custom_priority
            
            user_skill.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user_skill)
            
            # Invalidate cache
            self.invalidate_cache(user_id)
            
            # Return updated skill
            skill = user_skill.skill
            return await self._get_user_skill_dict(user_skill, skill)
            
        except Exception as e:
            logger.error(f"Error updating skill config {skill_id} for user {user_id}: {str(e)}")
            self.db.rollback()
            raise SkillConfigurationError(f"Failed to update skill config: {str(e)}")
    
    async def create_custom_skill(
        self,
        user_id: str,
        name: str,
        slug: str,
        description: str,
        system_prompt_template: str,
        config: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a custom skill for a user.
        
        Args:
            user_id: User UUID
            name: Skill name
            slug: Skill slug
            description: Skill description
            system_prompt_template: System prompt template
            config: Default configuration
            category: Skill category
            tags: Skill tags
            
        Returns:
            Created skill dictionary
        """
        try:
            # Check if skill with same name or slug already exists
            existing_skill = self.db.query(Skill).filter(
                or_(Skill.name == name, Skill.slug == slug),
                Skill.deleted_at.is_(None)
            ).first()
            
            if existing_skill:
                raise SkillAlreadyExistsError(f"Skill with name '{name}' or slug '{slug}' already exists")
            
            # Create new skill
            skill = Skill(
                name=name,
                slug=slug,
                description=description,
                system_prompt_template=system_prompt_template,
                default_config=config or {},
                category=category,
                tags=tags or [],
                is_builtin=False,
                priority=0
            )
            
            self.db.add(skill)
            self.db.flush()  # Get the ID
            
            # Create user skill association
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill.id,
                config=config or {},
                is_enabled=True,
                proficiency_level=1
            )
            
            self.db.add(user_skill)
            self.db.commit()
            self.db.refresh(skill)
            self.db.refresh(user_skill)
            
            # Invalidate cache
            self.invalidate_cache(user_id)
            
            return await self._get_user_skill_dict(user_skill, skill)
            
        except Exception as e:
            logger.error(f"Error creating custom skill for user {user_id}: {str(e)}")
            self.db.rollback()
            raise SkillConfigurationError(f"Failed to create custom skill: {str(e)}")
    
    async def delete_custom_skill(self, user_id: str, skill_id: str) -> bool:
        """
        Delete a custom skill (soft delete).
        
        Args:
            user_id: User UUID
            skill_id: Skill UUID
            
        Returns:
            True if successful
        """
        try:
            # Get skill
            skill = self.db.query(Skill).filter(
                Skill.id == skill_id,
                Skill.deleted_at.is_(None)
            ).first()
            
            if not skill:
                raise SkillNotFoundError(f"Skill {skill_id} not found")
            
            # Check if user owns this custom skill
            if skill.is_builtin:
                raise SkillPermissionError("Cannot delete built-in skills")
            
            # Check if user has this skill
            user_skill = self.db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_id,
                UserSkill.deleted_at.is_(None)
            ).first()
            
            if not user_skill:
                raise SkillPermissionError("User does not own this skill")
            
            # Soft delete the skill
            skill.deleted_at = datetime.utcnow()
            user_skill.deleted_at = datetime.utcnow()
            
            self.db.commit()
            
            # Invalidate cache
            self.invalidate_cache(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting custom skill {skill_id} for user {user_id}: {str(e)}")
            self.db.rollback()
            raise SkillConfigurationError(f"Failed to delete custom skill: {str(e)}")
    
    async def get_available_skills(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        builtin_only: bool = False,
        custom_only: bool = False,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available skills that users can add.
        
        Args:
            category: Filter by category
            tags: Filter by tags
            builtin_only: Only built-in skills
            custom_only: Only custom skills
            search: Search term
            
        Returns:
            List of available skill dictionaries
        """
        try:
            query = self.db.query(Skill).filter(
                Skill.deleted_at.is_(None),
                Skill.is_active == True
            )
            
            if category:
                query = query.filter(Skill.category == category)
            
            if tags:
                # Filter by tags (JSON contains)
                for tag in tags:
                    query = query.filter(Skill.tags.contains([tag]))
            
            if builtin_only:
                query = query.filter(Skill.is_builtin == True)
            elif custom_only:
                query = query.filter(Skill.is_builtin == False)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Skill.name.ilike(search_term),
                        Skill.description.ilike(search_term)
                    )
                )
            
            skills = query.order_by(Skill.priority.desc(), Skill.name).all()
            
            result = []
            for skill in skills:
                skill_dict = {
                    "id": str(skill.id),
                    "name": skill.name,
                    "slug": skill.slug,
                    "description": skill.description,
                    "system_prompt_template": skill.system_prompt_template,
                    "default_config": skill.default_config,
                    "category": skill.category,
                    "tags": skill.tags,
                    "is_builtin": skill.is_builtin,
                    "priority": skill.priority,
                    "created_at": skill.created_at.isoformat()
                }
                result.append(skill_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting available skills: {str(e)}")
            raise SkillConfigurationError(f"Failed to get available skills: {str(e)}")
    
    async def get_skill_categories(self) -> List[Dict[str, Any]]:
        """Get all skill categories."""
        try:
            categories = self.db.query(SkillCategory).filter(
                SkillCategory.is_active == True
            ).order_by(SkillCategory.sort_order, SkillCategory.name).all()
            
            result = []
            for category in categories:
                result.append({
                    "id": str(category.id),
                    "name": category.name,
                    "slug": category.slug,
                    "description": category.description,
                    "icon": category.icon,
                    "color": category.color,
                    "parent_id": str(category.parent_id) if category.parent_id else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting skill categories: {str(e)}")
            raise SkillConfigurationError(f"Failed to get skill categories: {str(e)}")
    
    async def log_skill_usage(
        self,
        user_id: str,
        skill_id: str,
        conversation_id: str,
        message_id: str,
        execution_time_ms: int,
        tokens_generated: int,
        success: bool = True,
        error_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log skill usage for analytics.
        
        Args:
            user_id: User UUID
            skill_id: Skill UUID
            conversation_id: Conversation UUID
            message_id: Message UUID
            execution_time_ms: Execution time in milliseconds
            tokens_generated: Number of tokens generated
            success: Whether the skill execution was successful
            error_message: Error message if failed
            context: Additional context
        """
        try:
            # Create usage log
            usage_log = SkillUsageLog(
                user_id=user_id,
                skill_id=skill_id,
                conversation_id=conversation_id,
                message_id=message_id,
                execution_time_ms=execution_time_ms,
                tokens_generated=tokens_generated,
                success=success,
                error_message=error_message,
                context=context or {}
            )
            
            self.db.add(usage_log)
            
            # Update user skill usage stats
            user_skill = self.db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_id,
                UserSkill.deleted_at.is_(None)
            ).first()
            
            if user_skill:
                user_skill.usage_count += 1
                user_skill.last_used_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging skill usage: {str(e)}")
            # Don't raise here as this is non-critical
    
    async def _get_user_skill_dict(self, user_skill: UserSkill, skill: Skill) -> Dict[str, Any]:
        """Convert user skill and skill to dictionary."""
        return {
            "id": str(skill.id),
            "user_skill_id": str(user_skill.id),
            "name": skill.name,
            "slug": skill.slug,
            "description": skill.description,
            "system_prompt_template": skill.system_prompt_template,
            "config": user_skill.config,
            "default_config": skill.default_config,
            "is_enabled": user_skill.is_enabled,
            "is_builtin": skill.is_builtin,
            "category": skill.category,
            "tags": skill.tags,
            "priority": user_skill.custom_priority or skill.priority,
            "proficiency_level": user_skill.proficiency_level,
            "usage_count": user_skill.usage_count,
            "last_used_at": user_skill.last_used_at.isoformat() if user_skill.last_used_at else None,
            "created_at": user_skill.created_at.isoformat()
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid."""
        if cache_key not in self._user_skills_cache:
            return False
        
        if cache_key not in self._last_cache_update:
            return False
        
        age = (datetime.utcnow() - self._last_cache_update[cache_key]).total_seconds()
        return age < self._cache_ttl
    
    def invalidate_cache(self, user_id: Optional[str] = None) -> None:
        """Invalidate cache for specific user or all users."""
        if user_id:
            # Invalidate all cache entries for this user
            keys_to_remove = [key for key in self._user_skills_cache.keys() if key.startswith(f"{user_id}_")]
            for key in keys_to_remove:
                self._user_skills_cache.pop(key, None)
                self._last_cache_update.pop(key, None)
        else:
            # Invalidate all cache
            self._user_skills_cache.clear()
            self._last_cache_update.clear()
    
    async def get_skill_usage_stats(self, user_id: str, skill_id: Optional[str] = None) -> Dict[str, Any]:
        """Get skill usage statistics for a user."""
        try:
            query = self.db.query(SkillUsageLog).filter(
                SkillUsageLog.user_id == user_id
            )
            
            if skill_id:
                query = query.filter(SkillUsageLog.skill_id == skill_id)
            
            logs = query.order_by(SkillUsageLog.created_at.desc()).limit(100).all()
            
            if not logs:
                return {
                    "total_usage": 0,
                    "average_execution_time": 0,
                    "total_tokens": 0,
                    "success_rate": 0,
                    "recent_usage": []
                }
            
            total_usage = len(logs)
            total_execution_time = sum(log.execution_time_ms for log in logs)
            total_tokens = sum(log.tokens_generated for log in logs)
            successful_usage = sum(1 for log in logs if log.success)
            
            recent_usage = []
            for log in logs[:10]:  # Last 10 uses
                recent_usage.append({
                    "skill_id": str(log.skill_id),
                    "execution_time_ms": log.execution_time_ms,
                    "tokens_generated": log.tokens_generated,
                    "success": log.success,
                    "created_at": log.created_at.isoformat()
                })
            
            return {
                "total_usage": total_usage,
                "average_execution_time": total_execution_time / total_usage,
                "total_tokens": total_tokens,
                "success_rate": (successful_usage / total_usage) * 100,
                "recent_usage": recent_usage
            }
            
        except Exception as e:
            logger.error(f"Error getting skill usage stats: {str(e)}")
            return {
                "total_usage": 0,
                "average_execution_time": 0,
                "total_tokens": 0,
                "success_rate": 0,
                "recent_usage": []
            }
