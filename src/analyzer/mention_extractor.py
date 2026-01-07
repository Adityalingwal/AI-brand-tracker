"""Extract brand mentions and citations from AI responses using LLM."""

from typing import Any
import json
import re
from dataclasses import dataclass
from ..config import Platform, BrandMention


@dataclass
class ExtractionResult:
    """Result of LLM extraction containing mentions and citations."""
    prompt_id: str
    mentions: list[BrandMention]
    citations: list[str]


class MentionExtractor:
    """Extract brand mentions and citations from AI responses using LLM."""

    BATCH_SYSTEM_PROMPT = """You are an expert at analyzing text for brand mentions and citations.

You will receive multiple AI responses, each with a prompt_id. Analyze EACH response separately.

For each response, extract:
1. Brand mentions (from the provided brand list)
2. URLs/citations found in the text

For each brand mentioned, provide:
- brand: The exact brand name (as provided in the list)
- count: How many times it's mentioned
- rank: The position (1 = first mentioned, 2 = second, etc.)
- context: A relevant context sentence
- isRecommended: Whether explicitly recommended (true/false)

Return a JSON object with "analyses" array containing analysis for EACH response:

{
  "analyses": [
    {
      "promptId": "prompt_001",
      "mentions": [
        {"brand": "Salesforce", "count": 3, "rank": 1, "context": "Salesforce leads...", "isRecommended": true}
      ],
      "citations": ["https://example.com"]
    },
    {
      "promptId": "prompt_002",
      "mentions": [...],
      "citations": [...]
    }
  ]
}

IMPORTANT: Return analysis for EACH response separately. Do not skip any response."""

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

    async def extract_batch(self, responses: list[dict], brands: list[str]) -> list[ExtractionResult]:
        """
        Extract brand mentions and citations from multiple responses in a single LLM call.

        Args:
            responses: List of response dicts with 'prompt_id', 'prompt_text', 'response'
            brands: List of brands to look for

        Returns:
            List of ExtractionResult for each response
        """
        if not responses or not brands:
            return []

        try:
            results = await self._extract_batch_with_llm(responses, brands)
            return results
        except Exception as e:
            self.logger.warning(f"  Batch LLM extraction failed: {e}")
            return [ExtractionResult(prompt_id=r["prompt_id"], mentions=[], citations=[]) for r in responses]

    async def _extract_batch_with_llm(self, responses: list[dict], brands: list[str]) -> list[ExtractionResult]:
        """Extract mentions and citations from multiple responses using single LLM call."""
        brands_list = ", ".join(brands)
        
        # Build the prompt with all responses
        responses_text = ""
        for i, resp in enumerate(responses):
            prompt_text = resp.get("prompt_text", "")[:100]
            response_text = resp.get("response", "")[:2500]  # Limit each response
            responses_text += f"""
=== RESPONSE {i+1} ===
Prompt ID: {resp["prompt_id"]}
Prompt: "{prompt_text}"
Response:
\"\"\"
{response_text}
\"\"\"

"""

        user_prompt = f"""Analyze these {len(responses)} responses for mentions of these brands: {brands_list}

Also extract any URLs/citations found in each response.

{responses_text}

Return a JSON object with "analyses" array containing analysis for EACH response.
Each analysis must have: promptId, mentions array, citations array."""

        content = ""

        if self.provider == Platform.GEMINI:
            content = await self._call_gemini(user_prompt)
        elif self.provider == Platform.CHATGPT:
            content = await self._call_openai(user_prompt)
        elif self.provider == Platform.CLAUDE:
            content = await self._call_anthropic(user_prompt)

        return self._parse_batch_response(content, brands, responses)

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API."""
        import google.generativeai as genai
        import asyncio

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(f"{self.BATCH_SYSTEM_PROMPT}\n\n{prompt}")
        )
        return response.text or ""

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.BATCH_SYSTEM_PROMPT},
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
            max_tokens=4096,
            system=self.BATCH_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
        return content

    def _parse_batch_response(self, content: str, valid_brands: list[str], original_responses: list[dict]) -> list[ExtractionResult]:
        """Parse batch LLM response into list of ExtractionResult."""
        results = []
        
        # Create a map of prompt_id to original response for fallback
        response_map = {r["prompt_id"]: r for r in original_responses}

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()
            
            data = json.loads(content)
            analyses = data.get("analyses", [])
            
            # Track which prompt_ids we've processed
            processed_ids = set()
            
            for analysis in analyses:
                if not isinstance(analysis, dict):
                    continue
                    
                prompt_id = analysis.get("promptId", "")
                processed_ids.add(prompt_id)
                
                # Parse mentions
                mentions = []
                mentions_data = analysis.get("mentions", [])
                if isinstance(mentions_data, list):
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
                citations = []
                citations_data = analysis.get("citations", [])
                if isinstance(citations_data, list):
                    citations = [str(url) for url in citations_data if url and isinstance(url, str)]
                
                results.append(ExtractionResult(
                    prompt_id=prompt_id,
                    mentions=mentions,
                    citations=citations
                ))
            
            # Add empty results for any responses that weren't in LLM output
            for resp in original_responses:
                if resp["prompt_id"] not in processed_ids:
                    results.append(ExtractionResult(
                        prompt_id=resp["prompt_id"],
                        mentions=[],
                        citations=[]
                    ))

        except json.JSONDecodeError:
            # Return empty results for all responses
            for resp in original_responses:
                results.append(ExtractionResult(
                    prompt_id=resp["prompt_id"],
                    mentions=[],
                    citations=[]
                ))

        return results
