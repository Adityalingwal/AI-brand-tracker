"""Consolidated analyzer that generates complete output structure in one LLM call."""

import json
from typing import Optional
from ..config import AnalysisProvider


class ConsolidatedAnalyzer:
    """Analyzes all platform responses and generates complete output structure."""

    def __init__(self, api_key: str, provider: AnalysisProvider, logger):
        """
        Initialize the consolidated analyzer.

        Args:
            api_key: API key for LLM provider
            provider: LLM provider (openai, anthropic, google)
            logger: Logger instance
        """
        self.api_key = api_key
        self.provider = provider
        self.logger = logger
        self.client = None

        # Initialize provider client
        if provider == AnalysisProvider.OPENAI:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = "gpt-4o-mini"
        elif provider == AnalysisProvider.ANTHROPIC:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=api_key)
            self.model = "claude-3-5-sonnet-20241022"
        elif provider == AnalysisProvider.GOOGLE:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = "gemini-2.0-flash-exp"

    def _build_analysis_prompt(
        self,
        my_brand: str,
        competitors: list[str],
        platform_responses: list[dict]
    ) -> str:
        """
        Build the comprehensive analysis prompt.

        Args:
            my_brand: User's brand name
            competitors: List of competitor brand names
            platform_responses: List of dicts with platform, prompt_text, response

        Returns:
            Formatted prompt string
        """
        # Group responses by platform
        platform_data = {}
        for resp in platform_responses:
            platform = resp["platform"]
            if platform not in platform_data:
                platform_data[platform] = []
            platform_data[platform].append({
                "question": resp["prompt_text"],
                "answer": resp["response"]
            })

        prompt = f"""You are analyzing AI platform responses to track brand mentions and visibility.

INPUT DATA:
- My Brand: "{my_brand}"
- Competitors: {json.dumps(competitors)}
- Total Platforms: {len(platform_data)}
- Total Prompts per Platform: {len(platform_responses) // len(platform_data) if platform_data else 0}

PLATFORM RESPONSES:
"""

        for platform, prompts in platform_data.items():
            prompt += f"\n=== Platform: {platform} ===\n"
            for i, p in enumerate(prompts, 1):
                prompt += f"\nPrompt #{i}:\n"
                prompt += f"Q: {p['question']}\n"
                prompt += f"A: {p['answer']}\n"

        prompt += """

ANALYSIS TASK:
Analyze each response and generate a comprehensive JSON output with the following structure:

{
  "summary": {
    "category": "<industry category from context>",
    "myBrand": "<my brand name>",
    "competitors": ["<competitor1>", "<competitor2>"]
  },

  "myBrandPerformance": {
    "brand": "<my brand name>",
    "platformPerformance": {
      "<platform1>": {
        "summary": "<Plain English summary: 'Mentioned X times across Y out of Z prompts. Ranked #N on this platform (Brand X ranked #1).' If not mentioned at all: 'Not mentioned on this platform.'>",
        "promptsMentionSummary": "<Which prompts mentioned/missed: 'Mentioned in Prompt #1 and Prompt #3. Missing from Prompt #2.' or 'Mentioned in all prompts.' or 'Missing from all prompts.'>"
      },
      "<platform2>": { ... }
    }
  },

  "competitorBrandPerformance": {
    "<competitor1>": {
      "platformPerformance": {
        "<platform1>": {
          "summary": "<same format as myBrandPerformance>",
          "promptsMentionSummary": "<same format>"
        }
      }
    },
    "<competitor2>": { ... }
  },

  "promptResults": [
    {
      "platform": "<platform name>",
      "prompts": [
        {
          "promptText": "<question>",
          "response": "<full answer>",
          "allBrandsMentioned": ["<brand1>", "<brand2>", ...]
        }
      ]
    }
  ]
}

ANALYSIS RULES:

1. **Brand Mention Detection**:
   - Count how many times each brand is explicitly mentioned in each response
   - Detect variations (e.g., "Salesforce", "salesforce.com", "SF")
   - Rank brands by: (1) mention count (higher = better), (2) first appearance position

2. **Summary Generation**:
   - Use plain English, no technical jargon
   - Format: "Mentioned X times across Y out of Z prompts. Ranked #N on this platform."
   - If brand ranked #1: "Ranked #1 on this platform."
   - If brand not #1: "Ranked #N on this platform (BrandX ranked #1)."
   - If not mentioned at all: "Not mentioned on this platform."

3. **Prompt Mention Summary**:
   - List which prompts mentioned the brand: "Mentioned in Prompt #1 and Prompt #3. Missing from Prompt #2."
   - If all mentioned: "Mentioned in all prompts."
   - If none mentioned: "Missing from all prompts."

4. **All Brands Mentioned**:
   - In promptResults, list ALL brands found (myBrand + competitors + any other brands)
   - Include brands even if not in competitors list
   - Use empty array [] if no brands mentioned

5. **Edge Cases**:
   - If platform failed or no response: summary = "Platform error - no data available."
   - If brand mentioned but never ranked #1: still show rank accurately
   - If tie in mentions: mention both as tied for rank

6. **Ranking Logic**:
   - Rank per platform based on total mention count across all prompts
   - Higher mentions = better rank (#1 is best)
   - If tied, use first appearance as tiebreaker

IMPORTANT:
- Return ONLY valid JSON, no markdown, no code blocks, no explanations
- Ensure all strings are properly escaped
- Use exact brand names as provided (preserve capitalization)
- Be accurate with counts and rankings

Generate the analysis now:"""

        return prompt

    async def analyze_all_responses(
        self,
        my_brand: str,
        competitors: list[str],
        category: str,
        platform_responses: list[dict]
    ) -> Optional[dict]:
        """
        Analyze all platform responses and generate consolidated output.

        Args:
            my_brand: User's brand name
            competitors: List of competitor brands
            category: Industry category
            platform_responses: List of response dicts with platform, prompt_text, response

        Returns:
            Complete output structure as dict, or None if failed
        """
        try:
            prompt = self._build_analysis_prompt(my_brand, competitors, platform_responses)

            self.logger.info(f"[Analyzer] Analyzing {len(platform_responses)} responses with {self.provider.value}...")

            if self.provider == AnalysisProvider.OPENAI:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a brand visibility analyst. Analyze AI responses and return structured JSON data."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content

            elif self.provider == AnalysisProvider.ANTHROPIC:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=8000,
                    temperature=0.1,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                result_text = response.content[0].text

            elif self.provider == AnalysisProvider.GOOGLE:
                import google.generativeai as genai
                model = genai.GenerativeModel(
                    self.model,
                    generation_config={
                        "temperature": 0.1,
                        "response_mime_type": "application/json"
                    }
                )
                response = await model.generate_content_async(prompt)
                result_text = response.text

            else:
                self.logger.error(f"Unsupported provider: {self.provider}")
                return None

            # Parse JSON
            try:
                output = json.loads(result_text)

                # Add category to summary (from input, more reliable than LLM inference)
                if "summary" in output:
                    output["summary"]["category"] = category

                self.logger.info("[Analyzer] Analysis complete!")
                return output

            except json.JSONDecodeError as e:
                self.logger.error(f"[Analyzer] Failed to parse JSON: {e}")
                self.logger.error(f"Raw response: {result_text[:500]}")
                return None

        except Exception as e:
            self.logger.error(f"[Analyzer] Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None
