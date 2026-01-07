"""OpenAI (ChatGPT) client."""

from typing import Any
from openai import AsyncOpenAI
from .base import BasePlatformClient, QueryResult, PlatformError


class OpenAIClient(BasePlatformClient):
    """Client for OpenAI's ChatGPT API."""

    MODEL = "gpt-5.2"

    def __init__(self, api_key: str, logger: Any):
        super().__init__(api_key, logger)
        self.client = AsyncOpenAI(api_key=api_key)

    @property
    def platform_name(self) -> str:
        return "chatgpt"

    @property
    def model_name(self) -> str:
        return self.MODEL

    async def query(self, prompt: str) -> QueryResult:
        """Query ChatGPT with a prompt."""
        try:
            response = await self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.7,
            )

            content = response.choices[0].message.content or ""

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
            if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
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
