"""AI Brand Tracker - Track brand visibility across AI platforms."""

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional
from apify import Actor

from .config import ActorInput, Platform, PromptResult, BrandMention, AnalysisProvider
from .utils import validate_input
from .error_handling import ErrorTracker
from .browser_clients import ChatGPTBrowserClient, PerplexityBrowserClient, GeminiBrowserClient
from .analyzer import MentionExtractor, MetricsCalculator
from .output import format_prompt_result, format_brand_summary, format_leaderboard, format_run_summary


def create_browser_client(platform: Platform, logger):
    """Create a browser client for the given platform."""
    if platform == Platform.CHATGPT:
        return ChatGPTBrowserClient(logger, None)
    elif platform == Platform.PERPLEXITY:
        return PerplexityBrowserClient(logger, None)
    elif platform == Platform.GEMINI:
        return GeminiBrowserClient(logger, None)
    return None


async def query_platform(platform: Platform, prompts: list[str], logger, error_tracker: ErrorTracker) -> list[dict]:
    """Query a single platform with all prompts."""
    responses = []
    client = create_browser_client(platform, logger)
    
    if not client:
        return responses
    
    try:
        await client.initialize()
        
        for i, prompt_text in enumerate(prompts):
            prompt_id = f"{platform.value}_{i:03d}"
            
            try:
                result = await client.query_with_retry(prompt_text, max_retries=2)
                
                if result.success:
                    error_tracker.add_success(f"{platform.value}:{prompt_id}", {})
                    responses.append({
                        "prompt_id": prompt_id,
                        "prompt_text": prompt_text,
                        "platform": platform.value,
                        "response": result.response,
                        "success": True,
                    })
                    logger.info(f"[{platform.value}] Query {i+1}/{len(prompts)} done")
                else:
                    error_tracker.add_error("query_failed", result.error or "Unknown", context=prompt_id)
                    responses.append({
                        "prompt_id": prompt_id,
                        "prompt_text": prompt_text,
                        "platform": platform.value,
                        "response": "",
                        "success": False,
                        "error": result.error,
                    })
                    
            except Exception as e:
                error_tracker.add_error("query_exception", str(e), context=prompt_id)
                responses.append({
                    "prompt_id": prompt_id,
                    "prompt_text": prompt_text,
                    "platform": platform.value,
                    "response": "",
                    "success": False,
                    "error": str(e),
                })
        
    except Exception as e:
        logger.error(f"[{platform.value}] Failed: {e}")
        error_tracker.add_error("platform_failed", str(e), context=platform.value)
    finally:
        await client.close()
    
    return responses


def get_analysis_api_key() -> tuple[Optional[str], Optional[AnalysisProvider]]:
    """Get analysis API key from environment."""
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if google_key:
        return google_key, AnalysisProvider.GOOGLE
    
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        return openai_key, AnalysisProvider.OPENAI
    
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        return anthropic_key, AnalysisProvider.ANTHROPIC
    
    return None, None


