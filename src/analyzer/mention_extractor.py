"""Extract brand mentions and citations from AI responses using LLM."""

from typing import Any
import json
import re
from dataclasses import dataclass
from ..config import Platform, BrandMention


@dataclass
class ExtractionResult:
    """Result of LLM extraction containing mentions and citations."""
    mentions: list[BrandMention]
    citations: list[str]


class MentionExtractor:
    """Extract brand mentions and citations from AI responses using LLM."""

    SYSTEM_PROMPT = """You are an expert at analyzing text for brand mentions and citations.

Your task is to analyze the given text and:
1. Identify mentions of specific brands
2. Extract any URLs/citations mentioned

For each brand mentioned, provide:
- brand: The exact brand name (as provided in the list)
- count: How many times it's mentioned (count all variations like "Nike", "Nike's", "by Nike")
- rank: The position (1 = first mentioned, 2 = second, etc.)
- context: A relevant context sentence showing how the brand is described
- isRecommended: Whether the brand is explicitly recommended (true/false)

Return a JSON object with two fields:
1. "mentions": Array of brand mention objects
2. "citations": Array of URL strings found in the text

Example output:
{
  "mentions": [
    {"brand": "Nike", "count": 3, "rank": 1, "context": "Nike leads the market with innovative designs", "isRecommended": true},
    {"brand": "Adidas", "count": 2, "rank": 2, "context": "Adidas offers competitive alternatives", "isRecommended": false}
  ],
  "citations": [
    "https://example.com/article",
    "https://review-site.com/comparison"
  ]
}

If no brands are mentioned, return an empty mentions array.
If no URLs are found, return an empty citations array."""

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

    async def extract(self, response_text: str, brands: list[str]) -> ExtractionResult:
        """
        Extract brand mentions and citations from response text using LLM.

        Args:
            response_text: The AI response to analyze
            brands: List of brands to look for

        Returns:
            ExtractionResult containing mentions and citations
        """
        if not response_text or not brands:
            return ExtractionResult(mentions=[], citations=[])

        try:
            result = await self._extract_with_llm(response_text, brands)
            return result
        except Exception as e:
            self.logger.warning(f"  LLM extraction failed: {e}")
            return ExtractionResult(mentions=[], citations=[])

    async def _extract_with_llm(self, response_text: str, brands: list[str]) -> ExtractionResult:
        """Extract mentions and citations using LLM."""
        brands_list = ", ".join(brands)
        user_prompt = f"""Analyze this text for mentions of these brands: {brands_list}

Also extract any URLs/citations found in the text.

Text to analyze:
\"\"\"
{response_text[:3000]}
\"\"\"

Return a JSON object with "mentions" array and "citations" array."""

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
            model="gpt-4o-mini",
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

    def _parse_response(self, content: str, valid_brands: list[str]) -> ExtractionResult:
        """Parse LLM response into ExtractionResult."""
        mentions = []
        citations = []

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()
            
            data = json.loads(content)
            
            # Parse mentions
            mentions_data = data.get("mentions", [])
            if not isinstance(mentions_data, list):
                mentions_data = []
                
            for item in mentions_data:
                if isinstance(item, dict):
                    brand = item.get("brand", "")
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
            
            # Parse citations
            citations_data = data.get("citations", [])
            if isinstance(citations_data, list):
                citations = [str(url) for url in citations_data if url and isinstance(url, str)]

        except json.JSONDecodeError:
            pass

        return ExtractionResult(mentions=mentions, citations=citations)
