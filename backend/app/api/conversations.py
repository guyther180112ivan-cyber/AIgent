from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import asyncio
from datetime import datetime

from ..core.database import get_db
from ..models import User, Agent, Conversation, Message, ToolCall
from .auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


# Pydantic models
class MessageCreate(BaseModel):
    content: str
    channel_type: str = "web"
    channel_id: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    tool_calls: List[dict] = []

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    channel_type: str
    channel_id: str
    metadata: dict
    created_at: str
    updated_at: Optional[str]
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    channel_type: str = "web"
    channel_id: Optional[str] = None
    metadata: Optional[dict] = {}


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        self.active_connections[conversation_id] = websocket

    def disconnect(self, conversation_id: str):
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]

    async def send_message(self, conversation_id: str, message: dict):
        if conversation_id in self.active_connections:
            await self.active_connections[conversation_id].send_text(json.dumps(message))


manager = ConnectionManager()


# Utility functions
async def process_message_with_agent(
    message_content: str,
    agent: Agent,
    conversation: Conversation,
    db: Session
) -> Message:
    """Process message with agent and generate response"""
    # This is a placeholder - in real implementation, this would:
    # 1. Get conversation history
    # 2. Build messages array for LLM
    # 3. Call LLM API (OpenRouter)
    # 4. Handle function calls
    # 5. Save response and tool calls
    
    # For now, return a simple echo response
    response_content = f"Agent {agent.name} received: {message_content}"
    
    # Create assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response_content,
        metadata={"model": agent.model_name}
    )
    
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return assistant_message


# Routes
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conv_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get user's agent
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Create conversation
    conversation = Conversation(
        agent_id=agent.id,
        channel_type=conv_data.channel_type,
        channel_id=conv_data.channel_id or f"web_{current_user.id}",
        metadata=conv_data.metadata or {}
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return ConversationResponse(
        id=str(conversation.id),
        channel_type=conversation.channel_type,
        channel_id=conversation.channel_id,
        metadata=conversation.metadata,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else None,
        messages=[]
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get user's agent
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    conversations = db.query(Conversation).filter(
        Conversation.agent_id == agent.id
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for conv in conversations:
        # Get latest message for preview
        latest_message = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.desc()).first()
        
        messages = []
        if latest_message:
            messages.append(MessageResponse(
                id=str(latest_message.id),
                role=latest_message.role,
                content=latest_message.content,
                created_at=latest_message.created_at.isoformat()
            ))
        
        result.append(ConversationResponse(
            id=str(conv.id),
            channel_type=conv.channel_type,
            channel_id=conv.channel_id,
            metadata=conv.metadata,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat() if conv.updated_at else None,
            messages=messages
        ))
    
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get user's agent
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.agent_id == agent.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages
    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.asc()).all()
    
    message_responses = []
    for msg in messages:
        # Get tool calls for this message
        tool_calls = db.query(ToolCall).filter(
            ToolCall.message_id == msg.id
        ).all()
        
        tool_call_data = [
            {
                "id": str(tc.id),
                "tool_name": tc.tool_name,
                "arguments": tc.arguments,
                "result": tc.result,
                "status": tc.status,
                "created_at": tc.created_at.isoformat(),
                "completed_at": tc.completed_at.isoformat() if tc.completed_at else None
            }
            for tc in tool_calls
        ]
        
        message_responses.append(MessageResponse(
            id=str(msg.id),
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at.isoformat(),
            tool_calls=tool_call_data
        ))
    
    return ConversationResponse(
        id=str(conversation.id),
        channel_type=conversation.channel_type,
        channel_id=conversation.channel_id,
        metadata=conversation.metadata,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else None,
        messages=message_responses
    )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get user's agent
    agent = db.query(Agent).filter(Agent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.agent_id == agent.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Create user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=message_data.content,
        metadata={"channel_type": message_data.channel_type}
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Process with agent
    assistant_message = await process_message_with_agent(
        message_data.content,
        agent,
        conversation,
        db
    )
    
    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    db.commit()
    
    # Send response via WebSocket if connected
    await manager.send_message(conversation_id, {
        "type": "message",
        "message": {
            "id": str(assistant_message.id),
            "role": assistant_message.role,
            "content": assistant_message.content,
            "created_at": assistant_message.created_at.isoformat()
        }
    })
    
    return MessageResponse(
        id=str(assistant_message.id),
        role=assistant_message.role,
        content=assistant_message.content,
        created_at=assistant_message.created_at.isoformat()
    )


@router.websocket("/conversations/{conversation_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    db: Session = Depends(get_db)
):
    await manager.connect(websocket, conversation_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages
            message_data = json.loads(data)
            
            # Process message and send response
            # This would integrate with the message processing logic
            await manager.send_message(conversation_id, {
                "type": "echo",
                "data": message_data
            })
            
    except WebSocketDisconnect:
        manager.disconnect(conversation_id)
