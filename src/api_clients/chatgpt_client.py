"""ChatGPT platform client backed by the configured OpenAI API key."""

import asyncio
import os
from typing import Any, Optional

from openai import AsyncOpenAI

from ..browser_clients.base import BrowserClientError, BrowserQueryResult
from ..utils import sanitize_error_message


class ChatGPTApiClient:
    """Low-latency ChatGPT query client with the same public interface as browser clients."""

    uses_browser = False

    def __init__(
        self,
        logger: Any,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[AsyncOpenAI] = None,
    ):
        self.logger = logger
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_CHATGPT_MODEL", "gpt-4.1-nano")
        self.client = client

    @property
    def platform_name(self) -> str:
        return "chatgpt"

    async def initialize(self):
        """Prepare the query client."""
        if not self.api_key:
            raise BrowserClientError(
                message="Internal query service is not configured",
                platform=self.platform_name,
                recoverable=False,
            )

        if not self.client:
            self.client = AsyncOpenAI(api_key=self.api_key, max_retries=0)

    async def query(self, prompt: str) -> BrowserQueryResult:
        """Send a prompt and return the generated response."""
        if not self.client:
            await self.initialize()

        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=1800,
                    temperature=0.2,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are ChatGPT. Answer the user's prompt directly, neutrally, "
                                "and with enough detail for brand visibility analysis. When the "
                                "prompt asks for recommendations or comparisons, include specific "
                                "brands, tradeoffs, and concise reasoning. Do not mention internal "
                                "systems or implementation details."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                ),
                timeout=90.0,
            )

            response_text = response.choices[0].message.content or ""
            response_text = response_text.strip()

            if not response_text:
                return BrowserQueryResult(
                    platform=self.platform_name,
                    prompt=prompt,
                    response="",
                    success=False,
                    error=f"Empty response received from {self.platform_name}",
                )

            return BrowserQueryResult(
                platform=self.platform_name,
                prompt=prompt,
                response=response_text,
                success=True,
            )

        except Exception as e:
            return BrowserQueryResult(
                platform=self.platform_name,
                prompt=prompt[:200] if prompt else "",
                response="",
                success=False,
                error=sanitize_error_message(e),
            )

    async def query_with_retry(self, prompt: str, max_retries: int = 1) -> BrowserQueryResult:
        """Retry transient API failures without restarting browser/proxy sessions."""
        last_result = None

        for attempt in range(max_retries + 1):
            result = await self.query(prompt)
            if result.success:
                return result

            last_result = result
            if attempt < max_retries:
                self.logger.warning(
                    f"[{self.platform_name}] Retrying prompt after failure: {result.error}"
                )
                await asyncio.sleep(2)

        return last_result

    async def close(self):
        """No browser resources to close."""
        self.client = None
