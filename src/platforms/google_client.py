"""Google (Gemini) client."""

from typing import Any
import google.generativeai as genai
from .base import BasePlatformClient, QueryResult, PlatformError


class GoogleClient(BasePlatformClient):
    """Client for Google's Gemini API."""

    MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: str, logger: Any):
        super().__init__(api_key, logger)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.MODEL)

    @property
    def platform_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self.MODEL

    async def query(self, prompt: str) -> QueryResult:
        """Query Gemini with a prompt."""
        try:
            # Gemini's generate_content is synchronous, run in executor
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )

            content = response.text if response.text else ""

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
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise PlatformError(
                    message=f"Rate limit exceeded: {error_msg}",
                    platform=self.platform_name,
                    recoverable=True,
                )

            # Check for invalid API key
            if "api key" in error_msg.lower() and ("invalid" in error_msg.lower() or "not valid" in error_msg.lower()):
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
