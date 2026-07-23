"""Shared OpenRouter client configuration."""

import os
from typing import Optional

from openai import AsyncOpenAI


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_APP_URL = "https://apify.com/adityalingwal/ai-brand-visibility"
OPENROUTER_APP_TITLE = "AI Brand Visibility"


def get_openrouter_api_key() -> Optional[str]:
    """Read the OpenRouter API key from the runtime environment."""
    return os.environ.get("OPENROUTER_API_KEY")


def create_openrouter_client(api_key: Optional[str] = None) -> Optional[AsyncOpenAI]:
    """Create the shared OpenAI-compatible client pointed at OpenRouter."""
    resolved_key = api_key or get_openrouter_api_key()
    if not resolved_key:
        return None

    return AsyncOpenAI(
        api_key=resolved_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": OPENROUTER_APP_URL,
            "X-OpenRouter-Title": OPENROUTER_APP_TITLE,
        },
        # Query and analysis layers own their bounded retry behavior.
        max_retries=0,
    )
