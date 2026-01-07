"""Base class for AI platform clients."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any


class PlatformError(Exception):
    """Error from an AI platform."""

    def __init__(self, message: str, platform: str, recoverable: bool = True):
        self.message = message
        self.platform = platform
        self.recoverable = recoverable
        super().__init__(message)


@dataclass
class QueryResult:
    """Result from querying an AI platform."""
    platform: str
    model: str
    prompt: str
    response: str
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "model": self.model,
            "prompt": self.prompt,
            "response": self.response,
            "success": self.success,
            "error": self.error,
        }


class BasePlatformClient(ABC):
    """Abstract base class for AI platform clients."""

    def __init__(self, api_key: str, logger: Any):
        self.api_key = api_key
        self.logger = logger

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the platform."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model being used."""
        pass

    @abstractmethod
    async def query(self, prompt: str) -> QueryResult:
        """
        Send a prompt to the AI platform and get a response.

        Args:
            prompt: The prompt to send

        Returns:
            QueryResult with the response
        """
        pass

    async def query_with_retry(self, prompt: str, max_retries: int = 3) -> QueryResult:
        """
        Query with exponential backoff retry.

        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retries

        Returns:
            QueryResult with the response
        """
        import asyncio

        last_error = None
        for attempt in range(max_retries):
            try:
                result = await self.query(prompt)
                if result.success:
                    return result
                last_error = result.error
            except PlatformError as e:
                last_error = e.message
                if not e.recoverable:
                    break
            except Exception as e:
                last_error = str(e)

            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s
                self.logger.warning(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                await asyncio.sleep(wait_time)

        return QueryResult(
            platform=self.platform_name,
            model=self.model_name,
            prompt=prompt,
            response="",
            success=False,
            error=last_error or "Unknown error after retries",
        )
