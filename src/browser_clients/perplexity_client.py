"""Perplexity browser-based client (no API key needed)."""

import asyncio
from typing import Any, Optional
from .base import BaseBrowserClient, BrowserQueryResult, BrowserClientError


class PerplexityBrowserClient(BaseBrowserClient):
    """Browser-based client for Perplexity AI (perplexity.ai) - no login required."""

    # CSS Selectors (verified working)
    SELECTORS = {
        "textbox": "#ask-input",
        "textbox_p": "#ask-input > p",
        "response": "#markdown-content-0",
        "response_content": "#markdown-content-0 > div > div > div",
    }

    def __init__(self, logger: Any, proxy_config: Optional[dict] = None):
        super().__init__(logger, proxy_config)
        self._message_count = 0

    @property
    def platform_name(self) -> str:
        return "perplexity"

    @property
    def model_name(self) -> str:
        return "perplexity-default (free)"

    @property
    def base_url(self) -> str:
        return "https://www.perplexity.ai"

    async def _platform_init(self):
        """Handle Perplexity-specific initialization."""
        
        # Wait for page to stabilize
        await asyncio.sleep(3)
        
        # Handle any cookie/popup banners (if present)
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
            await self.page.wait_for_selector(self.SELECTORS["textbox"], timeout=15000)
            self.logger.info("  Perplexity ready")
        except Exception as e:
            raise BrowserClientError(
                message=f"Perplexity page did not load properly: {e}",
                platform=self.platform_name,
                recoverable=False
            )

    async def _wait_for_response_complete(self, timeout_seconds: int = 120) -> bool:
        """
        Wait for Perplexity to finish generating response using polling.
        """
        last_content = ""
        stable_count = 0
        required_stable = 3  # Need 3 consecutive checks with no change
        check_interval = 1.5  # seconds between checks
        max_checks = int(timeout_seconds / check_interval)
        
        for _ in range(max_checks):
            await asyncio.sleep(check_interval)
            
            # Get current response content
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
        """Get the text from Perplexity's response."""
        try:
            # Try the specific response content selector first
            response_elem = await self.page.query_selector(self.SELECTORS["response_content"])
            if response_elem:
                text = await response_elem.inner_text()
                if text and text.strip():
                    return text.strip()
            
            # Fallback to parent container
            response_elem = await self.page.query_selector(self.SELECTORS["response"])
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

    async def query(self, prompt: str) -> BrowserQueryResult:
        """Send a prompt to Perplexity and get the response."""
        try:
            self._message_count += 1
            self.logger.info(f"  Perplexity query #{self._message_count}: {prompt[:50]}...")
            
            # For subsequent queries, start fresh by going to home
            if self._message_count > 1:
                await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
            
            # Wait for textbox
            await self.page.wait_for_selector(self.SELECTORS["textbox"], timeout=10000)
            
            # Click on textbox
            textbox = await self.page.query_selector(self.SELECTORS["textbox"])
            if not textbox:
                raise BrowserClientError(
                    message="Could not find Perplexity textbox",
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
                    error="No response received from Perplexity"
                )
            
            self.logger.info(f"  Got response: {len(response_text)} chars")
            
            # Add delay between queries to be human-like
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
