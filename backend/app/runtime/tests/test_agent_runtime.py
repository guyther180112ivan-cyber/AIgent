import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from ..agent_runtime import AgentRuntime
from ..exceptions import AgentRuntimeError, SkillLoadError
from ...models import Agent, Skill, Tool


class TestAgentRuntime:
    """Test cases for AgentRuntime."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def agent_runtime(self, mock_db):
        """Create AgentRuntime instance with mocked dependencies."""
        with patch('app.runtime.agent_runtime.LLMService'), \
             patch('app.runtime.agent_runtime.PromptGenerator'), \
             patch('app.runtime.agent_runtime.PromptComposer'), \
             patch('app.runtime.agent_runtime.ToolExecutor'):
            return AgentRuntime(mock_db)
    
    @pytest.fixture
    def sample_agent(self):
        """Create sample agent."""
        agent = Mock(spec=Agent)
        agent.id = "agent-123"
        agent.name = "Test Agent"
        agent.description = "A test agent"
        agent.model_name = "gpt-3.5-turbo"
        agent.configuration = {}
        return agent
    
    @pytest.fixture
    def sample_skills(self):
        """Create sample skills."""
        return [
            {
                "id": "skill-1",
                "name": "General Assistant",
                "description": "Basic assistance",
                "system_prompt_template": "You are helpful",
                "config": {},
                "proficiency_level": 3
            }
        ]
    
    @pytest.fixture
    def sample_tools(self):
        """Create sample tools."""
        return [
            {
                "id": "tool-1",
                "name": "calculator",
                "description": "Math calculator",
                "function_schema": {
                    "name": "calculator",
                    "parameters": {"type": "object", "properties": {}}
                },
                "config": {}
            }
        ]
    
    @pytest.mark.asyncio
    async def test_process_message_success(self, agent_runtime, mock_db, sample_agent, sample_skills, sample_tools):
        """Test successful message processing."""
        # Setup mocks
        agent_runtime._load_agent_data = AsyncMock(return_value={
            "agent": sample_agent,
            "skills": sample_skills,
            "tools": sample_tools
        })
        
        agent_runtime._get_conversation_history = AsyncMock(return_value=[])
        agent_runtime.prompt_composer.compose_prompt = AsyncMock(return_value="System prompt")
        agent_runtime.llm_service.format_messages = Mock(return_value=[])
        agent_runtime.llm_service.chat_completion = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"total_tokens": 50}
        })
        agent_runtime._process_tool_calls = AsyncMock(return_value=[])
        agent_runtime._extract_response_content = Mock(return_value="Test response")
        agent_runtime._save_conversation_messages = AsyncMock()
        
        # Execute
        result = await agent_runtime.process_message(
            user_id="user-123",
            conversation_id="conv-123",
            message_content="Hello"
        )
        
        # Verify
        assert result["response"] == "Test response"
        assert result["tool_calls"] == []
        assert result["model_used"] == "gpt-3.5-turbo"
        assert result["tokens_used"]["total_tokens"] == 50
        
        # Verify method calls
        agent_runtime._load_agent_data.assert_called_once_with("user-123")
        agent_runtime.prompt_composer.compose_prompt.assert_called_once()
        agent_runtime.llm_service.chat_completion.assert_called_once()
        agent_runtime._save_conversation_messages.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_no_agent(self, agent_runtime, mock_db):
        """Test processing message when no agent exists."""
        agent_runtime._load_agent_data = AsyncMock(return_value=None)
        
        with pytest.raises(AgentRuntimeError, match="No agent found"):
            await agent_runtime.process_message(
                user_id="user-123",
                conversation_id="conv-123",
                message_content="Hello"
            )
    
    @pytest.mark.asyncio
    async def test_process_message_with_tool_calls(self, agent_runtime, mock_db, sample_agent, sample_skills, sample_tools):
        """Test processing message with tool calls."""
        # Setup mocks
        agent_runtime._load_agent_data = AsyncMock(return_value={
            "agent": sample_agent,
            "skills": sample_skills,
            "tools": sample_tools
        })
        
        agent_runtime._get_conversation_history = AsyncMock(return_value=[])
        agent_runtime.prompt_composer.compose_prompt = AsyncMock(return_value="System prompt")
        agent_runtime.llm_service.format_messages = Mock(return_value=[])
        agent_runtime.llm_service.chat_completion = AsyncMock(return_value={
            "choices": [{
                "message": {
                    "content": "Test response",
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": "calculator",
                                "arguments": '{"expression": "2+2"}'
                            }
                        }
                    ]
                }
            }],
            "usage": {"total_tokens": 50}
        })
        
        agent_runtime._process_tool_calls = AsyncMock(return_value=[
            {
                "tool_call_id": "call-1",
                "tool_name": "calculator",
                "arguments": {"expression": "2+2"},
                "result": "4",
                "status": "completed",
                "error": None
            }
        ])
        
        agent_runtime._extract_response_content = Mock(return_value="Test response")
        agent_runtime._save_conversation_messages = AsyncMock()
        
        # Execute
        result = await agent_runtime.process_message(
            user_id="user-123",
            conversation_id="conv-123",
            message_content="Calculate 2+2"
        )
        
        # Verify
        assert result["response"] == "Test response"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool_name"] == "calculator"
        assert result["tool_calls"][0]["result"] == "4"
        
        # Verify tool calls processing
        agent_runtime._process_tool_calls.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_agent_data_success(self, agent_runtime, mock_db):
        """Test successful agent data loading."""
        # Setup database mocks
        mock_agent = Mock(spec=Agent)
        mock_agent.id = "agent-123"
        mock_agent.name = "Test Agent"
        mock_agent.model_name = "gpt-3.5-turbo"
        
        mock_skill = Mock(spec=Skill)
        mock_skill.id = "skill-123"
        mock_skill.name = "Test Skill"
        mock_skill.description = "Test description"
        mock_skill.system_prompt_template = "You are helpful"
        
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (Mock(config={}, proficiency_level=1), mock_skill)
        ]
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_agent
        
        # Execute
        result = await agent_runtime._load_agent_data("user-123")
        
        # Verify
        assert result is not None
        assert result["agent"].id == "agent-123"
        assert len(result["skills"]) == 1
        assert result["skills"][0]["name"] == "Test Skill"
    
    @pytest.mark.asyncio
    async def test_load_agent_data_cache(self, agent_runtime):
        """Test agent data caching."""
        # Setup cache
        cached_data = {"agent": Mock(), "skills": [], "tools": []}
        agent_runtime._user_cache["user-123"] = cached_data
        agent_runtime._last_cache_update["user-123"] = datetime.utcnow()
        
        # Execute
        result = await agent_runtime._load_agent_data("user-123")
        
        # Verify cache hit
        assert result is cached_data
    
    @pytest.mark.asyncio
    async def test_get_agent_status(self, agent_runtime):
        """Test getting agent status."""
        # Setup cache
        agent_runtime._user_cache["user-123"] = {
            "agent": Mock(name="Test Agent", model_name="gpt-3.5-turbo"),
            "skills": [Mock(), Mock()],
            "tools": [Mock()]
        }
        agent_runtime._last_cache_update["user-123"] = datetime.utcnow()
        
        # Execute
        status = await agent_runtime.get_agent_status("user-123")
        
        # Verify
        assert status["status"] == "active"
        assert status["agent_name"] == "Test Agent"
        assert status["model"] == "gpt-3.5-turbo"
        assert status["skills_count"] == 2
        assert status["tools_count"] == 1
    
    @pytest.mark.asyncio
    async def test_get_agent_status_no_agent(self, agent_runtime):
        """Test getting agent status when no agent exists."""
        agent_runtime._load_agent_data = AsyncMock(return_value=None)
        
        # Execute
        status = await agent_runtime.get_agent_status("user-123")
        
        # Verify
        assert status["status"] == "no_agent"
    
    @pytest.mark.asyncio
    async def test_update_agent_configuration(self, agent_runtime, mock_db):
        """Test updating agent configuration."""
        # Setup mock agent
        mock_agent = Mock(spec=Agent)
        mock_agent.configuration = {}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_agent
        
        # Execute
        result = await agent_runtime.update_agent_configuration(
            user_id="user-123",
            config_updates={
                "configuration": {"new_setting": "value"},
                "model_name": "gpt-4"
            }
        )
        
        # Verify
        assert result is True
        mock_agent.configuration.update.assert_called_once_with({"new_setting": "value"})
        assert mock_agent.model_name == "gpt-4"
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_agent_configuration_no_agent(self, agent_runtime, mock_db):
        """Test updating configuration when no agent exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = await agent_runtime.update_agent_configuration(
            user_id="user-123",
            config_updates={"model_name": "gpt-4"}
        )
        
        # Verify
        assert result is False
    
    def test_cache_invalidation(self, agent_runtime):
        """Test cache invalidation."""
        # Setup cache
        agent_runtime._user_cache["user-123"] = {"data": "test"}
        agent_runtime._last_cache_update["user-123"] = datetime.utcnow()
        
        # Invalidate specific user
        agent_runtime.invalidate_cache("user-123")
        
        # Verify
        assert "user-123" not in agent_runtime._user_cache
        assert "user-123" not in agent_runtime._last_cache_update
        
        # Setup cache again
        agent_runtime._user_cache["user-456"] = {"data": "test"}
        agent_runtime._last_cache_update["user-456"] = datetime.utcnow()
        
        # Invalidate all
        agent_runtime.invalidate_cache()
        
        # Verify all cleared
        assert len(agent_runtime._user_cache) == 0
        assert len(agent_runtime._last_cache_update) == 0
    
    def test_is_cache_valid(self, agent_runtime):
        """Test cache validity checking."""
        # Test no cache
        assert not agent_runtime._is_cache_valid("user-123")
        
        # Test valid cache
        agent_runtime._user_cache["user-123"] = {"data": "test"}
        agent_runtime._last_cache_update["user-123"] = datetime.utcnow()
        assert agent_runtime._is_cache_valid("user-123")
        
        # Test expired cache
        import time
        agent_runtime._last_cache_update["user-123"] = datetime.fromtimestamp(time.time() - 400)  # 400 seconds ago
        assert not agent_runtime._is_cache_valid("user-123")
