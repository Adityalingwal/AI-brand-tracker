"""Extract brand mentions from AI responses."""

from typing import Any, Optional
import json
import re
from dataclasses import dataclass
from ..config import Platform, BrandMention


class MentionExtractor:
    """Extract brand mentions from AI responses using LLM."""

    SYSTEM_PROMPT = """You are an expert at analyzing text for brand mentions.

Your task is to analyze the given text and identify mentions of specific brands.

For each brand mentioned, provide:
1. The exact brand name (as provided in the list)
2. How many times it's mentioned (count all variations like "Nike", "Nike's", "by Nike")
3. The position/rank (1 = first mentioned, 2 = second, etc.)
4. A relevant context sentence showing how the brand is described
5. Whether the brand is explicitly recommended (true/false)

Return ONLY a JSON array of objects. If a brand is not mentioned, do not include it.

Example output:
[
  {"brand": "Nike", "count": 3, "rank": 1, "context": "Nike leads the market with innovative designs", "isRecommended": true},
  {"brand": "Adidas", "count": 2, "rank": 2, "context": "Adidas offers competitive alternatives", "isRecommended": false}
]"""

    def __init__(self, api_key: str, provider: Platform, logger: Any):
        """
        Initialize mention extractor.

        Args:
            api_key: API key for the LLM provider
            provider: Which platform to use for extraction
            logger: Logger instance
        """
        self.api_key = api_key
        self.provider = provider
        self.logger = logger

    async def extract(self, response_text: str, brands: list[str]) -> list[BrandMention]:
        """
        Extract brand mentions from response text.

        Args:
            response_text: The AI response to analyze
            brands: List of brands to look for

        Returns:
            List of BrandMention objects
        """
        if not response_text or not brands:
            return []

        # First try LLM extraction
        try:
            mentions = await self._extract_with_llm(response_text, brands)
            if mentions:
                return mentions
        except Exception as e:
            self.logger.warning(f"  LLM extraction failed: {e}")

        # Fallback to regex-based extraction
        return self._extract_with_regex(response_text, brands)

    async def _extract_with_llm(self, response_text: str, brands: list[str]) -> list[BrandMention]:
        """Extract mentions using LLM."""
        brands_list = ", ".join(brands)
        user_prompt = f"""Analyze this text for mentions of these brands: {brands_list}

Text to analyze:
\"\"\"
{response_text[:3000]}
\"\"\"

Return ONLY a JSON array of brand mentions found. If a brand is not mentioned, do not include it."""

        content = ""

        if self.provider == Platform.GEMINI:
            content = await self._call_gemini(user_prompt)
        elif self.provider == Platform.CHATGPT:
            content = await self._call_openai(user_prompt)
        elif self.provider == Platform.CLAUDE:
            content = await self._call_anthropic(user_prompt)

        return self._parse_response(content, brands)

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API."""
        import google.generativeai as genai
        import asyncio

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(f"{self.SYSTEM_PROMPT}\n\n{prompt}")
        )
        return response.text or ""

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Use mini for analysis (cheaper)
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
        return content

    def _parse_response(self, content: str, valid_brands: list[str]) -> list[BrandMention]:
        """Parse LLM response into BrandMention objects."""
        mentions = []

        try:
            # Try direct JSON parse
            data = json.loads(content)
            if not isinstance(data, list):
                data = [data]

            for item in data:
                if isinstance(item, dict):
                    brand = item.get("brand", "")
                    # Only include if brand is in our list (case-insensitive match)
                    matched_brand = next(
                        (b for b in valid_brands if b.lower() == brand.lower()),
                        None
                    )
                    if matched_brand:
                        mentions.append(BrandMention(
                            brand=matched_brand,
                            count=item.get("count", 1),
                            rank=item.get("rank", len(mentions) + 1),
                            context=item.get("context", "")[:200],
                            is_recommended=item.get("isRecommended", False),
                        ))

        except json.JSONDecodeError:
            # Try to extract JSON from response
            try:
                match = re.search(r'\[.*?\]', content, re.DOTALL)
                if match:
                    return self._parse_response(match.group(), valid_brands)
            except:
                pass

        return mentions

    def _extract_with_regex(self, response_text: str, brands: list[str]) -> list[BrandMention]:
        """Fallback: Extract mentions using regex."""
        mentions = []
        text_lower = response_text.lower()

        for brand in brands:
            # Count occurrences (case-insensitive)
            pattern = re.compile(re.escape(brand), re.IGNORECASE)
            matches = pattern.findall(response_text)
            count = len(matches)

            if count > 0:
                # Find context (sentence containing the brand)
                context = ""
                sentences = re.split(r'[.!?]', response_text)
                for sentence in sentences:
                    if brand.lower() in sentence.lower():
                        context = sentence.strip()[:200]
                        break

                # Determine rank by first occurrence position
                first_pos = text_lower.find(brand.lower())

                mentions.append(BrandMention(
                    brand=brand,
                    count=count,
                    rank=0,  # Will be calculated later
                    context=context,
                    is_recommended=False,  # Can't determine without LLM
                ))

        # Sort by first occurrence and assign ranks
        mentions.sort(key=lambda m: response_text.lower().find(m.brand.lower()))
        for i, mention in enumerate(mentions):
            mention.rank = i + 1

        return mentions
