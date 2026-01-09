"""Browser-based AI platform clients (no API keys needed)."""

from .base import BaseBrowserClient, BrowserQueryResult
from .chatgpt_client import ChatGPTBrowserClient

__all__ = [
    "BaseBrowserClient",
    "BrowserQueryResult",
    "ChatGPTBrowserClient",
]
