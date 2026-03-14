import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from ..models import User, Agent, Skill, Tool, AgentSkill, AgentTool, Conversation, Message, ToolCall
from ..services.llm_service import LLMService
from ..services.prompt_generator import PromptGenerator
from .prompt_composer import PromptComposer
from .tool_executor import ToolExecutor
from .exceptions import (
    AgentRuntimeError,
    SkillLoadError,
    ToolExecutionError,
    PromptGenerationError
)

logger = logging.getLogger(__name__)


class AgentRuntime:
    """
    Main runtime for AI agent execution.
    Handles skill loading, prompt composition, tool execution, and LLM interaction.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.llm_service = LLMService()
        self.prompt_generator = PromptGenerator()
        self.prompt_composer = PromptComposer()
        self.tool_executor = ToolExecutor()
        
        # Cache for user-specific data
        self._user_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update: Dict[str, datetime] = {}
        
    async def process_message(
        self,
        user_id: str,
        conversation_id: str,
        message_content: str,
        channel_type: str = "web"
    ) -> Dict[str, Any]:
        """
        Process a user message and generate agent response.
        
        Args:
            user_id: User UUID
            conversation_id: Conversation UUID
            message_content: User message content
            channel_type: Channel type (web, telegram, voice)
            
        Returns:
            Dict containing agent response and metadata
        """
        try:
            # Load user agent data
            agent_data = await self._load_agent_data(user_id)
            
            if not agent_data:
                raise AgentRuntimeError(f"No agent found for user {user_id}")
            
            # Get conversation history
            conversation_history = await self._get_conversation_history(conversation_id)
            
            # Compose system prompt
            system_prompt = await self.prompt_composer.compose_prompt(
                agent=agent_data["agent"],
                skills=agent_data["skills"],
                tools=agent_data["tools"],
                channel_type=channel_type
            )
            
            # Format messages for LLM
            messages = self.llm_service.format_messages(
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                user_message=message_content
            )
            
            # Call LLM
            llm_response = await self.llm_service.chat_completion(
                messages=messages,
                model=agent_data["agent"].model_name,
                tools=agent_data["tools"]
            )
            
            # Process tool calls if any
            tool_results = []
            if "choices" in llm_response and llm_response["choices"]:
                choice = llm_response["choices"][0]
                message = choice.get("message", {})
                
                if "tool_calls" in message:
                    tool_results = await self._process_tool_calls(
                        tool_calls=message["tool_calls"],
                        tools=agent_data["tools"],
                        user_id=user_id
                    )
            
            # Extract response content
            response_content = self._extract_response_content(llm_response)
            
            # Save messages to database
            await self._save_conversation_messages(
                conversation_id=conversation_id,
                user_message=message_content,
                assistant_message=response_content,
                tool_results=tool_results
            )
            
            return {
                "response": response_content,
                "tool_calls": tool_results,
                "model_used": agent_data["agent"].model_name,
                "tokens_used": llm_response.get("usage", {}),
                "processing_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise AgentRuntimeError(f"Failed to process message: {str(e)}")
    
    async def _load_agent_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Load agent data including skills and tools.
        Uses caching for performance.
        """
        # Check cache first
        if self._is_cache_valid(user_id):
            return self._user_cache[user_id]
        
        try:
            # Get user's agent
            agent = self.db.query(Agent).filter(
                Agent.user_id == user_id,
                Agent.deleted_at.is_(None),
                Agent.is_active == True
            ).first()
            
            if not agent:
                return None
            
            # Get enabled skills
            user_skills = self.db.query(UserSkill, Skill).join(Skill).filter(
                UserSkill.user_id == user_id,
                UserSkill.deleted_at.is_(None),
                UserSkill.is_enabled == True,
                Skill.deleted_at.is_(None),
                Skill.is_active == True
            ).all()
            
            skills = []
            for user_skill, skill in user_skills:
                skill_data = {
                    "id": str(skill.id),
                    "name": skill.name,
                    "description": skill.description,
                    "system_prompt_template": skill.system_prompt_template,
                    "config": user_skill.config,
                    "proficiency_level": getattr(user_skill, 'proficiency_level', 1)
                }
                skills.append(skill_data)
            
            # Get enabled tools
            user_tools = self.db.query(UserTool, Tool).join(Tool).filter(
                UserTool.user_id == user_id,
                UserTool.deleted_at.is_(None),
                UserTool.is_enabled == True,
                Tool.deleted_at.is_(None),
                Tool.is_active == True
            ).all()
            
            tools = []
            for user_tool, tool in user_tools:
                tool_data = {
                    "id": str(tool.id),
                    "name": tool.name,
                    "description": tool.description,
                    "function_schema": tool.function_schema,
                    "config": user_tool.config
                }
                tools.append(tool_data)
            
            # Cache the data
            agent_data = {
                "agent": agent,
                "skills": skills,
                "tools": tools
            }
            
            self._user_cache[user_id] = agent_data
            self._last_cache_update[user_id] = datetime.utcnow()
            
            return agent_data
            
        except Exception as e:
            logger.error(f"Error loading agent data for user {user_id}: {str(e)}")
            raise SkillLoadError(f"Failed to load agent data: {str(e)}")
    
    async def _get_conversation_history(self, conversation_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history for context."""
        try:
            messages = self.db.query(Message).filter(
                Message.conversation_id == conversation_id,
                Message.deleted_at.is_(None)
            ).order_by(Message.created_at.asc()).limit(limit).all()
            
            history = []
            for msg in messages:
                history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error loading conversation history: {str(e)}")
            return []
    
    async def _process_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Process tool calls from LLM response."""
        results = []
        
        for tool_call in tool_calls:
            if tool_call.get("type") != "function":
                continue
                
            function_info = tool_call.get("function", {})
            tool_name = function_info.get("name")
            arguments = function_info.get("arguments", {})
            
            try:
                # Find tool configuration
                tool_config = None
                for tool in tools:
                    if tool["name"] == tool_name:
                        tool_config = tool
                        break
                
                if not tool_config:
                    raise ToolExecutionError(f"Tool {tool_name} not found")
                
                # Execute tool
                result = await self.tool_executor.execute_tool(
                    tool_name=tool_name,
                    arguments=arguments,
                    tool_config=tool_config,
                    user_id=user_id
                )
                
                results.append({
                    "tool_call_id": tool_call.get("id"),
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": result,
                    "status": "completed",
                    "error": None
                })
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {str(e)}")
                results.append({
                    "tool_call_id": tool_call.get("id"),
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": None,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def _extract_response_content(self, llm_response: Dict[str, Any]) -> str:
        """Extract response content from LLM response."""
        try:
            if "choices" in llm_response and llm_response["choices"]:
                choice = llm_response["choices"][0]
                message = choice.get("message", {})
                return message.get("content", "")
            return ""
        except Exception as e:
            logger.error(f"Error extracting response content: {str(e)}")
            return ""
    
    async def _save_conversation_messages(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        tool_results: List[Dict[str, Any]]
    ) -> None:
        """Save messages and tool calls to database."""
        try:
            # Save user message
            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                extra_data={"source": "agent_runtime"}
            )
            self.db.add(user_msg)
            self.db.flush()  # Get the ID
            
            # Save assistant message
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_message,
                extra_data={"source": "agent_runtime"}
            )
            self.db.add(assistant_msg)
            self.db.flush()  # Get the ID
            
            # Save tool calls
            for tool_result in tool_results:
                tool_call = ToolCall(
                    message_id=assistant_msg.id,
                    tool_name=tool_result["tool_name"],
                    arguments=tool_result["arguments"],
                    result=str(tool_result["result"]) if tool_result["result"] else None,
                    status=tool_result["status"],
                    error_message=tool_result.get("error")
                )
                self.db.add(tool_call)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error saving conversation messages: {str(e)}")
            self.db.rollback()
            raise
    
    def _is_cache_valid(self, user_id: str) -> bool:
        """Check if cached data is still valid."""
        if user_id not in self._user_cache:
            return False
        
        if user_id not in self._last_cache_update:
            return False
        
        age = (datetime.utcnow() - self._last_cache_update[user_id]).total_seconds()
        return age < self._cache_ttl
    
    def invalidate_cache(self, user_id: Optional[str] = None) -> None:
        """Invalidate cache for specific user or all users."""
        if user_id:
            self._user_cache.pop(user_id, None)
            self._last_cache_update.pop(user_id, None)
        else:
            self._user_cache.clear()
            self._last_cache_update.clear()
    
    async def get_agent_status(self, user_id: str) -> Dict[str, Any]:
        """Get current agent status and configuration."""
        try:
            agent_data = await self._load_agent_data(user_id)
            
            if not agent_data:
                return {"status": "no_agent"}
            
            return {
                "status": "active",
                "agent_name": agent_data["agent"].name,
                "model": agent_data["agent"].model_name,
                "skills_count": len(agent_data["skills"]),
                "tools_count": len(agent_data["tools"]),
                "last_updated": self._last_cache_update.get(user_id).isoformat() if user_id in self._last_cache_update else None
            }
            
        except Exception as e:
            logger.error(f"Error getting agent status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def update_agent_configuration(
        self,
        user_id: str,
        config_updates: Dict[str, Any]
    ) -> bool:
        """Update agent configuration and invalidate cache."""
        try:
            agent = self.db.query(Agent).filter(
                Agent.user_id == user_id,
                Agent.deleted_at.is_(None)
            ).first()
            
            if not agent:
                return False
            
            # Update configuration
            if "configuration" in config_updates:
                agent.configuration.update(config_updates["configuration"])
            
            if "model_name" in config_updates:
                agent.model_name = config_updates["model_name"]
            
            if "name" in config_updates:
                agent.name = config_updates["name"]
            
            if "description" in config_updates:
                agent.description = config_updates["description"]
            
            self.db.commit()
            
            # Invalidate cache
            self.invalidate_cache(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent configuration: {str(e)}")
            self.db.rollback()
            return False
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._user_cache.clear()
        self._last_cache_update.clear()
        logger.info("Agent runtime cleanup completed")
