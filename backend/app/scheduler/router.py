"""
API router for scheduled tasks.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db, SessionLocal
from ..api.auth import get_current_user
from ..models.user import User

from .service import SchedulerService, get_scheduler_service, set_scheduler_service

# Dev mode: return default user if no auth
async def get_current_user_optional(token: str = None) -> User:
    """Get current user or return default dev user."""
    try:
        if token:
            return await get_current_user(token)
    except:
        pass
    
    # Return default dev user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "developer").first()
        if not user:
            from uuid import uuid4
            user = User(
                id=uuid4(),
                email="dev@example.com",
                username="developer",
                name="Dev User",
                hashed_password="dev_password_hash"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()
from .schemas import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskResponse,
    ScheduledTaskList,
    TaskExecutionResult,
    ScheduleParseRequest,
    ScheduleParseResponse,
    ScheduleType
)
from .models import ScheduledTask

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


def get_scheduler(db: Session = Depends(get_db)) -> SchedulerService:
    """Dependency to get scheduler service."""
    service = get_scheduler_service()
    if not service:
        service = SchedulerService(db)
        set_scheduler_service(service)
    return service


@router.post("/tasks", response_model=ScheduledTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: ScheduledTaskCreate,
    current_user: User = Depends(get_current_user_optional),
    scheduler: SchedulerService = Depends(get_scheduler),
    db: Session = Depends(get_db)
):
    """Create a new scheduled task."""
    try:
        task_dict = task_data.dict()
        
        # Convert string IDs to UUID if needed
        if task_dict.get("agent_id"):
            from uuid import UUID
            task_dict["agent_id"] = UUID(task_dict["agent_id"])
            
        task = scheduler.create_task(task_dict, str(current_user.id))
        return ScheduledTaskResponse.from_orm(task)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/tasks", response_model=ScheduledTaskList)
async def list_tasks(
    active_only: bool = False,
    current_user: User = Depends(get_current_user_optional),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """List all scheduled tasks for the current user."""
    tasks = scheduler.get_user_tasks(str(current_user.id), active_only=active_only)
    return ScheduledTaskList(
        items=[ScheduledTaskResponse.from_orm(t) for t in tasks],
        total=len(tasks)
    )


@router.get("/tasks/{task_id}", response_model=ScheduledTaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user_optional),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """Get a specific scheduled task."""
    task = scheduler.get_task(task_id, str(current_user.id))
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return ScheduledTaskResponse.from_orm(task)


@router.put("/tasks/{task_id}", response_model=ScheduledTaskResponse)
async def update_task(
    task_id: str,
    updates: ScheduledTaskUpdate,
    current_user: User = Depends(get_current_user_optional),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """Update a scheduled task."""
    update_dict = updates.dict(exclude_unset=True)
    
    task = scheduler.update_task(task_id, str(current_user.id), update_dict)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return ScheduledTaskResponse.from_orm(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user_optional),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """Delete a scheduled task."""
    success = scheduler.delete_task(task_id, str(current_user.id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )


@router.post("/tasks/{task_id}/pause", response_model=ScheduledTaskResponse)
async def pause_task(
    task_id: str,
    current_user: User = Depends(get_current_user_optional),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """Pause a scheduled task."""
    task = scheduler.pause_task(task_id, str(current_user.id))
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return ScheduledTaskResponse.from_orm(task)


@router.post("/tasks/{task_id}/resume", response_model=ScheduledTaskResponse)
async def resume_task(
    task_id: str,
    current_user: User = Depends(get_current_user_optional),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """Resume a paused scheduled task."""
    task = scheduler.resume_task(task_id, str(current_user.id))
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return ScheduledTaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/execute", response_model=TaskExecutionResult)
async def execute_task_now(
    task_id: str,
    current_user: User = Depends(get_current_user_optional),
    scheduler: SchedulerService = Depends(get_scheduler)
):
    """Execute a scheduled task immediately (manual trigger)."""
    task = scheduler.get_task(task_id, str(current_user.id))
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    result = await scheduler._execute_task(task)
    return result


@router.post("/parse", response_model=ScheduleParseResponse)
async def parse_schedule(
    request: ScheduleParseRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Parse natural language schedule description.
    
    Examples:
    - "завтра в 3 утра" -> tomorrow at 3 AM
    - "каждый день в 8:00" -> daily at 8:00
    - "через 30 минут" -> in 30 minutes
    """
    text = request.text.lower().strip()
    now = datetime.now()
    
    # Simple parsing logic (can be enhanced with NLP)
    scheduled_at = None
    schedule_type = ScheduleType.ONCE
    description = None
    
    # Parse "завтра в X"
    if "завтра" in text:
        scheduled_at = now + __import__('datetime').timedelta(days=1)
        if "утра" in text or "утро" in text:
            scheduled_at = scheduled_at.replace(hour=8, minute=0, second=0)
        elif "вечера" in text or "вечер" in text:
            scheduled_at = scheduled_at.replace(hour=18, minute=0, second=0)
        description = f"Завтра в {scheduled_at.strftime('%H:%M')}"
        
    # Parse "через X минут/часов"
    elif "через" in text:
        if "минут" in text:
            import re
            match = re.search(r'(\d+)\s*минут', text)
            if match:
                minutes = int(match.group(1))
                scheduled_at = now + __import__('datetime').timedelta(minutes=minutes)
                description = f"Через {minutes} минут"
        elif "час" in text:
            import re
            match = re.search(r'(\d+)\s*час', text)
            if match:
                hours = int(match.group(1))
                scheduled_at = now + __import__('datetime').timedelta(hours=hours)
                description = f"Через {hours} часов"
                
    # Parse "каждый день"
    elif "каждый день" in text or "ежедневно" in text:
        schedule_type = ScheduleType.DAILY
        scheduled_at = now.replace(hour=8, minute=0, second=0)
        description = "Каждый день в 8:00"
        
    # Parse "каждую неделю"
    elif "каждую неделю" in text or "еженедельно" in text:
        schedule_type = ScheduleType.WEEKLY
        scheduled_at = now + __import__('datetime').timedelta(weeks=1)
        description = "Каждую неделю"
    
    if scheduled_at:
        return ScheduleParseResponse(
            success=True,
            scheduled_at=scheduled_at,
            schedule_type=schedule_type,
            description=description
        )
    else:
        return ScheduleParseResponse(
            success=False,
            error="Could not parse schedule description"
        )


# Health check endpoint for scheduler
@router.get("/health")
async def scheduler_health():
    """Check scheduler service health."""
    service = get_scheduler_service()
    return {
        "status": "healthy" if service and service.is_running else "not_running",
        "is_running": service.is_running if service else False
    }
