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

    async def initialize(self, headless: bool = False):
        """Initialize browser and navigate to platform.
        
        Note: headless=False is required because ChatGPT and Perplexity 
        block headless browsers. We use Xvfb for virtual display on servers.
        """
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
        await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)

        await self._platform_init()

    @abstractmethod
    async def _platform_init(self):
        """Platform-specific initialization after page load (handle popups, cookies, etc.)."""
        pass

    @abstractmethod
    async def _get_response_text(self) -> str:
        """Extract the response text from the page. Platform-specific."""
        pass

    async def _handle_popups_after_refresh(self):
        """Handle any popups that appear after page refresh. Override if needed."""
        pass

    async def _wait_for_response_complete(self, timeout_seconds: int = 120) -> bool:
        """Wait for response to complete using polling. Override if platform needs custom logic."""
        check_interval = 1.5
        initial_wait_time = 30
        max_checks = int(initial_wait_time / check_interval)

        current_content = ""
        for _ in range(max_checks):
            await asyncio.sleep(check_interval)
            try:
                current_content = await self._get_response_text()
            except Exception:
                return False

            if current_content:
                break

        if not current_content:
            return False

        last_content = current_content
        stable_count = 0
        required_stable = 3

        while True:
            await asyncio.sleep(check_interval)
            try:
                current_content = await self._get_response_text()
            except Exception:
                return len(last_content) > 0

            if current_content == last_content:
                stable_count += 1
                if stable_count >= required_stable:
                    return True
            else:
                stable_count = 0
                last_content = current_content

    async def query(self, prompt: str) -> BrowserQueryResult:
        """Send a prompt to the AI platform and get a response."""
        try:
            self._message_count += 1

            if self._message_count > 1:
                await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                await self._handle_popups_after_refresh()

            await self.page.wait_for_selector(self.textbox_selector, timeout=10000)
            textbox = await self.page.query_selector(self.textbox_selector)

            if not textbox:
                raise BrowserClientError(
                    message=f"Could not find {self.platform_name} textbox",
                    platform=self.platform_name,
                    recoverable=True
                )

            await textbox.click()
            await asyncio.sleep(0.5)

            await self._human_type(prompt)
            await asyncio.sleep(0.5)

            await self.page.keyboard.press("Enter")

            response_complete = await self._wait_for_response_complete(timeout_seconds=90)

            response_text = await self._get_response_text()

            if not response_text:
                return BrowserQueryResult(
                    platform=self.platform_name,
                    prompt=prompt,
                    response="",
                    success=False,
                    error=f"No response received from {self.platform_name}"
                )
            await asyncio.sleep(2)

            return BrowserQueryResult(
                platform=self.platform_name,
                prompt=prompt,
                response=response_text,
                success=True
            )

        except BrowserClientError:
            raise
        except Exception as e:
            return BrowserQueryResult(
                platform=self.platform_name,
                prompt=prompt[:200] if prompt else "",
                response="",
                success=False,
                error=sanitize_error_message(e)
            )

    async def query_with_retry(self, prompt: str, max_retries: int = 2) -> BrowserQueryResult:
        """Query with retry on failure."""
        last_error = None

        for attempt in range(max_retries):
            try:
                result = await self.query(prompt)
                if result.success:
                    return result
                last_error = result.error
            except BrowserClientError as e:
                last_error = e.message
                if not e.recoverable:
                    break
            except Exception as e:
                last_error = str(e)

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                await asyncio.sleep(wait_time)

        return BrowserQueryResult(
            platform=self.platform_name,
            prompt=prompt,
            response="",
            success=False,
            error=last_error or "Unknown error after retries",
        )

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
