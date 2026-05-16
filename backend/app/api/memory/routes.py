from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db, MemoryItem
import uuid

router = APIRouter(prefix="/api/memory", tags=["memory"])


class MemoryItemCreate(BaseModel):
    content: str
    agent_id: Optional[str] = None
    importance: int = 5
    tags: List[str] = []


class MemoryItemResponse(BaseModel):
    id: str
    user_id: str
    agent_id: Optional[str]
    content: str
    importance: int
    tags: List[str]
    created_at: str

    class Config:
        from_attributes = True


@router.get("/user/{user_id}")
def get_user_memories(
    user_id: str,
    agent_id: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(lambda: next(get_db()))
):
    query = db.query(MemoryItem).filter(MemoryItem.user_id == user_id)
    if agent_id:
        query = query.filter(MemoryItem.agent_id == agent_id)
    memories = query.order_by(MemoryItem.importance.desc()).limit(limit).all()
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "agent_id": m.agent_id,
            "content": m.content,
            "importance": m.importance,
            "tags": m.tags or [],
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in memories
    ]


@router.post("/user/{user_id}")
def create_memory(
    user_id: str,
    data: MemoryItemCreate,
    db: Session = Depends(lambda: next(get_db()))
):
    memory = MemoryItem(
        id=str(uuid.uuid4()),
        user_id=user_id,
        agent_id=data.agent_id,
        content=data.content,
        importance=data.importance,
        tags=data.tags,
        created_at=datetime.utcnow()
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return {
        "id": memory.id,
        "user_id": memory.user_id,
        "agent_id": memory.agent_id,
        "content": memory.content,
        "importance": memory.importance,
        "tags": memory.tags or [],
        "created_at": memory.created_at.isoformat() if memory.created_at else None
    }


@router.delete("/{memory_id}")
def delete_memory(memory_id: str, db: Session = Depends(lambda: next(get_db()))):
    memory = db.query(MemoryItem).filter(MemoryItem.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    db.delete(memory)
    db.commit()
    return {"status": "deleted"}