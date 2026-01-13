"""Base class for browser-based AI platform clients."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any
import asyncio
import random
import os

from playwright.async_api import async_playwright

try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

from ..utils import sanitize_error_message


class BrowserClientError(Exception):
    """Error from browser-based client."""

    def __init__(self, message: str, platform: str, recoverable: bool = True):
        self.message = message
        self.platform = platform
        self.recoverable = recoverable
        super().__init__(message)


@dataclass
class BrowserQueryResult:
    """Result from querying an AI platform via browser."""
    platform: str
    prompt: str
    response: str
    success: bool
    error: Optional[str] = None


class BaseBrowserClient(ABC):
  
    def __init__(self, logger: Any, proxy_config: Optional[dict] = None):
        """Initialize browser client."""
        self.logger = logger
        self.page = None
        self.browser = None
        self.context = None
        self._message_count = 0

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the platform (e.g., 'chatgpt', 'gemini', 'perplexity')."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL of the platform."""
        pass

    @property
    @abstractmethod
    def textbox_selector(self) -> str:
        """CSS selector for the input textbox."""
        pass

    async def _human_type(self, text: str, min_delay: int = 30, max_delay: int = 80):
        """Type text with human-like delays between keystrokes."""
        for char in text:
            await self.page.keyboard.type(char, delay=random.randint(min_delay, max_delay))

    async def _execute_with_retry(self, operation: callable, error_message: str, max_retries: int = 1):
        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries:
                    self.logger.error(f"[{self.platform_name}] Error: {error_message} - {str(e)}")
                    raise

                await asyncio.sleep(2)

    async def initialize(self, headless: bool = False):
        async def _init_impl():
            self.playwright = await async_playwright().start()
            
            is_apify = os.environ.get("APIFY_IS_AT_HOME") == "1"

            browser_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--single-process",
            ]
            
            if is_apify:
                browser_args.extend([
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-sync",
                    "--no-first-run",
                    "--no-zygote",
                ])
            else:
                browser_args.append("--window-size=1920,1080")

            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=browser_args
            )

            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            self.page = await self.context.new_page()

            if STEALTH_AVAILABLE:
                try:
                    stealth = Stealth()
                    await stealth.apply_stealth_async(self.page)
                except Exception:
                    pass
            await self.page.goto(self.base_url, wait_until="commit", timeout=60000)
            await asyncio.sleep(3)

            await self._platform_init()

        await self._execute_with_retry(
            _init_impl,
            "Browser initialization failed"
        )

    @abstractmethod
    async def _platform_init(self):
        """Platform-specific initialization after page load (handle popups, cookies, etc.)."""
        pass

    @abstractmethod
    async def _get_message_count(self) -> int:
        """Get the number of message bubbles in the conversation. Use for detecting new responses."""
        pass

    @abstractmethod
    async def _get_response_text(self) -> str:
        """Extract the response text from the page. Platform-specific."""
        pass

    async def _handle_popups_after_refresh(self):
        """Handle any popups that appear after page refresh. Override if needed."""
        pass

    async def _wait_for_new_message(self, old_count: int, timeout_seconds: int = 120) -> bool:
        """Wait for the message count to increase."""
        check_interval = 1.0
        max_checks = int(timeout_seconds / check_interval)

        for _ in range(max_checks):
            await asyncio.sleep(check_interval)
            try:
                current_count = await self._get_message_count()
                if current_count > old_count:
                    return True
            except Exception:
                pass
        return False

    async def _wait_for_response_complete(self, timeout_seconds: int = 120, old_content: str = "") -> bool:
        # This is now used only for checking text stability AFTER count has increased
        check_interval = 2.0
        
        last_content = ""
        stable_count = 0
        required_stable = 4  # Increased from 3 to ensure response is truly complete (8 seconds of stability)

        # We assume count has already increased, so we just wait for text to be stable (not streaming)
        for _ in range(int(timeout_seconds / check_interval)):
             await asyncio.sleep(check_interval)
             try:
                 current_content = await self._get_response_text()
             except Exception:
                 continue

             if current_content and current_content == last_content and len(current_content) > 10:
                 stable_count += 1
                 if stable_count >= required_stable:
                     return True
             else:
                 stable_count = 0
                 last_content = current_content
        
        return False


    async def query(self, prompt: str) -> BrowserQueryResult:
        """Send a prompt to the AI platform and get a response."""
        async def _query_impl():
            self._message_count += 1
            await self.page.wait_for_selector(self.textbox_selector, timeout=30000)
            textbox = await self.page.query_selector(self.textbox_selector)

            if not textbox:
                raise BrowserClientError(
                    message=f"Could not find {self.platform_name} textbox",
                    platform=self.platform_name,
                    recoverable=True
                )

            # Capture old state
            old_count = await self._get_message_count()

            await textbox.click()
            await asyncio.sleep(0.5)

            await self._human_type(prompt)
            await asyncio.sleep(0.5)

            await self.page.keyboard.press("Enter")

            # 1. Wait for new message bubble to appear
            new_message_appeared = await self._wait_for_new_message(old_count, timeout_seconds=60)
            
            if not new_message_appeared:
                 return BrowserQueryResult(
                    platform=self.platform_name,
                    prompt=prompt,
                    response="",
                    success=False,
                    error=f"No new response received from {self.platform_name} (count did not increase)"
                )

            # 2. Wait for text to finish streaming/stabilize
            await self._wait_for_response_complete(timeout_seconds=90)

            response_text = await self._get_response_text()

            if not response_text:
                return BrowserQueryResult(
                    platform=self.platform_name,
                    prompt=prompt,
                    response="",
                    success=False,
                    error=f"Empty response received from {self.platform_name}"
                )
            await asyncio.sleep(5)  # Increased from 2s - give platform time to fully settle before next query

            return BrowserQueryResult(
                platform=self.platform_name,
                prompt=prompt,
                response=response_text,
                success=True
            )

        try:
            return await self._execute_with_retry(
                _query_impl,
                f"Query failed for prompts: {prompt[:50]}...",
                max_retries=1
            )
        except Exception as e:
            return BrowserQueryResult(
                platform=self.platform_name,
                prompt=prompt[:200] if prompt else "",
                response="",
                success=False,
                error=sanitize_error_message(e)
            )

    async def query_with_retry(self, prompt: str, max_retries: int = 1) -> BrowserQueryResult:
        """Wrapper for query (now handled internally by _execute_with_retry)."""
        return await self.query(prompt)

    async def close(self):
        """Close browser and cleanup."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            raise
