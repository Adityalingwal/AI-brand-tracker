"""Browser-based AI platform clients (no API keys needed)."""

from .base import BaseBrowserClient, BrowserQueryResult
from .chatgpt_client import ChatGPTBrowserClient
from .perplexity_client import PerplexityBrowserClient

__all__ = [
    "BaseBrowserClient",
    "BrowserQueryResult",
    "ChatGPTBrowserClient",
    "PerplexityBrowserClient",
]
