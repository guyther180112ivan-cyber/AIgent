"""Custom exceptions for the Agent Runtime."""


class AgentRuntimeError(Exception):
    """Base exception for Agent Runtime errors."""
    pass


class SkillLoadError(AgentRuntimeError):
    """Raised when there's an error loading skills."""
    pass


class ToolExecutionError(AgentRuntimeError):
    """Raised when tool execution fails."""
    pass


class PromptGenerationError(AgentRuntimeError):
    """Raised when prompt generation fails."""
    pass


class LLMServiceError(AgentRuntimeError):
    """Raised when LLM service encounters an error."""
    pass


class ConfigurationError(AgentRuntimeError):
    """Raised when there's a configuration error."""
    pass


class ValidationError(AgentRuntimeError):
    """Raised when validation fails."""
    pass


class RateLimitError(AgentRuntimeError):
    """Raised when rate limits are exceeded."""
    pass


class AuthenticationError(AgentRuntimeError):
    """Raised when authentication fails."""
    pass


class PermissionError(AgentRuntimeError):
    """Raised when permissions are insufficient."""
    pass
