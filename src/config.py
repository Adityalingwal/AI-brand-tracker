"""Configuration dataclasses for AI Brand Tracker."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Platform(Enum):
    """Supported AI platforms (browser-scraped, no API needed)."""
    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"


# Model names (these are the free tier models we get via browser)
PLATFORM_MODELS = {
    Platform.CHATGPT: "gpt-4o-mini (free)",
    Platform.GEMINI: "gemini-2.0-flash (free)",
    Platform.PERPLEXITY: "perplexity-default (free)",
}


class AnalysisProvider(Enum):
    """Supported providers for LLM-based analysis."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass
class AnalysisAPIKeys:
    """API keys for LLM analysis (user provides at least one)."""
    openai: Optional[str] = None
    anthropic: Optional[str] = None
    google: Optional[str] = None

    def get_first_available(self) -> tuple[Optional[str], Optional[AnalysisProvider]]:
        """Get first available API key for analysis."""
        if self.google:
            return self.google, AnalysisProvider.GOOGLE
        if self.openai:
            return self.openai, AnalysisProvider.OPENAI
        if self.anthropic:
            return self.anthropic, AnalysisProvider.ANTHROPIC
        return None, None

    def has_any_key(self) -> bool:
        """Check if any API key is available."""
        return bool(self.openai or self.anthropic or self.google)


@dataclass
class ActorInput:
    """Parsed actor input."""
    category: str
    your_brand: str
    competitors: list[str] = field(default_factory=list)
    platforms: list[Platform] = field(default_factory=list)
    prompt_count: int = 1
    custom_prompts: list[str] = field(default_factory=list)
    analysis_keys: AnalysisAPIKeys = field(default_factory=AnalysisAPIKeys)
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
                pass  # Skip invalid platforms (e.g., old 'claude' value)

        analysis_keys = AnalysisAPIKeys(
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
            analysis_keys=analysis_keys,
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
