from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db
from ..models import User, Skill, AgentSkill
from .auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


# Pydantic models
class SkillCreate(BaseModel):
    name: str
    slug: str
    description: str
    system_prompt_template: str
    default_config: Optional[dict] = {}


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt_template: Optional[str] = None
    default_config: Optional[dict] = None


class SkillResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    system_prompt_template: str
    default_config: dict
    is_builtin: bool
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


# Routes
@router.get("/", response_model=List[SkillResponse])
async def get_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_builtin: Optional[bool] = Query(None),
    is_active: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Skill).filter(Skill.is_active == is_active)
    
    if is_builtin is not None:
        query = query.filter(Skill.is_builtin == is_builtin)
    
    skills = query.offset(skip).limit(limit).all()
    
    return [
        SkillResponse(
            id=str(skill.id),
            name=skill.name,
            slug=skill.slug,
            description=skill.description,
            system_prompt_template=skill.system_prompt_template,
            default_config=skill.default_config,
            is_builtin=skill.is_builtin,
            is_active=skill.is_active,
            created_at=skill.created_at.isoformat(),
            updated_at=skill.updated_at.isoformat() if skill.updated_at else None
        )
        for skill in skills
    ]


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    return SkillResponse(
        id=str(skill.id),
        name=skill.name,
        slug=skill.slug,
        description=skill.description,
        system_prompt_template=skill.system_prompt_template,
        default_config=skill.default_config,
        is_builtin=skill.is_builtin,
        is_active=skill.is_active,
        created_at=skill.created_at.isoformat(),
        updated_at=skill.updated_at.isoformat() if skill.updated_at else None
    )


@router.post("/", response_model=SkillResponse)
async def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if skill with same name or slug already exists
    existing_skill = db.query(Skill).filter(
        (Skill.name == skill_data.name) | (Skill.slug == skill_data.slug)
    ).first()
    
    if existing_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill with this name or slug already exists"
        )
    
    # Create new skill
    db_skill = Skill(
        name=skill_data.name,
        slug=skill_data.slug,
        description=skill_data.description,
        system_prompt_template=skill_data.system_prompt_template,
        default_config=skill_data.default_config,
        is_builtin=False  # User-created skills are not builtin
    )
    
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    
    return SkillResponse(
        id=str(db_skill.id),
        name=db_skill.name,
        slug=db_skill.slug,
        description=db_skill.description,
        system_prompt_template=db_skill.system_prompt_template,
        default_config=db_skill.default_config,
        is_builtin=db_skill.is_builtin,
        is_active=db_skill.is_active,
        created_at=db_skill.created_at.isoformat(),
        updated_at=db_skill.updated_at.isoformat() if db_skill.updated_at else None
    )


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    skill_data: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # Don't allow updating builtin skills
    if skill.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update builtin skills"
        )
    
    # Update skill fields
    update_data = skill_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(skill, field, value)
    
    db.commit()
    db.refresh(skill)
    
    return SkillResponse(
        id=str(skill.id),
        name=skill.name,
        slug=skill.slug,
        description=skill.description,
        system_prompt_template=skill.system_prompt_template,
        default_config=skill.default_config,
        is_builtin=skill.is_builtin,
        is_active=skill.is_active,
        created_at=skill.created_at.isoformat(),
        updated_at=skill.updated_at.isoformat() if skill.updated_at else None
    )


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # Don't allow deleting builtin skills
    if skill.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete builtin skills"
        )
    
    # Check if skill is used by any agents
    agent_skills = db.query(AgentSkill).filter(AgentSkill.skill_id == skill_id).all()
    if agent_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete skill that is used by agents"
        )
    
    db.delete(skill)
    db.commit()
    
    return {"message": "Skill deleted successfully"}


@router.get("/search/{query}", response_model=List[SkillResponse])
async def search_skills(
    query: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skills = db.query(Skill).filter(
        Skill.is_active == True,
        (Skill.name.ilike(f"%{query}%") | Skill.description.ilike(f"%{query}%"))
    ).offset(skip).limit(limit).all()
    
    return [
        SkillResponse(
            id=str(skill.id),
            name=skill.name,
            slug=skill.slug,
            description=skill.description,
            system_prompt_template=skill.system_prompt_template,
            default_config=skill.default_config,
            is_builtin=skill.is_builtin,
            is_active=skill.is_active,
            created_at=skill.created_at.isoformat(),
            updated_at=skill.updated_at.isoformat() if skill.updated_at else None
        )
        for skill in skills
    ]
