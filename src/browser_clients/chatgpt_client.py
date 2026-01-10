"""ChatGPT browser-based client (no API key needed)."""

import asyncio
from typing import Any, Optional
from .base import BaseBrowserClient, BrowserClientError


class ChatGPTBrowserClient(BaseBrowserClient):
    """Browser-based client for ChatGPT (chatgpt.com) - no login required."""

    @property
    def platform_name(self) -> str:
        return "chatgpt"

    @property
    def base_url(self) -> str:
        return "https://chatgpt.com"

    @property
    def textbox_selector(self) -> str:
        return "#prompt-textarea"

    async def _platform_init(self):
        """Handle ChatGPT-specific initialization."""
        await asyncio.sleep(3)

        # Handle Cloudflare challenge if present
        try:
            cloudflare = await self.page.query_selector("text='Verify you are human'")
            if cloudflare:
                self.logger.info("  Handling Cloudflare verification...")
                checkbox = await self.page.query_selector("input[type='checkbox']")
                if checkbox:
                    await checkbox.click()
                    await asyncio.sleep(5)
        except Exception:
            pass

        # Handle cookie consent
        try:
            cookie_btn = await self.page.query_selector("button:has-text('Accept all')")
            if cookie_btn:
                await cookie_btn.click()
                self.logger.info("  Accepted cookies")
                await asyncio.sleep(1)
        except Exception:
            pass

        # Handle "Stay logged out" or "Maybe later" popup
        await self._dismiss_login_popup()

        # Wait for textbox to be ready
        try:
            await self.page.wait_for_selector(self.textbox_selector, timeout=15000)
            self.logger.info("  ChatGPT ready")
        except Exception as e:
            raise BrowserClientError(
                message=f"ChatGPT page did not load properly: {e}",
                platform=self.platform_name,
                recoverable=False
            )

    async def _dismiss_login_popup(self):
        """Dismiss the login prompt popup."""
        try:
            maybe_btn = await self.page.query_selector(
                "button:has-text('Stay logged out'), button:has-text('Maybe later')"
            )
            if maybe_btn:
                await maybe_btn.click()
                self.logger.info("  Dismissed login prompt")
                await asyncio.sleep(1)
        except Exception:
            pass

    async def _handle_popups_after_refresh(self):
        """Handle popups that appear after page refresh."""
        await self._dismiss_login_popup()

    async def _get_response_text(self) -> str:
        """Get the text from the last assistant response."""
        try:
            # Get all article elements - first is user query, last is response
            articles = await self.page.query_selector_all("article")

            if len(articles) < 2:
                return ""

            # Last article is the response
            last_article = articles[-1]
            text = await last_article.inner_text()

            return text.strip() if text else ""

        except Exception as e:
            self.logger.warning(f"  Response extraction error: {e}")
            return ""
