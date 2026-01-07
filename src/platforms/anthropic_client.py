"""Anthropic (Claude) client."""

from typing import Any
from anthropic import AsyncAnthropic
from .base import BasePlatformClient, QueryResult, PlatformError


class AnthropicClient(BasePlatformClient):
    """Client for Anthropic's Claude API."""

    MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str, logger: Any):
        super().__init__(api_key, logger)
        self.client = AsyncAnthropic(api_key=api_key)

    @property
    def platform_name(self) -> str:
        return "claude"

    @property
    def model_name(self) -> str:
        return self.MODEL

    async def query(self, prompt: str) -> QueryResult:
        """Query Claude with a prompt."""
        try:
            response = await self.client.messages.create(
                model=self.MODEL,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )

            # Extract text from response
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            return QueryResult(
                platform=self.platform_name,
                model=self.model_name,
                prompt=prompt,
                response=content,
                success=True,
            )

        except Exception as e:
            error_msg = str(e)

            # Check for rate limit
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                raise PlatformError(
                    message=f"Rate limit exceeded: {error_msg}",
                    platform=self.platform_name,
                    recoverable=True,
                )

            # Check for invalid API key
            if "invalid" in error_msg.lower() and "key" in error_msg.lower():
                raise PlatformError(
                    message=f"Invalid API key: {error_msg}",
                    platform=self.platform_name,
                    recoverable=False,
                )

            return QueryResult(
                platform=self.platform_name,
                model=self.model_name,
                prompt=prompt,
                response="",
                success=False,
                error=error_msg,
            )
