"""ChatGPT browser-based client (no API key needed)."""

import asyncio
from typing import Any, Optional
from .base import BaseBrowserClient, BrowserQueryResult, BrowserClientError


class ChatGPTBrowserClient(BaseBrowserClient):
    """Browser-based client for ChatGPT (chatgpt.com) - no login required."""

    # CSS Selectors
    SELECTORS = {
        # Input textbox - the contenteditable paragraph inside prompt-textarea
        "textbox": "#prompt-textarea",
        "textbox_p": "#prompt-textarea > p",
        
        # Response container - assistant messages
        "response_article": "article[data-message-author-role='assistant']",
        "response_content": "article[data-message-author-role='assistant'] .markdown",
        
        # Buttons
        "send_button": "[data-testid='send-button']",
        "stop_button": "[data-testid='stop-button']",
        
        # Cookie/popup dismissal
        "cookie_accept": "button:has-text('Accept all')",
        "maybe_later": "button:has-text('Stay logged out'), button:has-text('Maybe later')",
        
        # Cloudflare captcha
        "cloudflare_checkbox": "input[type='checkbox']",
        
        # Loading indicator
        "loading": ".result-streaming",
    }

    def __init__(self, logger: Any, proxy_config: Optional[dict] = None):
        super().__init__(logger, proxy_config)
        self._message_count = 0

    @property
    def platform_name(self) -> str:
        return "chatgpt"

    @property
    def model_name(self) -> str:
        # Free tier typically uses GPT-4o or GPT-4o-mini
        return "gpt-4o-mini (free)"

    @property
    def base_url(self) -> str:
        return "https://chatgpt.com"

    async def _platform_init(self):
        """Handle ChatGPT-specific initialization."""
        
        # Wait for page to stabilize
        await asyncio.sleep(3)
        
        # Handle Cloudflare challenge if present
        try:
            cloudflare = await self.page.query_selector("text='Verify you are human'")
            if cloudflare:
                self.logger.info("  Handling Cloudflare verification...")
                checkbox = await self.page.query_selector(self.SELECTORS["cloudflare_checkbox"])
                if checkbox:
                    await checkbox.click()
                    await asyncio.sleep(5)
        except Exception:
            pass
        
        # Handle cookie consent
        try:
            cookie_btn = await self.page.query_selector(self.SELECTORS["cookie_accept"])
            if cookie_btn:
                await cookie_btn.click()
                self.logger.info("  Accepted cookies")
                await asyncio.sleep(1)
        except Exception:
            pass
        
        # Handle "Stay logged out" or "Maybe later" popup
        try:
            maybe_btn = await self.page.query_selector(self.SELECTORS["maybe_later"])
            if maybe_btn:
                await maybe_btn.click()
                self.logger.info("  Dismissed login prompt")
                await asyncio.sleep(1)
        except Exception:
            pass
        
        # Wait for textbox to be ready
        try:
            await self.page.wait_for_selector(self.SELECTORS["textbox"], timeout=15000)
            self.logger.info("  ChatGPT ready")
        except Exception as e:
            raise BrowserClientError(
                message=f"ChatGPT page did not load properly: {e}",
                platform=self.platform_name,
                recoverable=False
            )

    async def _wait_for_response_complete(self, timeout_seconds: int = 120) -> bool:
        """
        Wait for ChatGPT to finish generating response using polling.
        
        Checks if new content is being added. When content stops changing
        for a few seconds, we consider the response complete.
        """
        last_content = ""
        stable_count = 0
        required_stable = 3  # Need 3 consecutive checks with no change
        check_interval = 1.5  # seconds between checks
        max_checks = int(timeout_seconds / check_interval)
        
        for _ in range(max_checks):
            await asyncio.sleep(check_interval)
            
            # Check if stop button is still visible (means still generating)
            stop_btn = await self.page.query_selector(self.SELECTORS["stop_button"])
            
            # Get current response content
            current_content = await self._get_last_response_text()
            
            if current_content == last_content and len(current_content) > 0:
                stable_count += 1
                if stable_count >= required_stable and not stop_btn:
                    return True
            else:
                stable_count = 0
                last_content = current_content
            
            # Also check for streaming indicator
            streaming = await self.page.query_selector(self.SELECTORS["loading"])
            if not streaming and len(current_content) > 0 and stable_count >= 1:
                return True
        
        return len(last_content) > 0

    async def _get_last_response_text(self) -> str:
        """Get the text from the last assistant response using multiple strategies."""
        try:
            # Strategy 1: Try the data-message-author-role attribute
            articles = await self.page.query_selector_all("article[data-message-author-role='assistant']")
            if articles:
                last_article = articles[-1]
                # Try markdown content first
                markdown = await last_article.query_selector(".markdown")
                if markdown:
                    text = await markdown.inner_text()
                    if text.strip():
                        return text.strip()
                # Fallback to article text
                text = await last_article.inner_text()
                if text.strip():
                    return text.strip()
            
            # Strategy 2: Try to find any article with response content
            articles = await self.page.query_selector_all("article")
            if len(articles) >= 2:  # First is user query, second is response
                last_article = articles[-1]
                text = await last_article.inner_text()
                if text.strip():
                    return text.strip()
            
            # Strategy 3: JavaScript-based extraction (more robust)
            js_result = await self.page.evaluate("""
                () => {
                    // Try to find assistant messages
                    const articles = document.querySelectorAll('article');
                    if (articles.length >= 2) {
                        // Last article should be the response
                        const lastArticle = articles[articles.length - 1];
                        const markdown = lastArticle.querySelector('.markdown, .prose');
                        if (markdown) return markdown.innerText;
                        return lastArticle.innerText;
                    }
                    
                    // Try alternative: look for any div with substantial text after the input
                    const allDivs = document.querySelectorAll('div[class*="text"]');
                    for (const div of allDivs) {
                        if (div.innerText && div.innerText.length > 100) {
                            return div.innerText;
                        }
                    }
                    
                    return '';
                }
            """)
            if js_result and js_result.strip():
                return js_result.strip()
            
            return ""
            
        except Exception as e:
            self.logger.warning(f"  Response extraction error: {e}")
            return ""

    async def _clear_textbox(self):
        """Clear the textbox before typing new prompt."""
        try:
            textbox = await self.page.query_selector(self.SELECTORS["textbox"])
            if textbox:
                await textbox.click()
                # Select all and delete
                await self.page.keyboard.press("Meta+a" if "mac" in str(self.page).lower() else "Control+a")
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(0.3)
        except Exception:
            pass

    async def query(self, prompt: str) -> BrowserQueryResult:
        """Send a prompt to ChatGPT and get the response."""
        try:
            self._message_count += 1
            self.logger.info(f"  ChatGPT query #{self._message_count}: {prompt[:50]}...")
            
            # If this isn't the first message, we need to start a new chat
            # to avoid context from previous queries affecting results
            if self._message_count > 1:
                # Refresh to start new chat
                await self.page.goto(self.base_url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                
                # Handle any popups again
                try:
                    maybe_btn = await self.page.query_selector(self.SELECTORS["maybe_later"])
                    if maybe_btn:
                        await maybe_btn.click()
                        await asyncio.sleep(1)
                except Exception:
                    pass
            
            # Wait for textbox
            await self.page.wait_for_selector(self.SELECTORS["textbox"], timeout=10000)
            
            # Click on textbox
            textbox = await self.page.query_selector(self.SELECTORS["textbox"])
            if not textbox:
                raise BrowserClientError(
                    message="Could not find ChatGPT textbox",
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
            response_text = await self._get_last_response_text()
            
            if not response_text:
                return BrowserQueryResult(
                    platform=self.platform_name,
                    model=self.model_name,
                    prompt=prompt,
                    response="",
                    success=False,
                    error="No response received from ChatGPT"
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
