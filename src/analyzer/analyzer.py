"""Brand visibility analyzer."""

import json
from typing import Optional
from ..utils import sanitize_error_message


class BrandAnalyzer:
    """Analyzes AI platform responses to track brand visibility and mentions."""

    def __init__(self, api_key: str, logger):
        self.api_key = api_key
        self.logger = logger

        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-haiku-4-5-20251001"

    def _build_analysis_prompt(
        self,
        my_brand: str,
        competitors: list[str],
        platform_responses: list[dict]
    ) -> str:
        platform_data = {}
        for resp in platform_responses:
            platform = resp["platform"]
            if platform not in platform_data:
                platform_data[platform] = []
            platform_data[platform].append({
                "question": resp["prompt_text"],
                "answer": resp["response"]
            })

        _divisor = len(platform_data) if platform_data else 1
        _prompts_per_platform = len(platform_responses) // _divisor

        prompt = f"""You are analyzing AI platform responses to track brand mentions and visibility.

INPUT DATA:
- My Brand: "{my_brand[:500]}"
- Competitors: {json.dumps([c[:500] for c in competitors], ensure_ascii=False)}
- Total Platforms: {len(platform_data)}
- Total Prompts per Platform: {_prompts_per_platform}

PLATFORM RESPONSES:
"""

        for platform, prompts in platform_data.items():
            prompt += f"\n=== Platform: {str(platform)[:100]} ===\n"
            for i, p in enumerate(prompts, 1):
                question = str(p.get('question', ''))[:2000]
                answer = str(p.get('answer', ''))[:50000]
                prompt += f"\nPrompt #{i}:\n"
                prompt += f"Q: {question}\n"
                prompt += f"A: {answer}\n"

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

            self.logger.info(f"[Analyzer] Analyzing {len(platform_responses)} responses...")

            api_params = {
                "model": self.model,
                "max_tokens": 12000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            import asyncio
            try:
                response = await asyncio.wait_for(
                    self.client.messages.create(**api_params),
                    timeout=300.0
                )
            except asyncio.TimeoutError:
                self.logger.error("[Analyzer] API call timed out after 300 seconds")
                return None

            result_text = ""
            for block in response.content:
                if block.type == "text":
                    result_text += block.text

            try:
                clean_text = result_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()

                output = json.loads(clean_text)

                if "summary" in output:
                    output["summary"]["category"] = category

                self.logger.info("[Analyzer] Analysis complete!")
                return output

            except json.JSONDecodeError as e:
                self.logger.error(f"[Analyzer] Failed to parse JSON: {e}")
                self.logger.error(f"Raw response: {result_text[:500]}")
                return None

        except Exception as e:
            self.logger.error(f"[Analyzer] Analysis failed: {sanitize_error_message(e)}")
            return None
