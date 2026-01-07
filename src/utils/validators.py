"""Input validation utilities."""

from typing import Optional
from ..config import ActorInput, Platform


class InputValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, help_text: Optional[str] = None):
        self.message = message
        self.field = field
        self.help_text = help_text
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert to output dictionary."""
        return {
            "type": "validation_error",
            "status": "validation_error",
            "error": self.message,
            "field": self.field,
            "help": self.help_text,
        }


def validate_input(actor_input: ActorInput) -> list[InputValidationError]:
    """
    Validate actor input and return list of errors.

    Returns empty list if input is valid.
    """
    errors = []

    # Check required fields
    if not actor_input.category:
        errors.append(InputValidationError(
            message="Category is required",
            field="category",
            help_text="Example: 'CRM software', 'project management tools'"
        ))

    if not actor_input.your_brand:
        errors.append(InputValidationError(
            message="Your brand name is required",
            field="yourBrand",
            help_text="Example: 'Salesforce', 'HubSpot'"
        ))

    if not actor_input.platforms:
        errors.append(InputValidationError(
            message="At least one AI platform must be selected",
            field="platforms",
            help_text="Select from: ChatGPT, Claude, Gemini, Perplexity"
        ))

    # Check API keys for selected platforms
    platform_key_map = {
        Platform.CHATGPT: ("openaiApiKey", "OpenAI API key"),
        Platform.CLAUDE: ("anthropicApiKey", "Anthropic API key"),
        Platform.GEMINI: ("googleApiKey", "Google AI API key"),
        Platform.PERPLEXITY: ("perplexityApiKey", "Perplexity API key"),
    }

    for platform in actor_input.platforms:
        key = actor_input.api_keys.get_key_for_platform(platform)
        if not key:
            field_name, key_name = platform_key_map.get(platform, ("", "API key"))
            errors.append(InputValidationError(
                message=f"{key_name} is required for {platform.value}",
                field=field_name,
                help_text=f"Provide your {key_name} to use {platform.value}"
            ))

    # Validate prompt count
    if actor_input.prompt_count < 1:
        errors.append(InputValidationError(
            message="Prompt count must be at least 1",
            field="promptCount",
            help_text="Minimum: 1, Maximum: 50"
        ))
    elif actor_input.prompt_count > 50:
        errors.append(InputValidationError(
            message="Prompt count cannot exceed 50",
            field="promptCount",
            help_text="Minimum: 1, Maximum: 50"
        ))

    # Validate competitors count
    if len(actor_input.competitors) > 10:
        errors.append(InputValidationError(
            message="Maximum 10 competitors allowed",
            field="competitors",
            help_text="Reduce the number of competitor brands"
        ))

    return errors
