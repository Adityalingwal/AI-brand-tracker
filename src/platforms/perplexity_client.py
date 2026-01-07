"""Perplexity AI client."""

from typing import Any
import httpx
from .base import BasePlatformClient, QueryResult, PlatformError


class PerplexityClient(BasePlatformClient):
    """Client for Perplexity AI API."""

    MODEL = "llama-3.1-sonar-large-128k-online"
    API_URL = "https://api.perplexity.ai/chat/completions"

    def __init__(self, api_key: str, logger: Any):
        super().__init__(api_key, logger)

    @property
    def platform_name(self) -> str:
        return "perplexity"

    @property
    def model_name(self) -> str:
        return self.MODEL

    async def query(self, prompt: str) -> QueryResult:
        """Query Perplexity with a prompt."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.MODEL,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 2048,
                        "temperature": 0.7,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                    return QueryResult(
                        platform=self.platform_name,
                        model=self.model_name,
                        prompt=prompt,
                        response=content,
                        success=True,
                    )

                elif response.status_code == 429:
                    raise PlatformError(
                        message="Rate limit exceeded",
                        platform=self.platform_name,
                        recoverable=True,
                    )

                elif response.status_code == 401:
                    raise PlatformError(
                        message="Invalid API key",
                        platform=self.platform_name,
                        recoverable=False,
                    )

                else:
                    return QueryResult(
                        platform=self.platform_name,
                        model=self.model_name,
                        prompt=prompt,
                        response="",
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}",
                    )

        except PlatformError:
            raise
        except Exception as e:
            return QueryResult(
                platform=self.platform_name,
                model=self.model_name,
                prompt=prompt,
                response="",
                success=False,
                error=str(e),
            )
