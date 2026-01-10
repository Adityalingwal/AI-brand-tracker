"""Browser-based AI platform clients (no API keys needed)."""

from .base import BaseBrowserClient, BrowserQueryResult
from .chatgpt_client import ChatGPTBrowserClient
from .perplexity_client import PerplexityBrowserClient
from .gemini_client import GeminiBrowserClient

__all__ = [
    "BaseBrowserClient",
    "BrowserQueryResult",
    "ChatGPTBrowserClient",
    "PerplexityBrowserClient",
    "GeminiBrowserClient",
]
