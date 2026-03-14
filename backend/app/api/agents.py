from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db
from ..models import User, Agent, AgentSkill, Skill, AgentTool, Tool
from .auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


# Pydantic models
class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    model_name: Optional[str] = "gpt-3.5-turbo"
    configuration: Optional[dict] = {}


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_name: Optional[str] = None
    configuration: Optional[dict] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    system_prompt: str
    model_name: str
    configuration: dict
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    model_config = {"from_attributes": True}


class SkillResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    is_enabled: bool
    config: dict

    model_config = {"from_attributes": True}


class ToolResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    is_enabled: bool
    config: dict

    model_config = {"from_attributes": True}


class AgentDetailResponse(AgentResponse):
    skills: List[SkillResponse] = []
    tools: List[ToolResponse] = []


# Utility functions
def generate_system_prompt(agent: Agent, skills: List[Skill], tools: List[Tool]) -> str:
    """Generate dynamic system prompt based on agent's enabled skills and tools"""
    base_prompt = f"""You are {agent.name}, an AI assistant.
{agent.description or ''}

Your personality and capabilities are defined by your active skills and tools."""

    if skills:
        base_prompt += "\n\nActive Skills:\n"
        for skill in skills:
            skill_prompt = skill.system_prompt_template.format(**skill.config)
            base_prompt += f"- {skill.name}: {skill_prompt}\n"

    if tools:
        base_prompt += "\n\nAvailable Tools:\n"
        for tool in tools:
            base_prompt += f"- {tool.name}: {tool.description}\n"

    base_prompt += "\n\nRespond helpfully and use your tools when appropriate."
    return base_prompt


# Routes
@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user already has an agent
    existing_agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an agent"
        )
    
    # Create new agent
    db_agent = Agent(
        user_id=current_user.id,
        name=agent_data.name,
        description=agent_data.description,
        system_prompt="You are a helpful AI assistant.",
        model_name=agent_data.model_name,
        configuration=agent_data.configuration
    )
    
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    return AgentResponse(
        id=str(db_agent.id),
        name=db_agent.name,
        description=db_agent.description,
        system_prompt=db_agent.system_prompt,
        model_name=db_agent.model_name,
        configuration=db_agent.configuration,
        is_active=db_agent.is_active,
        created_at=db_agent.created_at.isoformat(),
        updated_at=db_agent.updated_at.isoformat() if db_agent.updated_at else None
    )


@router.get("/", response_model=AgentResponse)
async def get_agent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        model_name=agent.model_name,
        configuration=agent.configuration,
        is_active=agent.is_active,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat() if agent.updated_at else None
    )


@router.get("/detail", response_model=AgentDetailResponse)
async def get_agent_detail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Get agent skills
    agent_skills = db.query(AgentSkill, Skill).join(Skill).filter(
        AgentSkill.agent_id == agent.id,
        AgentSkill.is_enabled == True
    ).all()
    
    skills = []
    for agent_skill, skill in agent_skills:
        skills.append(SkillResponse(
            id=str(skill.id),
            name=skill.name,
            slug=skill.slug,
            description=skill.description,
            is_enabled=agent_skill.is_enabled,
            config=agent_skill.config
        ))
    
    # Get agent tools
    agent_tools = db.query(AgentTool, Tool).join(Tool).filter(
        AgentTool.agent_id == agent.id,
        AgentTool.is_enabled == True
    ).all()
    
    tools = []
    for agent_tool, tool in agent_tools:
        tools.append(ToolResponse(
            id=str(tool.id),
            name=tool.name,
            slug=tool.slug,
            description=tool.description,
            is_enabled=agent_tool.is_enabled,
            config=agent_tool.config
        ))
    
    return AgentDetailResponse(
        id=str(agent.id),
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        model_name=agent.model_name,
        configuration=agent.configuration,
        is_active=agent.is_active,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat() if agent.updated_at else None,
        skills=skills,
        tools=tools
    )


@router.put("/", response_model=AgentResponse)
async def update_agent(
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Update agent fields
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    
    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        model_name=agent.model_name,
        configuration=agent.configuration,
        is_active=agent.is_active,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat() if agent.updated_at else None
    )


@router.post("/skills/{skill_id}")
async def add_skill_to_agent(
    skill_id: str,
    config: Optional[dict] = None,
    is_enabled: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check if skill exists
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # Check if skill already added
    existing_agent_skill = db.query(AgentSkill).filter(
        AgentSkill.agent_id == agent.id,
        AgentSkill.skill_id == skill_id
    ).first()
    
    if existing_agent_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill already added to agent"
        )
    
    # Add skill to agent
    agent_skill = AgentSkill(
        agent_id=agent.id,
        skill_id=skill_id,
        config=config or skill.default_config,
        is_enabled=is_enabled
    )
    
    db.add(agent_skill)
    db.commit()
    
    # Update agent system prompt
    enabled_skills = db.query(Skill).join(AgentSkill).filter(
        AgentSkill.agent_id == agent.id,
        AgentSkill.is_enabled == True
    ).all()
    
    enabled_tools = db.query(Tool).join(AgentTool).filter(
        AgentTool.agent_id == agent.id,
        AgentTool.is_enabled == True
    ).all()
    
    agent.system_prompt = generate_system_prompt(agent, enabled_skills, enabled_tools)
    db.commit()
    
    return {"message": "Skill added to agent successfully"}


@router.delete("/skills/{skill_id}")
async def remove_skill_from_agent(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    agent_skill = db.query(AgentSkill).filter(
        AgentSkill.agent_id == agent.id,
        AgentSkill.skill_id == skill_id
    ).first()
    
    if not agent_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found in agent"
        )
    
    db.delete(agent_skill)
    db.commit()
    
    # Update agent system prompt
    enabled_skills = db.query(Skill).join(AgentSkill).filter(
        AgentSkill.agent_id == agent.id,
        AgentSkill.is_enabled == True
    ).all()
    
    enabled_tools = db.query(Tool).join(AgentTool).filter(
        AgentTool.agent_id == agent.id,
        AgentTool.is_enabled == True
    ).all()
    
    agent.system_prompt = generate_system_prompt(agent, enabled_skills, enabled_tools)
    db.commit()
    
    return {"message": "Skill removed from agent successfully"}
