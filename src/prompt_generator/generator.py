"""LLM-powered prompt generator."""

from typing import Any, Optional
import json
import re
from ..config import Platform


class PromptGenerator:
    """Generate diverse prompts for brand visibility analysis using LLM."""

    SYSTEM_PROMPT = """You are an expert at generating search queries that people use when researching products and services.

Your task is to generate diverse, realistic prompts that users might ask AI assistants when researching a specific category of products/services.

Generate prompts that cover different angles:
1. Recommendation queries ("What's the best...")
2. Comparison queries ("Compare X vs Y...")
3. Feature queries ("Which has the best...")
4. Pricing queries ("Most affordable...")
5. Use case queries ("Best for small teams...")
6. Alternative queries ("Alternatives to...")
7. Review queries ("What do users say about...")

IMPORTANT:
- Generate exactly the number of prompts requested
- Make prompts specific to the category provided
- Vary the phrasing and angles
- Return ONLY a JSON array of strings, no other text

Example output for "CRM software" category:
["What is the best CRM software for startups?", "Compare the top CRM tools for sales teams", "Which CRM has the best email integration?"]"""

    def __init__(self, api_key: str, provider: Platform, logger: Any):
        """
        Initialize prompt generator.

        Args:
            api_key: API key for the LLM provider
            provider: Which platform to use for generation
            logger: Logger instance
        """
        self.api_key = api_key
        self.provider = provider
        self.logger = logger

    async def generate(self, category: str, count: int) -> list[str]:
        """
        Generate prompts for the given category.

        Args:
            category: Industry/niche to generate prompts for
            count: Number of prompts to generate

        Returns:
            List of generated prompts
        """
        self.logger.info(f"  Generating {count} prompts for '{category}'...")

        user_prompt = f"""Generate exactly {count} diverse search prompts for the category: "{category}"

These prompts should represent realistic questions users ask AI assistants when researching products in this category.

Return ONLY a JSON array of {count} strings. Example format:
["prompt 1", "prompt 2", "prompt 3"]"""

        try:
            if self.provider == Platform.GEMINI:
                prompts = await self._generate_with_gemini(user_prompt)
            elif self.provider == Platform.CHATGPT:
                prompts = await self._generate_with_openai(user_prompt)
            elif self.provider == Platform.CLAUDE:
                prompts = await self._generate_with_anthropic(user_prompt)
            elif self.provider == Platform.PERPLEXITY:
                prompts = await self._generate_with_perplexity(user_prompt)
            else:
                prompts = self._generate_fallback(category, count)

            # Ensure we have exactly the requested count
            if len(prompts) < count:
                # Add fallback prompts if LLM didn't generate enough
                fallback = self._generate_fallback(category, count - len(prompts))
                prompts.extend(fallback)
            elif len(prompts) > count:
                prompts = prompts[:count]

            self.logger.info(f"  Generated {len(prompts)} prompts")
            return prompts

        except Exception as e:
            self.logger.warning(f"  LLM prompt generation failed: {e}")
            self.logger.info("  Using fallback prompt templates...")
            return self._generate_fallback(category, count)

    async def _generate_with_gemini(self, prompt: str) -> list[str]:
        """Generate prompts using Gemini."""
        import google.generativeai as genai
        import asyncio

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                f"{self.SYSTEM_PROMPT}\n\n{prompt}",
                generation_config={"temperature": 0.8}
            )
        )

        return self._parse_json_response(response.text)

    async def _generate_with_openai(self, prompt: str) -> list[str]:
        """Generate prompts using OpenAI."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
        )

        content = response.choices[0].message.content or "[]"
        return self._parse_json_response(content)

    async def _generate_with_anthropic(self, prompt: str) -> list[str]:
        """Generate prompts using Claude."""
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=self.SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return self._parse_json_response(content)

    async def _generate_with_perplexity(self, prompt: str) -> list[str]:
        """Generate prompts using Perplexity."""
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-sonar-large-128k-online",
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.8,
                },
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "[]")
                return self._parse_json_response(content)

        return []

    def _parse_json_response(self, response: str) -> list[str]:
        """Parse JSON array from LLM response."""
        try:
            # Try direct JSON parse
            prompts = json.loads(response)
            if isinstance(prompts, list):
                return [str(p) for p in prompts if p]
        except json.JSONDecodeError:
            pass

        # Try to extract JSON array from response
        try:
            match = re.search(r'\[.*?\]', response, re.DOTALL)
            if match:
                prompts = json.loads(match.group())
                if isinstance(prompts, list):
                    return [str(p) for p in prompts if p]
        except (json.JSONDecodeError, AttributeError):
            pass

        return []

    def _generate_fallback(self, category: str, count: int) -> list[str]:
        """Generate fallback prompts without LLM."""
        templates = [
            f"What are the best {category} available today?",
            f"Which {category} offers the most features for the price?",
            f"Compare the top rated {category} options",
            f"What is the most affordable {category}?",
            f"Best {category} for small businesses",
            f"Best {category} for startups",
            f"Best {category} for enterprise companies",
            f"Which {category} has the best customer support?",
            f"What are alternatives to popular {category}?",
            f"What do users say about {category} in 2025?",
            f"Which {category} is easiest to use?",
            f"Best {category} with free trial",
            f"Top rated {category} according to reviews",
            f"Which {category} integrates with other tools?",
            f"Most recommended {category} by experts",
        ]

        # Return requested number of templates
        result = []
        for i in range(count):
            result.append(templates[i % len(templates)])
        return result