async def main():
    """Main entry point."""

    async with Actor:
        logger = Actor.log
        error_tracker = ErrorTracker()
        started_at = datetime.now(timezone.utc)

        logger.info("AI Brand Tracker - Starting")

        try:
            # Parse input
            raw_input = await Actor.get_input() or {}
            actor_input = ActorInput.from_raw_input(raw_input)

            # Validate
            validation_errors = validate_input(actor_input)
            if validation_errors:
                for error in validation_errors:
                    logger.error(f"Validation error: {error.field} - {error.message}")
                await Actor.push_data({
                    "type": "error",
                    "message": "Input validation failed",
                    "errors": [e.to_dict() for e in validation_errors],
                })
                return

            logger.info(f"Category: {actor_input.category}")
            logger.info(f"Brand: {actor_input.my_brand}")
            logger.info(f"Platforms: {[p.value for p in actor_input.platforms]}")
            logger.info(f"Prompts: {len(actor_input.prompts)}")

            # Use prompts from input
            all_prompts = actor_input.prompts

            # Query all platforms in parallel
            logger.info(f"Querying {len(actor_input.platforms)} platform(s)...")
            
            tasks = [
                query_platform(platform, all_prompts, logger, error_tracker)
                for platform in actor_input.platforms
            ]
            
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_responses = []
            for result in platform_results:
                if isinstance(result, list):
                    all_responses.extend(result)

            logger.info(f"Collected {len(all_responses)} responses")

            # Analyze responses
            analysis_key, analysis_provider = get_analysis_api_key()
            
            if not analysis_key:
                logger.error("No analysis API key configured")
                await Actor.push_data({
                    "type": "error",
                    "message": "Analysis API key not configured",
                })
                return

            mention_extractor = MentionExtractor(analysis_key, analysis_provider, logger)
            metrics_calculator = MetricsCalculator()

            all_brands = actor_input.all_brands
            prompt_results = []
            
            valid_responses = [r for r in all_responses if r["success"] and r["response"]]
            
            if valid_responses:
                logger.info(f"Analyzing {len(valid_responses)} responses...")
                
                try:
                    extraction_results = await mention_extractor.extract_batch(valid_responses, all_brands)
                    extraction_map = {r.prompt_id: r for r in extraction_results}
                    
                    for resp in valid_responses:
                        extraction = extraction_map.get(resp["prompt_id"])
                        mentions = extraction.mentions if extraction else []
                        citations = extraction.citations if extraction else []

                        my_brand_mention = next(
                            (m for m in mentions if m.brand.lower() == actor_input.my_brand.lower()),
                            None
                        )

                        result = PromptResult(
                            prompt_id=resp["prompt_id"],
                            prompt_text=resp["prompt_text"],
                            platform=resp["platform"],
                            platform_model="",  # Not exposing model info
                            raw_response=resp["response"],
                            mentions=mentions,
                            citations=citations,
                            prompt_winner=metrics_calculator.determine_winner(mentions),
                            prompt_loser=metrics_calculator.determine_loser(mentions),
                            my_brand_mentioned=my_brand_mention is not None,
                            my_brand_rank=my_brand_mention.rank if my_brand_mention else None,
                            competitors_mentioned=[
                                m.brand for m in mentions
                                if m.brand.lower() in [c.lower() for c in actor_input.competitors]
                            ],
                            competitors_missed=[
                                c for c in actor_input.competitors
                                if c.lower() not in [m.brand.lower() for m in mentions]
                            ],
                        )
                        prompt_results.append(result)
                        
                        await Actor.push_data(format_prompt_result(
                            prompt_id=result.prompt_id,
                            prompt_text=result.prompt_text,
                            platform=result.platform,
                            platform_model="",
                            raw_response=result.raw_response,
                            mentions=result.mentions,
                            citations=result.citations,
                            my_brand=actor_input.my_brand,
                            competitors=actor_input.competitors,
                        ))
                        
                except Exception as e:
                    logger.error(f"Analysis error: {e}")

            # Calculate metrics
            brand_metrics_list = []
            for brand in all_brands:
                metrics = metrics_calculator.calculate_brand_metrics(brand, prompt_results, all_brands)
                brand_metrics_list.append(metrics)

            rankings = metrics_calculator.build_leaderboard(brand_metrics_list)
            platform_leaderboards = metrics_calculator.build_platform_leaderboards(
                brand_metrics_list, [p.value for p in actor_input.platforms]
            )

            for metrics in brand_metrics_list:
                rank_entry = next((r for r in rankings if r["brand"] == metrics.brand), None)
                summary = format_brand_summary(metrics)
                summary["competitivePosition"]["rank"] = rank_entry["rank"] if rank_entry else 0
                summary["competitivePosition"]["totalBrands"] = len(all_brands)
                await Actor.push_data(summary)

            await Actor.push_data(format_leaderboard(rankings, platform_leaderboards))

            # Finalize
            completed_at = datetime.now(timezone.utc)
            
            await Actor.push_data(format_run_summary(
                status="completed",
                category=actor_input.category,
                my_brand=actor_input.my_brand,
                competitors=actor_input.competitors,
                platforms=[p.value for p in actor_input.platforms],
                prompt_count=len(actor_input.prompts),
                started_at=started_at,
                completed_at=completed_at,
                prompts_processed=len(all_prompts),
                responses_collected=len(all_responses),
                events_charged=len(prompt_results),
            ))

            # Charge for events
            if len(prompt_results) > 0:
                try:
                    await Actor.charge(event_name="prompt-analyzed", count=len(prompt_results))
                except Exception:
                    pass

            # Log summary
            my_brand_metrics = next(
                (m for m in brand_metrics_list if m.brand == actor_input.my_brand), None
            )
            
            logger.info("=" * 40)
            logger.info("RESULTS")
            logger.info("=" * 40)
            logger.info(f"Brand: {actor_input.my_brand}")
            if my_brand_metrics:
                logger.info(f"Visibility: {my_brand_metrics.visibility_score}%")
                logger.info(f"Mentions: {my_brand_metrics.total_mentions}")
            logger.info(f"Analyzed: {len(prompt_results)}")
            logger.info("=" * 40)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
