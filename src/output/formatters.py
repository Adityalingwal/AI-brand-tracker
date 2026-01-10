"""Output formatters for different record types."""

from typing import Optional
from datetime import datetime
from ..config import PromptResult, BrandMention
from ..analyzer.metrics_calculator import BrandMetrics


def format_prompt_result(
    prompt_id: str,
    prompt_text: str,
    platform: str,
    platform_model: str,
    raw_response: str,
    mentions: list[BrandMention],
    citations: list[str],
    my_brand: str,
    competitors: list[str],
) -> dict:
    """
    Format a prompt_result record for output.

    Args:
        prompt_id: Unique prompt identifier
        prompt_text: The prompt text
        platform: Platform name (chatgpt, claude, etc.)
        platform_model: Model used
        raw_response: Raw response from platform
        mentions: Extracted brand mentions
        citations: Extracted URLs
        my_brand: User's brand
        competitors: Competitor brands

    Returns:
        Formatted dictionary for dataset
    """
    # Determine winner and loser
    prompt_winner = None
    prompt_loser = None

    if mentions:
        # Sort by count (desc), then rank (asc)
        sorted_mentions = sorted(mentions, key=lambda m: (-m.count, m.rank))
        prompt_winner = sorted_mentions[0].brand if sorted_mentions else None

        if len(sorted_mentions) > 1:
            # Loser is the one with lowest count
            sorted_by_count = sorted(mentions, key=lambda m: m.count)
            prompt_loser = sorted_by_count[0].brand

    # Check if your brand is mentioned
    my_brand_mention = next(
        (m for m in mentions if m.brand.lower() == my_brand.lower()),
        None
    )
    my_brand_mentioned = my_brand_mention is not None
    my_brand_rank = my_brand_mention.rank if my_brand_mention else None

    # Determine which competitors were mentioned/missed
    mentioned_brands = {m.brand.lower() for m in mentions}
    competitors_mentioned = [c for c in competitors if c.lower() in mentioned_brands]
    competitors_missed = [c for c in competitors if c.lower() not in mentioned_brands]

    return {
        "type": "prompt_result",
        "promptId": prompt_id,
        "promptText": prompt_text,
        "platform": platform,
        "platformModel": platform_model,
        "rawResponse": raw_response,
        "mentions": [
            {
                "brand": m.brand,
                "count": m.count,
                "rank": m.rank,
                "context": m.context,
                "isRecommended": m.is_recommended,
            }
            for m in mentions
        ],
        "citations": citations,
        "promptWinner": prompt_winner,
        "promptLoser": prompt_loser,
        "myBrandMentioned": my_brand_mentioned,
        "myBrandRank": my_brand_rank,
        "competitorsMentioned": competitors_mentioned,
        "competitorsMissed": competitors_missed,
    }


def format_brand_summary(metrics: BrandMetrics) -> dict:
    """
    Format a brand_summary record for output.

    Args:
        metrics: Calculated brand metrics

    Returns:
        Formatted dictionary for dataset
    """
    return {
        "type": "brand_summary",
        "brand": metrics.brand,
        "overallMetrics": {
            "visibilityScore": metrics.visibility_score,
            "citationShare": metrics.citation_share,
            "totalMentions": metrics.total_mentions,
            "totalPromptsAnalyzed": metrics.total_prompts_analyzed,
            "promptsWithMention": metrics.prompts_with_mention,
            "promptsMissed": metrics.prompts_missed,
        },
        "platformBreakdown": metrics.platform_breakdown,
        "competitivePosition": {
            "rank": 0,  # Will be set from leaderboard
            "totalBrands": 0,  # Will be set from leaderboard
            "promptsWon": metrics.prompts_won,
            "promptsLost": metrics.prompts_lost,
            "promptsTied": metrics.prompts_tied,
        },
        "topContexts": metrics.top_contexts,
    }


def format_leaderboard(
    rankings: list[dict],
    platform_leaderboards: dict[str, list[dict]],
) -> dict:
    """
    Format a leaderboard record for output.

    Args:
        rankings: Overall brand rankings
        platform_leaderboards: Per-platform rankings

    Returns:
        Formatted dictionary for dataset
    """
    return {
        "type": "leaderboard",
        "rankings": rankings,
        "platformLeaderboards": platform_leaderboards,
    }


def format_run_summary(
    status: str,
    category: str,
    my_brand: str,
    competitors: list[str],
    platforms: list[str],
    prompt_count: int,
    started_at: datetime,
    completed_at: datetime,
    prompts_processed: int,
    responses_collected: int,
    events_charged: int,
    price_per_event: float = 0.02,
) -> dict:
    """
    Format a run_summary record for output.

    Args:
        status: Run status (completed, failed, etc.)
        category: Industry category
        my_brand: User's brand
        competitors: Competitor brands
        platforms: Platforms used
        prompt_count: Number of prompts requested
        started_at: Start timestamp
        completed_at: End timestamp
        prompts_processed: Prompts actually processed
        responses_collected: Total responses collected
        events_charged: Number of PPE events
        price_per_event: Price per event

    Returns:
        Formatted dictionary for dataset
    """
    duration_ms = int((completed_at - started_at).total_seconds() * 1000)

    return {
        "type": "run_summary",
        "status": status,
        "input": {
            "category": category,
            "myBrand": my_brand,
            "competitors": competitors,
            "platforms": platforms,
            "promptCount": prompt_count,
        },
        "execution": {
            "startedAt": started_at.isoformat(),
            "completedAt": completed_at.isoformat(),
            "durationMs": duration_ms,
            "promptsProcessed": prompts_processed,
            "responsesCollected": responses_collected,
        },
        "billing": {
            "eventType": "prompt_analyzed",
            "eventsCharged": events_charged,
            "pricePerEvent": price_per_event,
        },
    }
