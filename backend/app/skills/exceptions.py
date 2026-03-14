"""Custom exceptions for the Skills system."""


class SkillError(Exception):
    """Base exception for Skills system errors."""
    pass


class SkillNotFoundError(SkillError):
    """Raised when a skill is not found."""
    pass


class SkillAlreadyExistsError(SkillError):
    """Raised when trying to create a skill that already exists."""
    pass


class SkillConfigurationError(SkillError):
    """Raised when there's an error in skill configuration."""
    pass


class SkillPermissionError(SkillError):
    """Raised when user doesn't have permission to perform an action."""
    pass


class SkillTemplateError(SkillError):
    """Raised when there's an error with skill templates."""
    pass


class SkillMergeError(SkillError):
    """Raised when there's an error merging skill prompts."""
    pass


class SkillValidationError(SkillError):
    """Raised when skill validation fails."""
    pass
