from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from ..core.database import get_db
from ..models import User, Agent, Conversation, Message
from .auth import get_current_user, get_current_user_optional
from ..runtime.agent_runtime import AgentRuntime
from pydantic import BaseModel

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str


async def get_demo_user(db: Session) -> User:
    """Get or create a demo user for testing."""
    demo_email = "demo@aigent.com"
    user = db.query(User).filter(User.email == demo_email).first()
    
    if not user:
        user = User(
            email=demo_email,
            username="demo",
            hashed_password="demo",
            name="Demo User",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


@router.post("/chat", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Send a message to the AI agent and get a response.
    Uses OpenRouter API for LLM processing.
    """
    try:
        # Get user - either from auth or create demo user
        user = None
        if authorization and authorization.startswith("Bearer "):
            from jose import jwt, JWTError
            from ..core.config import settings
            try:
                token = authorization.replace("Bearer ", "")
                payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
                user_id = payload.get("sub")
                if user_id:
                    user = db.query(User).filter(User.id == user_id).first()
            except JWTError:
                pass
        
        if not user:
            # Use demo user for testing
            user = await get_demo_user(db)
        
        # Get or create agent for user
        agent = db.query(Agent).filter(Agent.user_id == user.id).first()
        if not agent:
            # Create default agent
            agent = Agent(
                user_id=user.id,
                name="Default Agent",
                description="Your personal AI assistant powered by OpenRouter",
                model_name="anthropic/claude-3-sonnet",
                system_prompt="You are a helpful AI assistant. Answer user questions clearly and concisely.",
                is_active=True
            )
            db.add(agent)
            db.commit()
            db.refresh(agent)
        
        # Get or create conversation
        conversation = None
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id,
                Conversation.agent_id == agent.id
            ).first()
        
        if not conversation:
            conversation = Conversation(
                agent_id=agent.id,
                channel_type="web",
                channel_id=f"web_{user.id}",
                extra_data={}
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            extra_data={"channel_type": "web"}
        )
        db.add(user_message)
        db.commit()
        
        # Process with AgentRuntime
        runtime = AgentRuntime(db)
        result = await runtime.process_message(
            user_id=str(user.id),
            conversation_id=str(conversation.id),
            message_content=request.message,
            channel_type="web"
        )
        
        # Get the assistant message that was saved
        assistant_message = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.role == "assistant"
        ).order_by(Message.created_at.desc()).first()
        
        if not assistant_message:
            # Fallback response if something went wrong
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=result.get("response", "I'm sorry, I couldn't process your request."),
                extra_data={}
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
        
        return ChatMessageResponse(
            response=assistant_message.content,
            conversation_id=str(conversation.id),
            message_id=str(assistant_message.id)
        )
        
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )
