"""Input validation utilities."""

import re
from typing import Optional
from ..config import ActorInput


class InputValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, help_text: Optional[str] = None):
        self.message = message
        self.field = field
        self.help_text = help_text
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "type": "validation_error",
            "error": self.message,
            "field": self.field,
        }


def _validate_no_injection_patterns(value: str) -> bool:
    """
    Check for actual prompt injection patterns, not just keywords.
    Relaxed to avoid false positives.
    """
    dangerous_patterns = [
        r'<script[\s>]',
        r'javascript:\s*[a-z_]\w*\s*\(',
        r'data:text/html\s*,',
    ]
    return not any(re.search(pattern, value, re.IGNORECASE | re.DOTALL) for pattern in dangerous_patterns)

def validate_input(actor_input: ActorInput) -> list[InputValidationError]:
    """Validate actor input and return list of errors."""
    errors = []

    if not actor_input.category:
        errors.append(InputValidationError(
            message="Category is required",
            field="category",
        ))
    else:
        if not _validate_no_injection_patterns(actor_input.category):
            errors.append(InputValidationError(
                message="Category contains potentially dangerous content",
                field="category",
            ))

    if not actor_input.my_brand:
        errors.append(InputValidationError(
            message="Brand name is required",
            field="myBrand",
        ))
    else:
        if not _validate_no_injection_patterns(actor_input.my_brand):
            errors.append(InputValidationError(
                message="Brand name contains potentially dangerous content",
                field="myBrand",
            ))

    if not actor_input.platforms:
        errors.append(InputValidationError(
            message="At least one platform is required",
            field="platforms",
        ))

    if not actor_input.prompts:
        errors.append(InputValidationError(
            message="At least one prompt is required",
            field="prompts",
        ))
    elif len(actor_input.prompts) > 3:
        errors.append(InputValidationError(
            message="Maximum 3 prompts allowed",
            field="prompts",
        ))
    else:
        for i, prompt in enumerate(actor_input.prompts):
            if not _validate_no_injection_patterns(prompt):
                errors.append(InputValidationError(
                    message=f"Prompt {i+1} contains potentially dangerous content",
                    field="prompts",
                ))

    if len(actor_input.competitors) > 5:
        errors.append(InputValidationError(
            message="Maximum 5 competitors allowed",
            field="competitors",
        ))
    else:
        for i, competitor in enumerate(actor_input.competitors):
            if not _validate_no_injection_patterns(competitor):
                errors.append(InputValidationError(
                    message=f"Competitor {i+1} contains potentially dangerous content",
                    field="competitors",
                ))

    return errors
