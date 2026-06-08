"""Configuration dataclasses for AI Brand Visibility."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class Platform(Enum):
    """Supported AI platforms (browser-scraped, no API needed)."""
    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"

@dataclass
class ActorInput:
    """Parsed actor input."""
    category: str
    my_brand: str
    competitors: list[str] = field(default_factory=list)
    platforms: list[Platform] = field(default_factory=list)
    prompts: list[str] = field(default_factory=list)
    proxy_configuration: dict[str, Any] | None = None
    proxy_platforms: list[Platform] = field(default_factory=list)
    diagnostics_enabled: bool = True

    @property
    def all_brands(self) -> list[str]:
        """Get all brands to track (my brand + competitors)."""
        return [self.my_brand] + self.competitors

    @classmethod
    def from_raw_input(cls, raw: dict) -> "ActorInput":
        """Parse raw actor input into ActorInput."""
        platforms = []
        for p in raw.get("platforms", []):
            try:
                platforms.append(Platform(p.lower()))
            except ValueError:
                pass

        proxy_configuration = raw.get("proxyConfiguration")
        if proxy_configuration is None and Platform.CHATGPT in platforms:
            proxy_configuration = {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            }

        proxy_platforms = []
        for p in raw.get("proxyPlatforms", ["chatgpt"]):
            try:
                proxy_platforms.append(Platform(p.lower()))
            except ValueError:
                pass

        return cls(
            category=raw.get("category", "").strip(),
            my_brand=raw.get("myBrand", "").strip(),
            competitors=[c.strip() for c in raw.get("competitors", []) if c.strip()][:5],
            platforms=platforms,
            prompts=[p.strip() for p in raw.get("prompts", []) if p.strip()][:3],
            proxy_configuration=proxy_configuration,
            proxy_platforms=proxy_platforms,
            diagnostics_enabled=raw.get("diagnosticsEnabled", True),
        )
