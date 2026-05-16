import asyncio
import logging
import json
import importlib
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import traceback
import httpx
from abc import ABC, abstractmethod

from .exceptions import ToolExecutionError

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for all tools that can be executed by the agent."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the tool with given arguments."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return the function schema for this tool."""
        pass
    
    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """Validate arguments against the tool schema."""
        schema = self.get_schema()
        required_params = schema.get("parameters", {}).get("required", [])
        
        for param in required_params:
            if param not in arguments:
                raise ToolExecutionError(f"Missing required parameter: {param}")
        
        return True


class WebSearchTool(BaseTool):
    """Web search tool implementation."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key")
        self.search_engine = self.config.get("search_engine", "duckduckgo")
        self.max_results = self.config.get("max_results", 5)
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web search."""
        try:
            query = arguments.get("query")
            if not query:
                raise ToolExecutionError("Search query is required")
            
            num_results = arguments.get("num_results", self.max_results)
            
            # Use DuckDuckGo (free, no API key required)
            if self.search_engine == "duckduckgo":
                results = await self._duckduckgo_search(query, num_results)
            else:
                # Placeholder for other search engines
                results = await self._generic_search(query, num_results)
            
            return {
                "query": query,
                "results": results,
                "count": len(results),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            raise ToolExecutionError(f"Web search failed: {str(e)}")
    
    async def _duckduckgo_search(self, query: str, num_results: int) -> list:
        """Perform DuckDuckGo search."""
        try:
            # Use DuckDuckGo's HTML version (no API key required)
            url = "https://duckduckgo.com/html/"
            params = {
                "q": query,
                "kl": "us-en"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                # Parse HTML results (simplified parsing)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                results = []
                result_elements = soup.find_all('div', class_='result')[:num_results]
                
                for element in result_elements:
                    title_elem = element.find('a', class_='result__a')
                    snippet_elem = element.find('a', class_='result__snippet')
                    
                    if title_elem:
                        result = {
                            "title": title_elem.get_text(strip=True),
                            "url": title_elem.get('href', ''),
                            "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                        }
                        results.append(result)
                
                return results
                
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {str(e)}")
            # Fallback to generic search
            return await self._generic_search(query, num_results)
    
    async def _generic_search(self, query: str, num_results: int) -> list:
        """Generic search fallback."""
        # This would integrate with other search APIs
        return [
            {
                "title": f"Search results for: {query}",
                "url": "https://example.com",
                "snippet": f"This is a placeholder result for the query: {query}"
            }
        ]
    
    def get_schema(self) -> Dict[str, Any]:
        """Return function schema."""
        return {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }


class CalculatorTool(BaseTool):
    """Calculator tool for mathematical operations."""
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mathematical calculation."""
        try:
            expression = arguments.get("expression")
            if not expression:
                raise ToolExecutionError("Mathematical expression is required")
            
            # Safe evaluation of mathematical expressions
            allowed_names = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "len": len,
                "pow": pow,
            }
            
            # Add math functions
            import math
            math_functions = {
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "sqrt": math.sqrt,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e
            }
            allowed_names.update(math_functions)
            
            # Evaluate expression safely
            result = eval(expression, allowed_names, {})
            
            return {
                "expression": expression,
                "result": result,
                "result_type": type(result).__name__,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Calculator error: {str(e)}")
            raise ToolExecutionError(f"Calculation failed: {str(e)}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Return function schema."""
        return {
            "name": "calculator",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sin(pi/2)', 'sqrt(16)')"
                    }
                },
                "required": ["expression"]
            }
        }


