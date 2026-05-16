import httpx
import json
from typing import List, Dict, Any, Optional
from ..core.config import settings
from ..models import Agent, Tool


class LLMService:
    """Service for interacting with LLM providers (OpenRouter)"""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = settings.default_model
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create chat completion with optional function calling"""
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            **kwargs
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Add tools if provided
        if tools:
            function_schemas = []
            for tool in tools:
                function_schemas.append(tool.function_schema)
            
            payload["tools"] = [
                {
                    "type": "function",
                    "function": schema
                }
                for schema in function_schemas
            ]
            payload["tool_choice"] = "auto"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"LLM API error: {response.status_code} - {error_text}")
            
            return response.json()

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Stream chat completion response"""
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            **kwargs
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Add tools if provided
        if tools:
            function_schemas = []
            for tool in tools:
                function_schemas.append(tool.function_schema)
            
            payload["tools"] = [
                {
                    "type": "function",
                    "function": schema
                }
                for schema in function_schemas
            ]
            payload["tool_choice"] = "auto"
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"LLM API error: {response.status_code} - {error_text}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue

    def format_messages(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, Any]],
        user_message: str
    ) -> List[Dict[str, str]]:
        """Format messages for LLM API"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages

    async def extract_function_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract function calls from LLM response"""
        
        function_calls = []
        
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            message = choice.get("message", {})
            
            if "tool_calls" in message:
                for tool_call in message["tool_calls"]:
                    if tool_call["type"] == "function":
                        function_call = {
                            "id": tool_call["id"],
                            "name": tool_call["function"]["name"],
                            "arguments": json.loads(tool_call["function"]["arguments"])
                        }
                        function_calls.append(function_call)
        
        return function_calls

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        
        # Common model configurations
        model_configs = {
            "anthropic/claude-3-sonnet": {
                "max_tokens": 4096,
                "supports_tools": True,
                "supports_vision": True,
                "cost_per_1k_input": 0.003,
                "cost_per_1k_output": 0.015
            },
            "anthropic/claude-3-haiku": {
                "max_tokens": 4096,
                "supports_tools": True,
                "supports_vision": True,
                "cost_per_1k_input": 0.00025,
                "cost_per_1k_output": 0.00125
            },
            "openai/gpt-4-turbo": {
                "max_tokens": 4096,
                "supports_tools": True,
                "supports_vision": True,
                "cost_per_1k_input": 0.01,
                "cost_per_1k_output": 0.03
            },
            "openai/gpt-3.5-turbo": {
                "max_tokens": 4096,
                "supports_tools": True,
                "supports_vision": False,
                "cost_per_1k_input": 0.0005,
                "cost_per_1k_output": 0.0015
            }
        }
        
        return model_configs.get(model, {
            "max_tokens": 2048,
            "supports_tools": False,
            "supports_vision": False,
            "cost_per_1k_input": 0.001,
            "cost_per_1k_output": 0.002
        })

    async def validate_model_access(self, model: str) -> bool:
        """Check if the model is accessible with current API key"""
        
        try:
            # Make a minimal request to test access
            test_messages = [
                {"role": "user", "content": "test"}
            ]
            
            response = await self.chat_completion(
                messages=test_messages,
                model=model,
                max_tokens=1
            )
            
            return True
        except Exception:
            return False
