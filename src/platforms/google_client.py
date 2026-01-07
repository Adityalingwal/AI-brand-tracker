"""Google (Gemini) client using the new google-genai SDK."""

from typing import Any
from google import genai
from google.genai import types
from .base import BasePlatformClient, QueryResult, PlatformError


class GoogleClient(BasePlatformClient):
    """Client for Google's Gemini API using the new unified SDK."""

    MODEL = "gemini-3-pro-preview"

    def __init__(self, api_key: str, logger: Any):
        super().__init__(api_key, logger)
        self.client = genai.Client(api_key=api_key)

    @property
    def platform_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self.MODEL

    async def query(self, prompt: str) -> QueryResult:
        """Query Gemini with a prompt."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=2048,
                        temperature=0.7,
                    )
                )
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

            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise PlatformError(
                    message=f"Rate limit exceeded: {error_msg}",
                    platform=self.platform_name,
                    recoverable=True,
                )

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
