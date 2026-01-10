"""Google Gemini browser-based client (no API key needed)."""

import asyncio
from typing import Any, Optional
from .base import BaseBrowserClient, BrowserQueryResult, BrowserClientError


class GeminiBrowserClient(BaseBrowserClient):
    """Browser-based client for Google Gemini (gemini.google.com) - no login required."""

    # CSS Selectors
    SELECTORS = {
        # Input field - Quill editor inside rich-textarea
        "textbox": "rich-textarea .ql-editor",
        "textbox_p": "rich-textarea .ql-editor p",
        
        # Response container
        "response": "model-response",
        "response_container": ".presented-response-container",
        "response_content": "model-response .markdown-main-panel",
    }

    def __init__(self, logger: Any, proxy_config: Optional[dict] = None):
        super().__init__(logger, proxy_config)
        self._message_count = 0

    @property
    def platform_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return "gemini-2.0-flash (free)"

    @property
    def base_url(self) -> str:
        return "https://gemini.google.com"

    async def _platform_init(self):
        """Handle Gemini-specific initialization."""
        
        # Wait for page to stabilize
        await asyncio.sleep(3)
        
        # Handle cookie consent if present
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
        
        # Handle "Try Gemini" or similar buttons
        try:
            try_btn = await self.page.query_selector("button:has-text('Try Gemini')")
            if try_btn:
                await try_btn.click()
                self.logger.info("  Clicked 'Try Gemini'")
                await asyncio.sleep(2)
        except Exception:
            pass
        
        # Wait for the input field to be ready
        try:
            await self.page.wait_for_selector(self.SELECTORS["textbox"], timeout=15000)
            self.logger.info("  Gemini ready")
        except Exception as e:
            raise BrowserClientError(
                message=f"Gemini page did not load properly: {e}",
                platform=self.platform_name,
                recoverable=False
            )

    async def _wait_for_response_complete(self, timeout_seconds: int = 120) -> bool:
        """
        Wait for Gemini to finish generating response using polling.
        """
        last_content = ""
        stable_count = 0
        required_stable = 3
        check_interval = 1.5
        max_checks = int(timeout_seconds / check_interval)
        
        for _ in range(max_checks):
            await asyncio.sleep(check_interval)
            
            current_content = await self._get_response_text()
            
            if current_content == last_content and len(current_content) > 0:
                stable_count += 1
                if stable_count >= required_stable:
                    return True
            else:
                stable_count = 0
                last_content = current_content
        
        return len(last_content) > 0

    async def _get_response_text(self) -> str:
        """Get the text from Gemini's response."""
        try:
            # Try to get all model-response elements
            responses = await self.page.query_selector_all("model-response")
            
            if responses:
                # Get the last response (most recent)
                last_response = responses[-1]
                text = await last_response.inner_text()
                if text and text.strip():
                    return text.strip()
            
            # Fallback: Try structured-content-container
            content = await self.page.query_selector("structured-content-container")
            if content:
                text = await content.inner_text()
                return text.strip() if text else ""
            
            # Fallback: Try presented-response-container
            container = await self.page.query_selector(".presented-response-container")
            if container:
                text = await container.inner_text()
                return text.strip() if text else ""
            
            return ""
            
        except Exception as e:
            self.logger.warning(f"  Response extraction error: {e}")
            return ""

    async def query(self, prompt: str) -> BrowserQueryResult:
        """Send a prompt to Gemini and get the response."""
        try:
            self._message_count += 1
            self.logger.info(f"  Gemini query #{self._message_count}: {prompt[:50]}...")
            
            # For subsequent queries, start fresh
            if self._message_count > 1:
                await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
            
            # Wait for textbox
            await self.page.wait_for_selector(self.SELECTORS["textbox"], timeout=10000)
            
            # Click on textbox
            textbox = await self.page.query_selector(self.SELECTORS["textbox"])
            if not textbox:
                raise BrowserClientError(
                    message="Could not find Gemini textbox",
                    platform=self.platform_name,
                    recoverable=True
                )
            
            await textbox.click()
            await asyncio.sleep(0.5)
            
            # Type prompt with human-like delays
            await self._human_type(self.page, prompt, min_delay=30, max_delay=80)
            
            # Small pause before sending
            await asyncio.sleep(0.5)
            
            # Press Enter to send
            await self.page.keyboard.press("Enter")
            
            # Wait for response to complete
            self.logger.info("  Waiting for response...")
            response_complete = await self._wait_for_response_complete(timeout_seconds=90)
            
            if not response_complete:
                self.logger.warning("  Response may be incomplete (timeout)")
            
            # Extract the response
            response_text = await self._get_response_text()
            
            if not response_text:
                return BrowserQueryResult(
                    platform=self.platform_name,
                    model=self.model_name,
                    prompt=prompt,
                    response="",
                    success=False,
                    error="No response received from Gemini"
                )
            
            self.logger.info(f"  Got response: {len(response_text)} chars")
            
            # Add delay between queries
            await asyncio.sleep(2)
            
            return BrowserQueryResult(
                platform=self.platform_name,
                model=self.model_name,
                prompt=prompt,
                response=response_text,
                success=True
            )
            
        except BrowserClientError:
            raise
        except Exception as e:
            return BrowserQueryResult(
                platform=self.platform_name,
                model=self.model_name,
                prompt=prompt,
                response="",
                success=False,
                error=str(e)
            )
