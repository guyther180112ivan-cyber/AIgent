from typing import List, Dict, Any
from ..models import Agent, Skill, Tool


class PromptGenerator:
    """Service for generating dynamic system prompts based on agent's skills and tools"""
    
    def __init__(self):
        self.base_template = """You are {agent_name}, an AI assistant.
{agent_description}

Your personality and capabilities are defined by your active skills and tools."""

        self.skill_template = """
**{skill_name}**: {skill_description}
{skill_prompt}
"""

        self.tool_template = """
**{tool_name}**: {tool_description}
Usage: {tool_usage}
"""

        self.channel_templates = {
            "web": "You are communicating through a web interface. Respond in a friendly, conversational manner.",
            "telegram": "You are communicating through Telegram. Keep responses concise and use markdown formatting when appropriate.",
            "voice": "You are communicating through voice. Speak naturally and clearly, avoiding complex markdown formatting."
        }

        self.system_instructions = """
Guidelines:
- Be helpful, accurate, and respectful
- Use your available tools when they can help answer the user's question
- If you don't know something, admit it
- Keep responses appropriate for the communication channel
- Learn from the conversation and adapt your responses accordingly
"""

    def generate_system_prompt(
        self,
        agent: Agent,
        skills: List[Skill],
        tools: List[Tool],
        channel_type: str = "web"
    ) -> str:
        """Generate complete system prompt for agent"""
        
        # Start with base template
        prompt_parts = [
            self.base_template.format(
                agent_name=agent.name,
                agent_description=agent.description or "You are a helpful AI assistant."
            )
        ]

        # Add skills section
        if skills:
            prompt_parts.append("\n## Active Skills")
            for skill in skills:
                skill_prompt = self._format_skill_prompt(skill)
                prompt_parts.append(skill_prompt)

        # Add tools section
        if tools:
            prompt_parts.append("\n## Available Tools")
            for tool in tools:
                tool_prompt = self._format_tool_prompt(tool)
                prompt_parts.append(tool_prompt)

        # Add channel-specific instructions
        channel_instructions = self.channel_templates.get(channel_type, self.channel_templates["web"])
        prompt_parts.append(f"\n## Channel Instructions\n{channel_instructions}")

        # Add system instructions
        prompt_parts.append(f"\n## System Instructions{self.system_instructions}")

        return "\n".join(prompt_parts)

    def _format_skill_prompt(self, skill: Skill) -> str:
        """Format individual skill prompt"""
        return self.skill_template.format(
            skill_name=skill.name,
            skill_description=skill.description,
            skill_prompt=skill.system_prompt_template
        )

    def _format_tool_prompt(self, tool: Tool) -> str:
        """Format individual tool prompt"""
        function_schema = tool.function_schema
        
        # Extract tool usage information from schema
        tool_usage = self._extract_tool_usage(function_schema)
        
        return self.tool_template.format(
            tool_name=tool.name,
            tool_description=tool.description,
            tool_usage=tool_usage
        )

    def _extract_tool_usage(self, function_schema: Dict[str, Any]) -> str:
        """Extract tool usage information from function schema"""
        tool_name = function_schema.get("name", "unknown")
        description = function_schema.get("description", "No description available")
        parameters = function_schema.get("parameters", {})
        
        usage_parts = [f"Function: `{tool_name}`"]
        usage_parts.append(f"Description: {description}")
        
        if parameters and "properties" in parameters:
            required_params = parameters.get("required", [])
            usage_parts.append("Parameters:")
            
            for param_name, param_info in parameters["properties"].items():
                param_type = param_info.get("type", "string")
                param_desc = param_info.get("description", "")
                required_indicator = " (required)" if param_name in required_params else " (optional)"
                usage_parts.append(f"  - {param_name}: {param_type}{required_indicator} - {param_desc}")
        
        return "\n".join(usage_parts)

    def update_agent_prompt(
        self,
        agent: Agent,
        skills: List[Skill],
        tools: List[Tool],
        channel_type: str = "web",
        db_session = None
    ) -> str:
        """Update agent's system prompt and return it"""
        new_prompt = self.generate_system_prompt(agent, skills, tools, channel_type)
        
        # Update agent in database if session provided
        if db_session:
            agent.system_prompt = new_prompt
            db_session.commit()
        
        return new_prompt

    def validate_skill_template(self, template: str) -> List[str]:
        """Validate skill template and return list of errors"""
        errors = []
        
        # Basic checks
        if not template or not template.strip():
            errors.append("Template cannot be empty")
        
        # Check for dangerous content
        dangerous_patterns = [
            "ignore previous instructions",
            "disregard",
            "forget",
            "system prompt",
            "admin access"
        ]
        
        template_lower = template.lower()
        for pattern in dangerous_patterns:
            if pattern in template_lower:
                errors.append(f"Template contains potentially dangerous pattern: {pattern}")
        
        return errors

    def get_skill_variables(self, template: str) -> List[str]:
        """Extract variables from skill template using {variable} syntax"""
        import re
        
        pattern = r'\{([^}]+)\}'
        variables = re.findall(pattern, template)
        return list(set(variables))

    def render_skill_template(self, template: str, config: Dict[str, Any]) -> str:
        """Render skill template with provided configuration"""
        try:
            return template.format(**config)
        except KeyError as e:
            # Return template with missing variables highlighted
            missing_var = str(e).strip("'\"")
            return template.replace(f"{{{missing_var}}}", f"[MISSING: {missing_var}]")
        except Exception as e:
            return f"Error rendering template: {str(e)}\n\nOriginal template:\n{template}"
