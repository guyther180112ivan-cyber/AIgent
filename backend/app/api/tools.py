from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db
from ..models import User, Tool, AgentTool
from .auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


# Pydantic models
class ToolCreate(BaseModel):
    name: str
    slug: str
    description: str
    function_schema: dict
    default_config: Optional[dict] = {}


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    function_schema: Optional[dict] = None
    default_config: Optional[dict] = None


class ToolResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    function_schema: dict
    default_config: dict
    is_builtin: bool
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    model_config = {"from_attributes": True}


# Routes
@router.get("/", response_model=List[ToolResponse])
async def get_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_builtin: Optional[bool] = Query(None),
    is_active: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Tool).filter(Tool.is_active == is_active)
    
    if is_builtin is not None:
        query = query.filter(Tool.is_builtin == is_builtin)
    
    tools = query.offset(skip).limit(limit).all()
    
    return [
        ToolResponse(
            id=str(tool.id),
            name=tool.name,
            slug=tool.slug,
            description=tool.description,
            function_schema=tool.function_schema,
            default_config=tool.default_config,
            is_builtin=tool.is_builtin,
            is_active=tool.is_active,
            created_at=tool.created_at.isoformat(),
            updated_at=tool.updated_at.isoformat() if tool.updated_at else None
        )
        for tool in tools
    ]


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    return ToolResponse(
        id=str(tool.id),
        name=tool.name,
        slug=tool.slug,
        description=tool.description,
        function_schema=tool.function_schema,
        default_config=tool.default_config,
        is_builtin=tool.is_builtin,
        is_active=tool.is_active,
        created_at=tool.created_at.isoformat(),
        updated_at=tool.updated_at.isoformat() if tool.updated_at else None
    )


@router.post("/", response_model=ToolResponse)
async def create_tool(
    tool_data: ToolCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if tool with same name or slug already exists
    existing_tool = db.query(Tool).filter(
        (Tool.name == tool_data.name) | (Tool.slug == tool_data.slug)
    ).first()
    
    if existing_tool:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tool with this name or slug already exists"
        )
    
    # Validate function schema
    if not isinstance(tool_data.function_schema, dict) or "name" not in tool_data.function_schema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid function schema. Must contain 'name' field."
        )
    
    # Create new tool
    db_tool = Tool(
        name=tool_data.name,
        slug=tool_data.slug,
        description=tool_data.description,
        function_schema=tool_data.function_schema,
        default_config=tool_data.default_config,
        is_builtin=False  # User-created tools are not builtin
    )
    
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    
    return ToolResponse(
        id=str(db_tool.id),
        name=db_tool.name,
        slug=db_tool.slug,
        description=db_tool.description,
        function_schema=db_tool.function_schema,
        default_config=db_tool.default_config,
        is_builtin=db_tool.is_builtin,
        is_active=db_tool.is_active,
        created_at=db_tool.created_at.isoformat(),
        updated_at=db_tool.updated_at.isoformat() if db_tool.updated_at else None
    )


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: str,
    tool_data: ToolUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    # Don't allow updating builtin tools
    if tool.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update builtin tools"
        )
    
    # Update tool fields
    update_data = tool_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)
    
    db.commit()
    db.refresh(tool)
    
    return ToolResponse(
        id=str(tool.id),
        name=tool.name,
        slug=tool.slug,
        description=tool.description,
        function_schema=tool.function_schema,
        default_config=tool.default_config,
        is_builtin=tool.is_builtin,
        is_active=tool.is_active,
        created_at=tool.created_at.isoformat(),
        updated_at=tool.updated_at.isoformat() if tool.updated_at else None
    )


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    # Don't allow deleting builtin tools
    if tool.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete builtin tools"
        )
    
    # Check if tool is used by any agents
    agent_tools = db.query(AgentTool).filter(AgentTool.tool_id == tool_id).all()
    if agent_tools:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete tool that is used by agents"
        )
    
    db.delete(tool)
    db.commit()
    
    return {"message": "Tool deleted successfully"}


@router.get("/search/{query}", response_model=List[ToolResponse])
async def search_tools(
    query: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tools = db.query(Tool).filter(
        Tool.is_active == True,
        (Tool.name.ilike(f"%{query}%") | Tool.description.ilike(f"%{query}%"))
    ).offset(skip).limit(limit).all()
    
    return [
        ToolResponse(
            id=str(tool.id),
            name=tool.name,
            slug=tool.slug,
            description=tool.description,
            function_schema=tool.function_schema,
            default_config=tool.default_config,
            is_builtin=tool.is_builtin,
            is_active=tool.is_active,
            created_at=tool.created_at.isoformat(),
            updated_at=tool.updated_at.isoformat() if tool.updated_at else None
        )
        for tool in tools
    ]
