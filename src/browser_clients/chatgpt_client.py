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

    @property
    def textbox_selectors(self) -> tuple[str, ...]:
        return (
            "#prompt-textarea[contenteditable='true']",
            "div#prompt-textarea[role='textbox']",
            "textarea[name='prompt-textarea']",
            "#prompt-textarea",
        )

    async def _platform_init(self):
        """Handle ChatGPT-specific initialization."""
        await asyncio.sleep(3)

        try:
            cloudflare = await self.page.query_selector("text='Verify you are human'")
            if cloudflare:
                checkbox = await self.page.query_selector("input[type='checkbox']")
                if checkbox:
                    await checkbox.click()
                    await asyncio.sleep(5)
        except Exception:
            pass

        try:
            cookie_btn = await self.page.query_selector("button:has-text('Accept all')")
            if cookie_btn:
                await cookie_btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        await self._dismiss_login_popup()

        try:
            await self._find_visible_textbox(timeout_ms=30000)
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
                await asyncio.sleep(1)
        except Exception:
            pass

    async def _handle_popups_after_refresh(self):
        """Handle popups that appear after page refresh."""
        await self._dismiss_login_popup()

    async def _get_message_count(self) -> int:
        """Count assistant messages in the conversation."""
        try:
            messages = await self.page.query_selector_all("[data-message-author-role='assistant']")
            return len(messages)
        except Exception:
            return 0

    async def _get_response_text(self) -> str:
        try:
            messages = await self.page.query_selector_all("[data-message-author-role='assistant']")

            if not messages:
                return ""

            last_message = messages[-1]
            
            content_div = await last_message.query_selector(".markdown, [class*='markdown']")
            if content_div:
                text = await content_div.inner_text()
                if text and len(text.strip()) > 5:
                    return text.strip()

            text = await last_message.inner_text()
            if text and len(text.strip()) > 5:
                return text.strip()

            return ""

        except Exception:
            return ""
