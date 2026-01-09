"""Configuration dataclasses for AI Brand Tracker."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Platform(Enum):
    """Supported AI platforms."""
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"


# Model configurations (best available, hardcoded for v1)
PLATFORM_MODELS = {
    Platform.CHATGPT: "gpt-4o",
    Platform.CLAUDE: "claude-sonnet-4-20250514",
    Platform.GEMINI: "gemini-2.5-flash",
}


@dataclass
class APIKeys:
    """API keys for various platforms."""
    openai: Optional[str] = None
    anthropic: Optional[str] = None
    google: Optional[str] = None

    def get_key_for_platform(self, platform: Platform) -> Optional[str]:
        """Get API key for a specific platform."""
        mapping = {
            Platform.CHATGPT: self.openai,
            Platform.CLAUDE: self.anthropic,
            Platform.GEMINI: self.google,
        }
        return mapping.get(platform)

    def get_first_available_key(self) -> tuple[Optional[str], Optional[Platform]]:
        """Get first available API key (for prompt generation)."""
        for platform in [Platform.GEMINI, Platform.CHATGPT, Platform.CLAUDE]:
            key = self.get_key_for_platform(platform)
            if key:
                return key, platform
        return None, None


@dataclass
class ActorInput:
    """Parsed actor input."""
    category: str
    your_brand: str
    competitors: list[str] = field(default_factory=list)
    platforms: list[Platform] = field(default_factory=list)
    prompt_count: int = 1
    custom_prompts: list[str] = field(default_factory=list)
    api_keys: APIKeys = field(default_factory=APIKeys)
    proxy_config: Optional[dict] = None

    @property
    def all_brands(self) -> list[str]:
        """Get all brands to track (your brand + competitors)."""
        return [self.your_brand] + self.competitors

    @classmethod
    def from_raw_input(cls, raw: dict) -> "ActorInput":
        """Parse raw actor input into ActorInput."""
        platforms = []
        for p in raw.get("platforms", []):
            try:
                platforms.append(Platform(p.lower()))
            except ValueError:
                pass  # Skip invalid platforms

        api_keys = APIKeys(
            openai=raw.get("openaiApiKey", "").strip() or None,
            anthropic=raw.get("anthropicApiKey", "").strip() or None,
            google=raw.get("googleApiKey", "").strip() or None,
        )

        return cls(
            category=raw.get("category", "").strip(),
            your_brand=raw.get("yourBrand", "").strip(),
            competitors=[c.strip() for c in raw.get("competitors", []) if c.strip()],
            platforms=platforms,
            prompt_count=raw.get("promptCount", 5),
            custom_prompts=[p.strip() for p in raw.get("customPrompts", []) if p.strip()],
            api_keys=api_keys,
            proxy_config=raw.get("proxyConfiguration"),
        )


@dataclass
class BrandMention:
    """A brand mention extracted from a response."""
    brand: str
    count: int
    rank: int
    context: str
    is_recommended: bool


@dataclass
class PlatformResponse:
    """Response from an AI platform."""
    platform: Platform
    model: str
    prompt: str
    prompt_id: str
    response: str
    success: bool
    error: Optional[str] = None


@dataclass
class PromptResult:
    """Analyzed result for a single prompt on a single platform."""
    prompt_id: str
    prompt_text: str
    platform: str
    platform_model: str
    raw_response: str
    mentions: list[BrandMention]
    citations: list[str]
    prompt_winner: Optional[str]
    prompt_loser: Optional[str]
    your_brand_mentioned: bool
    your_brand_rank: Optional[int]
    competitors_mentioned: list[str]
    competitors_missed: list[str]

    def to_dict(self) -> dict:
        """Convert to output dictionary."""
        return {
            "type": "prompt_result",
            "promptId": self.prompt_id,
            "promptText": self.prompt_text,
            "platform": self.platform,
            "platformModel": self.platform_model,
            "rawResponse": self.raw_response,
            "mentions": [
                {
                    "brand": m.brand,
                    "count": m.count,
                    "rank": m.rank,
                    "context": m.context,
                    "isRecommended": m.is_recommended,
                }
                for m in self.mentions
            ],
            "citations": self.citations,
            "promptWinner": self.prompt_winner,
            "promptLoser": self.prompt_loser,
            "yourBrandMentioned": self.your_brand_mentioned,
            "yourBrandRank": self.your_brand_rank,
            "competitorsMentioned": self.competitors_mentioned,
            "competitorsMissed": self.competitors_missed,
        }
