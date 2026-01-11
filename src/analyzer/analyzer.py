"""Brand visibility analyzer."""

import asyncio
import json
from typing import Optional

from anthropic import AsyncAnthropic

from ..utils import sanitize_error_message
from .prompts import build_analysis_prompt


class BrandAnalyzer:
    """Analyzes AI platform responses to track brand visibility and mentions."""

    def __init__(self, api_key: str, logger):
        self.api_key = api_key
        self.logger = logger
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-haiku-4-5-20251001"

    async def analyze_all_responses(
        self,
        my_brand: str,
        competitors: list[str],
        category: str,
        platform_responses: list[dict]
    ) -> Optional[dict]:
        try:
            prompt = build_analysis_prompt(my_brand, competitors, platform_responses, category)

            self.logger.info("Analyzing responses...")

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

            response = None
            for attempt in range(2):
                try:
                    response = await asyncio.wait_for(
                        self.client.messages.create(**api_params),
                        timeout=300.0
                    )
                    break
                except asyncio.TimeoutError:
                    if attempt == 1:
                        self.logger.error("Analysis timed out")
                        return None
                    await asyncio.sleep(2)
                except Exception:
                    if attempt == 1:
                        self.logger.error("Analysis failed")
                        return None
                    await asyncio.sleep(2)

            if not response:
                self.logger.error("Analysis failed")
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

                self.logger.info("Analysis complete")
                return output

            except json.JSONDecodeError:
                self.logger.error("Analysis failed - invalid response format")
                return None

        except Exception:
            self.logger.error("Analysis failed")
            return None
