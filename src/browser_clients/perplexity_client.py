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

        # Handle any cookie/popup banners
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
                    self.logger.info(f"  Dismissed popup: {selector}")
                    await asyncio.sleep(1)
            except Exception:
                pass

        # Wait for textbox to be ready
        try:
            await self.page.wait_for_selector(self.textbox_selector, timeout=15000)
            self.logger.info("  Perplexity ready")
        except Exception as e:
            raise BrowserClientError(
                message=f"Perplexity page did not load properly: {e}",
                platform=self.platform_name,
                recoverable=False
            )

    async def _get_response_text(self) -> str:
        """Get the text from Perplexity's response."""
        try:
            # Try the specific response content selector first
            response_elem = await self.page.query_selector("#markdown-content-0 > div > div > div")
            if response_elem:
                text = await response_elem.inner_text()
                if text and text.strip():
                    return text.strip()

            # Fallback to parent container
            response_elem = await self.page.query_selector("#markdown-content-0")
            if response_elem:
                text = await response_elem.inner_text()
                return text.strip() if text else ""

            # Fallback: look for any markdown content
            markdown_elems = await self.page.query_selector_all("[id^='markdown-content']")
            if markdown_elems:
                last_elem = markdown_elems[-1]
                text = await last_elem.inner_text()
                return text.strip() if text else ""

            return ""

        except Exception as e:
            self.logger.warning(f"  Response extraction error: {e}")
            return ""