class WeatherTool(BaseTool):
    """Weather information tool."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key")
        self.units = self.config.get("units", "metric")
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather information."""
        try:
            location = arguments.get("location")
            if not location:
                raise ToolExecutionError("Location is required")
            
            units = arguments.get("units", self.units)
            
            # Use OpenWeatherMap API (requires API key)
            if self.api_key:
                weather_data = await self._get_weather_from_api(location, units)
            else:
                # Fallback to mock data
                weather_data = await self._get_mock_weather(location, units)
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Weather tool error: {str(e)}")
            raise ToolExecutionError(f"Weather lookup failed: {str(e)}")
    
    async def _get_weather_from_api(self, location: str, units: str) -> Dict[str, Any]:
        """Get weather from OpenWeatherMap API."""
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": units
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                return {
                    "location": data["name"],
                    "country": data["sys"]["country"],
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data.get("wind", {}).get("speed", 0),
                    "units": units,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.warning(f"Weather API failed: {str(e)}")
            return await self._get_mock_weather(location, units)
    
    async def _get_mock_weather(self, location: str, units: str) -> Dict[str, Any]:
        """Get mock weather data."""
        import random
        
        temp = round(random.uniform(15, 25), 1) if units == "metric" else round(random.uniform(59, 77), 1)
        humidity = random.randint(30, 80)
        
        descriptions = ["clear sky", "few clouds", "scattered clouds", "broken clouds", "shower rain", "thunderstorm"]
        description = random.choice(descriptions)
        
        return {
            "location": location,
            "country": "Unknown",
            "temperature": temp,
            "feels_like": temp + random.uniform(-2, 2),
            "humidity": humidity,
            "pressure": random.randint(1000, 1020),
            "description": description,
            "wind_speed": random.uniform(0, 10),
            "units": units,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "This is mock data as no weather API key was provided"
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return function schema."""
        return {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or coordinates (e.g., 'London', 'New York', '40.7128,-74.0060')"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "description": "Temperature units",
                        "default": "metric"
                    }
                },
                "required": ["location"]
            }
        }


class ToolExecutor:
    """
    Main tool executor that manages tool registration and execution.
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.tool_configs: Dict[str, Dict[str, Any]] = {}
        self.execution_stats: Dict[str, Dict[str, Any]] = {}
        
        # Register built-in tools
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in tools."""
        builtin_tools = {
            "web_search": WebSearchTool,
            "calculator": CalculatorTool,
            "get_weather": WeatherTool
        }
        
        for tool_name, tool_class in builtin_tools.items():
            self.register_tool(tool_name, tool_class)
    
    def register_tool(self, tool_name: str, tool_class: type, config: Dict[str, Any] = None):
        """Register a new tool."""
        try:
            tool_instance = tool_class(config or {})
            self.tools[tool_name] = tool_instance
            self.tool_configs[tool_name] = config or {}
            self.execution_stats[tool_name] = {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0,
                "last_used": None
            }
            logger.info(f"Registered tool: {tool_name}")
        except Exception as e:
            logger.error(f"Failed to register tool {tool_name}: {str(e)}")
            raise ToolExecutionError(f"Failed to register tool: {str(e)}")
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        tool_config: Dict[str, Any],
        user_id: str
    ) -> Any:
        """
        Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool
            tool_config: Tool configuration
            user_id: User ID for logging/permissions
            
        Returns:
            Tool execution result
        """
        start_time = datetime.utcnow()
        
        try:
            # Check if tool is registered
            if tool_name not in self.tools:
                raise ToolExecutionError(f"Tool '{tool_name}' is not registered")
            
            tool = self.tools[tool_name]
            
            # Validate arguments
            tool.validate_arguments(arguments)
            
            # Execute tool
            logger.info(f"Executing tool {tool_name} for user {user_id}")
            result = await tool.execute(arguments)
            
            # Update stats
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_stats(tool_name, True, execution_time)
            
            logger.info(f"Tool {tool_name} executed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_stats(tool_name, False, execution_time)
            
            logger.error(f"Tool {tool_name} execution failed: {str(e)}")
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")
    
    def _update_stats(self, tool_name: str, success: bool, execution_time: float):
        """Update tool execution statistics."""
        if tool_name not in self.execution_stats:
            return
        
        stats = self.execution_stats[tool_name]
        stats["executions"] += 1
        stats["total_time"] += execution_time
        stats["last_used"] = datetime.utcnow().isoformat()
        
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
        
        # Calculate average time
        stats["average_time"] = stats["total_time"] / stats["executions"]
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the function schema for a tool."""
        if tool_name in self.tools:
            return self.tools[tool_name].get_schema()
        return None
    
    def get_all_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get all tool schemas."""
        schemas = {}
        for tool_name, tool in self.tools.items():
            schemas[tool_name] = tool.get_schema()
        return schemas
    
    def get_tool_stats(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Get execution statistics for tools."""
        if tool_name:
            return self.execution_stats.get(tool_name, {})
        return self.execution_stats
    
    def list_registered_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())
    
    async def validate_tool_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate tool execution without actually running it.
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check if tool exists
            if tool_name not in self.tools:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Tool '{tool_name}' is not registered")
                return validation_result
            
            tool = self.tools[tool_name]
            schema = tool.get_schema()
            
            # Validate arguments against schema
            try:
                tool.validate_arguments(arguments)
            except ToolExecutionError as e:
                validation_result["valid"] = False
                validation_result["errors"].append(str(e))
            
            # Check for unexpected arguments
            expected_params = set(schema.get("parameters", {}).get("properties", {}).keys())
            provided_params = set(arguments.keys())
            unexpected_params = provided_params - expected_params
            
            if unexpected_params:
                validation_result["warnings"].append(f"Unexpected parameters: {list(unexpected_params)}")
            
            return validation_result
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
            return validation_result
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Tool executor cleanup completed")
