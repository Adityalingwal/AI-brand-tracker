"""Perplexity browser-based client (no API key needed)."""

import asyncio
from typing import Any, Optional
from .base import BaseBrowserClient, BrowserClientError


class PerplexityBrowserClient(BaseBrowserClient):
    """Browser-based client for Perplexity AI (perplexity.ai) - no login required."""

    @property
    def platform_name(self) -> str:
        return "perplexity"

    @property
    def base_url(self) -> str:
        return "https://www.perplexity.ai"

    @property
    def textbox_selector(self) -> str:
        return "#ask-input"

    async def _platform_init(self):
        """Handle Perplexity-specific initialization."""
        await asyncio.sleep(3)

        popup_selectors = [
            "button:has-text('Accept')",
            "button:has-text('Got it')",
            "button:has-text('Close')",
            "[aria-label='Close']",
        ]

        for selector in popup_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

        try:
            await self.page.wait_for_selector(self.textbox_selector, timeout=30000)
        except Exception as e:
            raise BrowserClientError(
                message=f"Perplexity page did not load properly: {e}",
                platform=self.platform_name,
                recoverable=False
            )

    async def _get_message_count(self) -> int:
        """Count the number of markdown response blocks."""
        try:
            elems = await self.page.query_selector_all("[id^='markdown-content']")
            return len(elems)
        except Exception:
            return 0

    async def _get_response_text(self) -> str:
        try:
            markdown_elems = await self.page.query_selector_all("[id^='markdown-content']")
            if markdown_elems:
                last_elem = markdown_elems[-1]
                text = await last_elem.inner_text()
                return text.strip() if text else ""

            return ""

        except Exception:
            return ""
