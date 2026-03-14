import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import Agent, Skill, Tool
from ..services.prompt_generator import PromptGenerator
from .exceptions import PromptGenerationError

logger = logging.getLogger(__name__)


class PromptComposer:
    """
    Composes system prompts by combining agent configuration with active skills and tools.
    Handles prompt templates, variable substitution, and channel-specific formatting.
    """
    
    def __init__(self):
        self.prompt_generator = PromptGenerator()
        
        # Channel-specific configurations
        self.channel_configs = {
            "web": {
                "max_context_length": 4000,
                "formatting": "markdown",
                "tone": "conversational",
                "response_style": "detailed"
            },
            "telegram": {
                "max_context_length": 2000,
                "formatting": "markdown",
                "tone": "concise",
                "response_style": "brief"
            },
            "voice": {
                "max_context_length": 3000,
                "formatting": "plain_text",
                "tone": "natural",
                "response_style": "spoken"
            }
        }
    
    async def compose_prompt(
        self,
        agent: Agent,
        skills: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        channel_type: str = "web",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Compose a complete system prompt for the agent.
        
        Args:
            agent: Agent configuration
            skills: List of enabled skills with their configurations
            tools: List of enabled tools with their configurations
            channel_type: Communication channel type
            context: Additional context for prompt composition
            
        Returns:
            Complete system prompt string
        """
        try:
            # Get channel configuration
            channel_config = self.channel_configs.get(channel_type, self.channel_configs["web"])
            
            # Build prompt components
            prompt_parts = []
            
            # 1. Base agent identity
            base_identity = self._build_base_identity(agent, channel_config)
            prompt_parts.append(base_identity)
            
            # 2. Skills section
            if skills:
                skills_section = await self._build_skills_section(skills, channel_config)
                prompt_parts.append(skills_section)
            
            # 3. Tools section
            if tools:
                tools_section = self._build_tools_section(tools, channel_config)
                prompt_parts.append(tools_section)
            
            # 4. Channel-specific instructions
            channel_instructions = self._build_channel_instructions(channel_type, channel_config)
            prompt_parts.append(channel_instructions)
            
            # 5. Behavioral guidelines
            guidelines = self._build_behavioral_guidelines(channel_config)
            prompt_parts.append(guidelines)
            
            # 6. Context-specific additions
            if context:
                context_section = self._build_context_section(context)
                prompt_parts.append(context_section)
            
            # Combine all parts
            full_prompt = "\n\n".join(filter(None, prompt_parts))
            
            # Truncate if necessary
            if len(full_prompt) > channel_config["max_context_length"]:
                full_prompt = self._truncate_prompt(full_prompt, channel_config["max_context_length"])
            
            logger.debug(f"Composed prompt for agent {agent.id} ({len(full_prompt)} chars)")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error composing prompt: {str(e)}")
            raise PromptGenerationError(f"Failed to compose prompt: {str(e)}")
    
    def _build_base_identity(self, agent: Agent, channel_config: Dict[str, Any]) -> str:
        """Build the base identity section of the prompt."""
        identity_parts = [
            f"You are {agent.name}, an AI assistant."
        ]
        
        if agent.description:
            identity_parts.append(agent.description)
        
        # Add channel-specific personality traits
        tone_instructions = {
            "conversational": "Be friendly, engaging, and conversational.",
            "concise": "Be direct and to the point.",
            "natural": "Speak naturally and clearly, avoiding complex formatting."
        }
        
        if channel_config["tone"] in tone_instructions:
            identity_parts.append(tone_instructions[channel_config["tone"]])
        
        return "\n".join(identity_parts)
    
    async def _build_skills_section(self, skills: List[Dict[str, Any]], channel_config: Dict[str, Any]) -> str:
        """Build the skills section of the prompt."""
        if not skills:
            return ""
        
        skills_parts = ["## Active Skills"]
        
        # Sort skills by proficiency level if available
        sorted_skills = sorted(skills, key=lambda x: x.get("proficiency_level", 1), reverse=True)
        
        for skill in sorted_skills:
            try:
                # Render skill template with configuration
                skill_prompt = self._render_skill_template(skill)
                
                skill_desc = f"**{skill['name']}**: {skill['description']}"
                if skill.get("proficiency_level"):
                    skill_desc += f" (Level {skill['proficiency_level']})"
                
                skills_parts.append(skill_desc)
                skills_parts.append(skill_prompt)
                skills_parts.append("")  # Empty line for readability
                
            except Exception as e:
                logger.warning(f"Error rendering skill {skill['name']}: {str(e)}")
                skills_parts.append(f"**{skill['name']}**: {skill['description']}")
                skills_parts.append("(Skill configuration error)")
                skills_parts.append("")
        
        return "\n".join(skills_parts)
    
    def _render_skill_template(self, skill: Dict[str, Any]) -> str:
        """Render skill template with configuration variables."""
        template = skill.get("system_prompt_template", "")
        config = skill.get("config", {})
        
        if not template:
            return skill.get("description", "")
        
        try:
            # Substitute template variables
            rendered = template
            for key, value in config.items():
                placeholder = f"{{{key}}}"
                if placeholder in rendered:
                    rendered = rendered.replace(placeholder, str(value))
            
            # Check for missing variables
            import re
            missing_vars = re.findall(r'\{([^}]+)\}', rendered)
            if missing_vars:
                logger.warning(f"Missing variables in skill {skill['name']}: {missing_vars}")
                for var in missing_vars:
                    rendered = rendered.replace(f"{{{var}}}", f"[MISSING: {var}]")
            
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering skill template for {skill['name']}: {str(e)}")
            return f"Error rendering skill template: {str(e)}"
    
    def _build_tools_section(self, tools: List[Dict[str, Any]], channel_config: Dict[str, Any]) -> str:
        """Build the tools section of the prompt."""
        if not tools:
            return ""
        
        tools_parts = ["## Available Tools"]
        
        for tool in tools:
            try:
                tool_desc = f"**{tool['name']}**: {tool['description']}"
                tools_parts.append(tool_desc)
                
                # Add usage instructions
                usage_info = self._extract_tool_usage(tool)
                tools_parts.append(f"Usage: {usage_info}")
                tools_parts.append("")  # Empty line for readability
                
            except Exception as e:
                logger.warning(f"Error processing tool {tool['name']}: {str(e)}")
                tools_parts.append(f"**{tool['name']}**: {tool['description']}")
                tools_parts.append("(Tool configuration error)")
                tools_parts.append("")
        
        # Add tool usage guidelines
        tools_parts.append("Tool Usage Guidelines:")
        tools_parts.append("- Use tools when they can help answer the user's question")
        tools_parts.append("- Call tools with the exact parameters specified")
        tools_parts.append("- If a tool fails, try alternative approaches")
        tools_parts.append("- Explain tool results to the user in natural language")
        
        return "\n".join(tools_parts)
    
    def _extract_tool_usage(self, tool: Dict[str, Any]) -> str:
        """Extract tool usage information from function schema."""
        function_schema = tool.get("function_schema", {})
        
        tool_name = function_schema.get("name", tool["name"])
        description = function_schema.get("description", "No description available")
        
        usage_parts = [f"Function: `{tool_name}`", f"Description: {description}"]
        
        parameters = function_schema.get("parameters", {})
        if parameters and "properties" in parameters:
            required_params = parameters.get("required", [])
            usage_parts.append("Parameters:")
            
            for param_name, param_info in parameters["properties"].items():
                param_type = param_info.get("type", "string")
                param_desc = param_info.get("description", "")
                required_indicator = " (required)" if param_name in required_params else " (optional)"
                usage_parts.append(f"  - {param_name}: {param_type}{required_indicator} - {param_desc}")
        
        return "\n".join(usage_parts)
    
    def _build_channel_instructions(self, channel_type: str, channel_config: Dict[str, Any]) -> str:
        """Build channel-specific instructions."""
        instructions = {
            "web": "You are communicating through a web interface. Use markdown formatting for better readability. Provide detailed, well-structured responses.",
            "telegram": "You are communicating through Telegram. Keep responses concise and use markdown formatting. Avoid very long messages.",
            "voice": "You are communicating through voice. Speak naturally and clearly. Use simple language and avoid complex formatting that doesn't translate well to speech."
        }
        
        base_instruction = instructions.get(channel_type, instructions["web"])
        
        # Add response style guidance
        style_guidance = {
            "detailed": "Provide comprehensive answers with explanations and examples.",
            "brief": "Keep responses short and to the point.",
            "spoken": "Use conversational language that sounds natural when spoken."
        }
        
        if channel_config["response_style"] in style_guidance:
            base_instruction += f"\n{style_guidance[channel_config['response_style']]}"
        
        return f"## Channel Instructions\n{base_instruction}"
    
    def _build_behavioral_guidelines(self, channel_config: Dict[str, Any]) -> str:
        """Build general behavioral guidelines."""
        guidelines = [
            "## Behavioral Guidelines",
            "- Be helpful, accurate, and respectful in all interactions",
            "- Admit when you don't know something or when you make mistakes",
            "- Learn from the conversation and adapt your responses accordingly",
            "- Maintain consistency with your defined personality and skills",
            "- Use your available tools when they can help provide better answers",
            "- Consider the communication channel when formatting responses",
            "- Prioritize user safety and privacy"
        ]
        
        # Add channel-specific guidelines
        if channel_config["formatting"] == "plain_text":
            guidelines.append("- Avoid complex markdown formatting that may not render well")
        
        return "\n".join(guidelines)
    
    def _build_context_section(self, context: Dict[str, Any]) -> str:
        """Build context-specific additions to the prompt."""
        if not context:
            return ""
        
        context_parts = ["## Current Context"]
        
        # Add time context
        if "current_time" in context:
            context_parts.append(f"Current time: {context['current_time']}")
        
        # Add user context
        if "user_context" in context:
            user_context = context["user_context"]
            if isinstance(user_context, dict):
                for key, value in user_context.items():
                    context_parts.append(f"User {key}: {value}")
            else:
                context_parts.append(f"User context: {user_context}")
        
        # Add conversation context
        if "conversation_context" in context:
            conv_context = context["conversation_context"]
            context_parts.append(f"Conversation context: {conv_context}")
        
        # Add custom context
        for key, value in context.items():
            if key not in ["current_time", "user_context", "conversation_context"]:
                context_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(context_parts)
    
    def _truncate_prompt(self, prompt: str, max_length: int) -> str:
        """Truncate prompt to fit within maximum length while preserving structure."""
        if len(prompt) <= max_length:
            return prompt
        
        # Try to truncate by removing less critical sections first
        lines = prompt.split('\n')
        truncated_lines = []
        current_length = 0
        
        # Priority: keep identity > skills > tools > guidelines > context
        section_priority = {
            "You are": 1,
            "## Active Skills": 2,
            "## Available Tools": 3,
            "## Behavioral Guidelines": 4,
            "## Channel Instructions": 5,
            "## Current Context": 6
        }
        
        current_section = 1
        for line in lines:
            # Check if we're starting a new section
            for section_header, priority in section_priority.items():
                if line.strip().startswith(section_header):
                    current_section = priority
                    break
            
            # Include line if we're within priority and length limits
            if current_section <= 3 or current_length + len(line) < max_length - 100:
                truncated_lines.append(line)
                current_length += len(line) + 1  # +1 for newline
            else:
                break
        
        truncated_prompt = '\n'.join(truncated_lines)
        
        # Add truncation notice
        if len(truncated_prompt) < len(prompt):
            truncated_prompt += "\n\n[Note: Some prompt sections were truncated to fit within context limits]"
        
        return truncated_prompt
    
    async def validate_prompt_composition(
        self,
        agent: Agent,
        skills: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        channel_type: str = "web"
    ) -> Dict[str, Any]:
        """
        Validate prompt composition and return diagnostic information.
        """
        try:
            prompt = await self.compose_prompt(agent, skills, tools, channel_type)
            
            diagnostics = {
                "valid": True,
                "prompt_length": len(prompt),
                "sections": {
                    "identity": bool("You are" in prompt),
                    "skills": bool("## Active Skills" in prompt),
                    "tools": bool("## Available Tools" in prompt),
                    "guidelines": bool("## Behavioral Guidelines" in prompt),
                    "channel_instructions": bool("## Channel Instructions" in prompt)
                },
                "skills_count": len(skills),
                "tools_count": len(tools),
                "channel_type": channel_type,
                "warnings": [],
                "errors": []
            }
            
            # Check for potential issues
            if len(prompt) > 3500:
                diagnostics["warnings"].append("Prompt is quite long, may affect performance")
            
            # Check for missing template variables
            for skill in skills:
                template = skill.get("system_prompt_template", "")
                if template:
                    import re
                    missing_vars = re.findall(r'\{([^}]+)\}', template)
                    config = skill.get("config", {})
                    for var in missing_vars:
                        if var not in config:
                            diagnostics["warnings"].append(f"Skill '{skill['name']}' missing variable: {var}")
            
            # Check tool schemas
            for tool in tools:
                schema = tool.get("function_schema", {})
                if not schema.get("name"):
                    diagnostics["errors"].append(f"Tool '{tool['name']}' missing function name")
            
            if diagnostics["errors"]:
                diagnostics["valid"] = False
            
            return diagnostics
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "prompt_length": 0,
                "sections": {},
                "skills_count": 0,
                "tools_count": 0,
                "warnings": [],
                "errors": [str(e)]
            }
