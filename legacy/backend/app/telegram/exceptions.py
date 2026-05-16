"""Custom exceptions for Telegram bot."""


class TelegramBotError(Exception):
    """Base exception for Telegram bot errors."""
    pass


class TelegramAuthError(TelegramBotError):
    """Raised when there's an authentication error."""
    pass


class UserNotLinkedError(TelegramBotError):
    """Raised when user is not linked to platform account."""
    pass


class VoiceProcessingError(TelegramBotError):
    """Raised when voice processing fails."""
    pass


class WebhookError(TelegramBotError):
    """Raised when webhook processing fails."""
    pass


class MessageProcessingError(TelegramBotError):
    """Raised when message processing fails."""
    pass
