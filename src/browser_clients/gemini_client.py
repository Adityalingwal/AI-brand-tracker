"""Google Gemini browser-based client (no API key needed)."""

import asyncio
from typing import Any, Optional
from .base import BaseBrowserClient, BrowserClientError


class GeminiBrowserClient(BaseBrowserClient):
    """Browser-based client for Google Gemini (gemini.google.com) - no login required."""

    @property
    def platform_name(self) -> str:
        return "gemini"

    @property
    def base_url(self) -> str:
        return "https://gemini.google.com"

    @property
    def textbox_selector(self) -> str:
        return "rich-textarea .ql-editor"

    async def _platform_init(self):
        """Handle Gemini-specific initialization."""
        await asyncio.sleep(3)

        cookie_selectors = [
            "button:has-text('Accept all')",
            "button:has-text('I agree')",
            "button:has-text('Got it')",
        ]

        for selector in cookie_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    self.logger.info(f"  Dismissed: {selector}")
                    await asyncio.sleep(1)
                    break
            except Exception:
                pass

        try:
            try_btn = await self.page.query_selector("button:has-text('Try Gemini')")
            if try_btn:
                await try_btn.click()
                self.logger.info("  Clicked 'Try Gemini'")
                await asyncio.sleep(2)
        except Exception:
            pass

        try:
            await self.page.wait_for_selector(self.textbox_selector, timeout=15000)
            self.logger.info("  Gemini ready")
        except Exception as e:
            raise BrowserClientError(
                message=f"Gemini page did not load properly: {e}",
                platform=self.platform_name,
                recoverable=False
            )

    async def _get_response_text(self) -> str:
        """Extract response text with fallback selectors."""
        try:
            responses = await self.page.query_selector_all("model-response")

            if responses:
                last_response = responses[-1]
                text = await last_response.inner_text()
                if text and text.strip():
                    return text.strip()

            content = await self.page.query_selector("structured-content-container")
            if content:
                text = await content.inner_text()
                return text.strip() if text else ""

            container = await self.page.query_selector(".presented-response-container")
            if container:
                text = await container.inner_text()
                return text.strip() if text else ""

            return ""

        except Exception as e:
            self.logger.warning(f"  Response extraction error: {e}")
            return ""
