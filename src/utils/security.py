"""Security utilities for sanitizing error messages and sensitive data."""


def sanitize_error_message(error: Exception, max_length: int = 200) -> str:
    """
    Sanitize error message to remove sensitive data like API keys.

    Args:
        error: Exception object
        max_length: Maximum length of error message

    Returns:
        Sanitized error message string
    """
    error_msg = str(error)[:max_length]

    sensitive_patterns = ["api_key", "sk-ant", "anthropic", "token", "secret", "password"]

    if any(pattern in error_msg.lower() for pattern in sensitive_patterns):
        return "Internal error occurred"

    return error_msg
