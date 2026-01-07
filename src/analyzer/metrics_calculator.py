"""Calculate visibility metrics from extracted data."""

from typing import Optional
from dataclasses import dataclass, field
from ..config import BrandMention, PromptResult


@dataclass
class BrandMetrics:
    """Aggregated metrics for a single brand."""
    brand: str
    visibility_score: float = 0.0
    citation_share: float = 0.0
    total_mentions: int = 0
    total_prompts_analyzed: int = 0
    prompts_with_mention: int = 0
    prompts_missed: int = 0
    prompts_won: int = 0
    prompts_lost: int = 0
    prompts_tied: int = 0
    platform_breakdown: dict = field(default_factory=dict)
    top_contexts: list[str] = field(default_factory=list)


class MetricsCalculator:
    """Calculate visibility and competitive metrics."""

    def calculate_visibility_score(
        self,
        prompts_with_mention: int,
        total_prompts: int
    ) -> float:
        """
        Calculate visibility score (0-100).

        Visibility = (prompts with at least one mention / total prompts) * 100
        """
        if total_prompts == 0:
            return 0.0
        return round((prompts_with_mention / total_prompts) * 100, 1)

    def calculate_citation_share(
        self,
        brand_mentions: int,
        total_mentions: int
    ) -> float:
        """
        Calculate citation share (0-100).

        Citation Share = (brand's total mentions / all mentions) * 100
        """
        if total_mentions == 0:
            return 0.0
        return round((brand_mentions / total_mentions) * 100, 1)

    def determine_winner(self, mentions: list[BrandMention]) -> Optional[str]:
        """
        Determine winner for a prompt based on mentions.

        Winner is the brand with:
        1. Highest mention count, OR
        2. If tied, the one mentioned first (rank 1)
        """
        if not mentions:
            return None

        # Sort by count (desc), then by rank (asc)
        sorted_mentions = sorted(
            mentions,
            key=lambda m: (-m.count, m.rank)
        )

        if len(sorted_mentions) == 0:
            return None

        top = sorted_mentions[0]

        # Check for tie
        if len(sorted_mentions) > 1 and sorted_mentions[1].count == top.count:
            # It's a tie based on count, winner is the one with lower rank
            if sorted_mentions[1].rank < top.rank:
                return sorted_mentions[1].brand
            elif sorted_mentions[1].rank == top.rank:
                return None  # True tie

        return top.brand

    def determine_loser(self, mentions: list[BrandMention]) -> Optional[str]:
        """
        Determine loser for a prompt based on mentions.

        Loser is the brand with lowest mention count (if mentioned at all).
        """
        if len(mentions) < 2:
            return None

        # Sort by count (asc), then by rank (desc)
        sorted_mentions = sorted(
            mentions,
            key=lambda m: (m.count, -m.rank)
        )

        return sorted_mentions[0].brand

    def calculate_brand_metrics(
        self,
        brand: str,
        prompt_results: list[PromptResult],
        all_brands: list[str]
    ) -> BrandMetrics:
        """
        Calculate comprehensive metrics for a single brand.

        Args:
            brand: The brand to calculate metrics for
            prompt_results: All prompt results
            all_brands: All brands being tracked

        Returns:
            BrandMetrics object with all calculated metrics
        """
        metrics = BrandMetrics(brand=brand)

        # Group results by platform
        platform_data: dict[str, dict] = {}

        total_all_mentions = 0
        brand_total_mentions = 0
        prompts_by_platform: dict[str, int] = {}
        mentions_by_platform: dict[str, int] = {}
        prompts_with_mention_by_platform: dict[str, int] = {}
        contexts: list[str] = []

        for result in prompt_results:
            platform = result.platform

            # Initialize platform tracking
            if platform not in prompts_by_platform:
                prompts_by_platform[platform] = 0
                mentions_by_platform[platform] = 0
                prompts_with_mention_by_platform[platform] = 0

            prompts_by_platform[platform] += 1
            metrics.total_prompts_analyzed += 1

            # Count all mentions for citation share calculation
            for mention in result.mentions:
                total_all_mentions += mention.count

            # Find this brand's mention in the result
            brand_mention = next(
                (m for m in result.mentions if m.brand.lower() == brand.lower()),
                None
            )

            if brand_mention:
                metrics.prompts_with_mention += 1
                prompts_with_mention_by_platform[platform] += 1

                brand_total_mentions += brand_mention.count
                metrics.total_mentions += brand_mention.count
                mentions_by_platform[platform] += brand_mention.count

                if brand_mention.context:
                    contexts.append(brand_mention.context)
            else:
                metrics.prompts_missed += 1

            # Check win/loss
            if result.prompt_winner:
                if result.prompt_winner.lower() == brand.lower():
                    metrics.prompts_won += 1
                else:
                    # Check if brand was mentioned at all
                    if brand_mention:
                        if result.prompt_loser and result.prompt_loser.lower() == brand.lower():
                            metrics.prompts_lost += 1
                        else:
                            metrics.prompts_tied += 1

        # Calculate overall metrics
        metrics.visibility_score = self.calculate_visibility_score(
            metrics.prompts_with_mention,
            metrics.total_prompts_analyzed
        )
        metrics.citation_share = self.calculate_citation_share(
            brand_total_mentions,
            total_all_mentions
        )

        # Calculate platform breakdown
        for platform in prompts_by_platform:
            total_prompts = prompts_by_platform[platform]
            prompts_mentioned = prompts_with_mention_by_platform[platform]
            mentions = mentions_by_platform[platform]

            # Calculate platform-specific citation share
            platform_total_mentions = sum(
                m.count
                for r in prompt_results
                if r.platform == platform
                for m in r.mentions
            )

            metrics.platform_breakdown[platform] = {
                "visibilityScore": self.calculate_visibility_score(prompts_mentioned, total_prompts),
                "citationShare": self.calculate_citation_share(mentions, platform_total_mentions),
                "mentions": mentions,
                "promptsWithMention": prompts_mentioned,
            }

        # Get top unique contexts (max 5)
        seen_contexts = set()
        for ctx in contexts:
            ctx_lower = ctx.lower()[:50]  # Use first 50 chars for dedup
            if ctx_lower not in seen_contexts:
                seen_contexts.add(ctx_lower)
                metrics.top_contexts.append(ctx)
                if len(metrics.top_contexts) >= 5:
                    break

        return metrics

    def build_leaderboard(
        self,
        brand_metrics: list[BrandMetrics]
    ) -> list[dict]:
        """
        Build leaderboard ranking from brand metrics.

        Args:
            brand_metrics: List of BrandMetrics for all brands

        Returns:
            Sorted leaderboard (highest visibility first)
        """
        # Sort by total_mentions (primary), then visibility_score (secondary)
        sorted_metrics = sorted(
            brand_metrics,
            key=lambda m: (-m.total_mentions, -m.visibility_score)
        )

        leaderboard = []
        for i, metrics in enumerate(sorted_metrics):
            leaderboard.append({
                "rank": i + 1,
                "brand": metrics.brand,
                "visibilityScore": metrics.visibility_score,
                "citationShare": metrics.citation_share,
                "totalMentions": metrics.total_mentions,
                "promptsWon": metrics.prompts_won,
            })

        return leaderboard

    def build_platform_leaderboards(
        self,
        brand_metrics: list[BrandMetrics],
        platforms: list[str]
    ) -> dict[str, list[dict]]:
        """
        Build platform-specific leaderboards.

        Args:
            brand_metrics: List of BrandMetrics for all brands
            platforms: List of platforms to build leaderboards for

        Returns:
            Dict mapping platform to leaderboard
        """
        platform_leaderboards = {}

        for platform in platforms:
            # Get platform-specific data
            platform_data = []
            for metrics in brand_metrics:
                if platform in metrics.platform_breakdown:
                    pb = metrics.platform_breakdown[platform]
                    platform_data.append({
                        "brand": metrics.brand,
                        "citationShare": pb["citationShare"],
                        "mentions": pb["mentions"],
                    })

            # Sort by citation share
            platform_data.sort(key=lambda x: -x["citationShare"])

            # Add ranks
            for i, item in enumerate(platform_data):
                item["rank"] = i + 1

            platform_leaderboards[platform] = platform_data

        return platform_leaderboards
