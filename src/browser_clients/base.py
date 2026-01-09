"""Base class for browser-based AI platform clients."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any
import asyncio
import random


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
    model: str
    prompt: str
    response: str
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "model": self.model,
            "prompt": self.prompt,
            "response": self.response,
            "success": self.success,
            "error": self.error,
        }


class BaseBrowserClient(ABC):
    """Abstract base class for browser-based AI platform clients."""

    def __init__(self, logger: Any, proxy_config: Optional[dict] = None):
        """
        Initialize browser client.
        
        Args:
            logger: Logger instance
            proxy_config: Apify proxy configuration dict
        """
        self.logger = logger
        self.proxy_config = proxy_config
        self.page = None
        self.browser = None
        self.context = None

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the platform."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model being used (best guess for free tier)."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL of the platform."""
        pass

    async def _get_proxy_url(self) -> Optional[str]:
        """Get proxy URL from Apify proxy configuration."""
        if not self.proxy_config:
            return None
        
        try:
            from apify import Actor
            proxy_configuration = await Actor.create_proxy_configuration(
                actor_proxy_input=self.proxy_config
            )
            if proxy_configuration:
                return await proxy_configuration.new_url()
        except Exception as e:
            self.logger.warning(f"  Failed to get proxy URL: {e}")
        
        return None

    async def _human_delay(self, min_ms: int = 50, max_ms: int = 150):
        """Add human-like delay."""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)

    async def _human_type(self, page, text: str, min_delay: int = 30, max_delay: int = 100):
        """Type text with human-like delays between keystrokes using keyboard."""
        for char in text:
            await page.keyboard.type(char, delay=random.randint(min_delay, max_delay))

    async def initialize(self, headless: bool = True):
        """Initialize browser and navigate to platform."""
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        
        # Get proxy if configured
        proxy_url = await self._get_proxy_url()
        
        browser_args = {
            "headless": headless,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        }
        
        self.browser = await self.playwright.chromium.launch(**browser_args)
        
        context_args = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        
        if proxy_url:
            # Parse proxy URL for Playwright format
            context_args["proxy"] = {"server": proxy_url}
            self.logger.info(f"  Using Apify proxy for {self.platform_name}")
        
        self.context = await self.browser.new_context(**context_args)
        self.page = await self.context.new_page()
        
        # Navigate to platform
        self.logger.info(f"  Navigating to {self.base_url}...")
        await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait a bit for dynamic content
        await asyncio.sleep(3)
        
        # Platform-specific initialization (handle cookie banners, etc.)
        await self._platform_init()

    @abstractmethod
    async def _platform_init(self):
        """Platform-specific initialization after page load."""
        pass

    @abstractmethod
    async def query(self, prompt: str) -> BrowserQueryResult:
        """
        Send a prompt to the AI platform and get a response.

        Args:
            prompt: The prompt to send

        Returns:
            BrowserQueryResult with the response
        """
        pass

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
                self.logger.warning(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                await asyncio.sleep(wait_time)

        return BrowserQueryResult(
            platform=self.platform_name,
            model=self.model_name,
            prompt=prompt,
            response="",
            success=False,
            error=last_error or "Unknown error after retries",
        )

    async def close(self):
        """Close browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
