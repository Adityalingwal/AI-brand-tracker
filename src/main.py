"""
AI Brand Tracker - Main Orchestration.

Track brand visibility across AI platforms (ChatGPT, Gemini, Perplexity).
Uses browser automation - no API keys needed for querying platforms!
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional
from apify import Actor

from .config import ActorInput, Platform, PromptResult, BrandMention, PLATFORM_MODELS, AnalysisProvider
from .utils import ProgressTracker, validate_input
from .error_handling import ErrorTracker
from .prompt_generator import PromptGenerator
from .browser_clients import BaseBrowserClient, ChatGPTBrowserClient, PerplexityBrowserClient, GeminiBrowserClient
from .analyzer import MentionExtractor, MetricsCalculator
from .output import (
    format_prompt_result,
    format_brand_summary,
    format_leaderboard,
    format_run_summary,
)


def create_browser_client(
    platform: Platform,
    logger,
    proxy_config: Optional[dict] = None
) -> Optional[BaseBrowserClient]:
    """Create a browser client for the given platform."""
    if platform == Platform.CHATGPT:
        return ChatGPTBrowserClient(logger, proxy_config)
    elif platform == Platform.PERPLEXITY:
        return PerplexityBrowserClient(logger, proxy_config)
    elif platform == Platform.GEMINI:
        return GeminiBrowserClient(logger, proxy_config)
    return None


async def query_platform(
    platform: Platform,
    prompts: list[str],
    logger,
    proxy_config: Optional[dict],
    error_tracker: ErrorTracker
) -> list[dict]:
    """Query a single platform with all prompts. Runs in parallel with other platforms."""
    responses = []
    
    client = create_browser_client(platform, logger, proxy_config)
    if not client:
        logger.warning(f"  {platform.value} not implemented, skipping...")
        return responses
    
    try:
        logger.info(f"  [{platform.value.upper()}] Initializing browser...")
        await client.initialize()
        
        for i, prompt_text in enumerate(prompts):
            prompt_id = f"{platform.value}_prompt_{i:03d}"
            
            try:
                result = await client.query_with_retry(prompt_text, max_retries=2)
                
                if result.success:
                    error_tracker.add_success(
                        f"{platform.value}:{prompt_id}",
                        {"prompt": prompt_text[:50]}
                    )
                    responses.append({
                        "prompt_id": prompt_id,
                        "prompt_text": prompt_text,
                        "platform": platform.value,
                        "model": result.model,
                        "response": result.response,
                        "success": True,
                    })
                    logger.info(f"  [{platform.value.upper()}] Query {i+1}/{len(prompts)} ✓")
                else:
                    error_tracker.add_error(
                        "query_failed",
                        result.error or "Unknown error",
                        context=f"{platform.value}:{prompt_id}"
                    )
                    responses.append({
                        "prompt_id": prompt_id,
                        "prompt_text": prompt_text,
                        "platform": platform.value,
                        "model": result.model,
                        "response": "",
                        "success": False,
                        "error": result.error,
                    })
                    logger.warning(f"  [{platform.value.upper()}] Query {i+1} failed: {result.error}")
                    
            except Exception as e:
                error_tracker.add_error(
                    "query_exception",
                    str(e),
                    context=f"{platform.value}:{prompt_id}"
                )
                responses.append({
                    "prompt_id": prompt_id,
                    "prompt_text": prompt_text,
                    "platform": platform.value,
                    "model": "",
                    "response": "",
                    "success": False,
                    "error": str(e),
                })
        
        logger.info(f"  [{platform.value.upper()}] Completed all queries")
        
    except Exception as e:
        logger.error(f"  [{platform.value.upper()}] Failed: {e}")
        error_tracker.add_error("platform_init_failed", str(e), context=platform.value)
    finally:
        await client.close()
    
    return responses


def get_analysis_api_key() -> tuple[Optional[str], Optional[AnalysisProvider]]:
    """Get analysis API key from environment variables."""
    # Priority: Google (free) > OpenAI > Anthropic
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
    """Main entry point for the AI Brand Tracker actor."""

    async with Actor:
        logger = Actor.log
        progress = ProgressTracker(logger)
        error_tracker = ErrorTracker()
        started_at = datetime.now(timezone.utc)

        logger.info("")
        logger.info("=" * 60)
        logger.info("  AI Brand Tracker v2 (Browser Mode)")
        logger.info("=" * 60)
        logger.info("  Track brand visibility across AI platforms")
        logger.info("  No API keys needed for querying!")
        logger.info("=" * 60)

        try:
            # ============================================================
            # STEP 1: INPUT VALIDATION
            # ============================================================
            progress.start_step("INPUT", "Parsing and validating input")

            raw_input = await Actor.get_input() or {}
            actor_input = ActorInput.from_raw_input(raw_input)

            # Validate input
            validation_errors = validate_input(actor_input)

            if validation_errors:
                logger.error("")
                logger.error("=" * 60)
                logger.error("  INPUT VALIDATION FAILED")
                logger.error("=" * 60)

                for error in validation_errors:
                    logger.error(f"  - {error.field}: {error.message}")
                    if error.help_text:
                        logger.error(f"    Help: {error.help_text}")

                await Actor.push_data({
                    "type": "validation_error",
                    "status": "failed",
                    "errors": [e.to_dict() for e in validation_errors],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

                progress.complete_step("INPUT", success=False, details="Validation failed")
                return

            logger.info(f"  Category: {actor_input.category}")
            logger.info(f"  Your Brand: {actor_input.your_brand}")
            logger.info(f"  Competitors: {actor_input.competitors or '(none)'}")
            logger.info(f"  Platforms: {[p.value for p in actor_input.platforms]}")
            logger.info(f"  Prompt Count: {actor_input.prompt_count}")

            progress.complete_step("INPUT", items=1, details="Validation passed")

            # ============================================================
            # STEP 2: PROMPT GENERATION
            # ============================================================
            progress.start_step("PROMPTS", "Preparing prompts")

            if actor_input.custom_prompts:
                all_prompts = actor_input.custom_prompts[:5]
                logger.info(f"  Using {len(all_prompts)} custom prompts")
            else:
                prompt_generator = PromptGenerator(logger)
                all_prompts = prompt_generator.generate(
                    actor_input.category,
                    actor_input.prompt_count
                )
                logger.info(f"  Using {len(all_prompts)} template prompts")

            logger.info(f"  Total prompts to analyze: {len(all_prompts)}")

            progress.complete_step("PROMPTS", items=len(all_prompts))

            # ============================================================
            # STEP 3: QUERY AI PLATFORMS (PARALLEL EXECUTION)
            # ============================================================
            progress.start_step("QUERY", f"Querying {len(actor_input.platforms)} AI platforms in PARALLEL")

            logger.info(f"  Starting parallel queries on: {[p.value for p in actor_input.platforms]}")

            # Run all platforms in parallel
            tasks = [
                query_platform(
                    platform,
                    all_prompts,
                    logger,
                    actor_input.proxy_config,
                    error_tracker
                )
                for platform in actor_input.platforms
            ]
            
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Flatten results
            all_responses: list[dict] = []
            for result in platform_results:
                if isinstance(result, Exception):
                    logger.error(f"  Platform error: {result}")
                elif isinstance(result, list):
                    all_responses.extend(result)

            logger.info(f"")
            logger.info(f"  Collected {len(all_responses)} responses from all platforms")

            progress.complete_step(
                "QUERY",
                items=len(all_responses),
                details=f"{error_tracker.get_success_count()} successful"
            )

            # ============================================================
            # STEP 4: ANALYZE RESPONSES (Using our API key from ENV)
            # ============================================================
            progress.start_step("ANALYZE", "Analyzing responses for brand mentions and citations")

            # Get API key from environment
            analysis_key, analysis_provider = get_analysis_api_key()
            
            if not analysis_key or not analysis_provider:
                logger.error("  No analysis API key configured in environment")
                logger.error("  Please set GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY")
                await Actor.push_data({
                    "type": "error",
                    "status": "failed",
                    "message": "No analysis API key configured. Contact actor developer.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return

            logger.info(f"  Using {analysis_provider.value} for analysis")
            
            mention_extractor = MentionExtractor(analysis_key, analysis_provider, logger)
            metrics_calculator = MetricsCalculator()

            all_brands = actor_input.all_brands
            prompt_results: list[PromptResult] = []
            
            # Filter successful responses
            valid_responses = [r for r in all_responses if r["success"] and r["response"]]
            
            if not valid_responses:
                logger.warning("  No valid responses to analyze")
            else:
                # Analyze all responses in a single batch
                logger.info(f"  Analyzing {len(valid_responses)} responses...")
                
                try:
                    extraction_results = await mention_extractor.extract_batch(valid_responses, all_brands)
                    extraction_map = {r.prompt_id: r for r in extraction_results}
                    
                    for resp in valid_responses:
                        prompt_id = resp["prompt_id"]
                        extraction = extraction_map.get(prompt_id)
                        
                        if not extraction:
                            extraction = type('obj', (object,), {'mentions': [], 'citations': []})()
                        
                        mentions = extraction.mentions
                        citations = extraction.citations

                        prompt_winner = metrics_calculator.determine_winner(mentions)
                        prompt_loser = metrics_calculator.determine_loser(mentions)

                        your_brand_mention = next(
                            (m for m in mentions if m.brand.lower() == actor_input.your_brand.lower()),
                            None
                        )

                        result = PromptResult(
                            prompt_id=resp["prompt_id"],
                            prompt_text=resp["prompt_text"],
                            platform=resp["platform"],
                            platform_model=resp["model"],
                            raw_response=resp["response"],
                            mentions=mentions,
                            citations=citations,
                            prompt_winner=prompt_winner,
                            prompt_loser=prompt_loser,
                            your_brand_mentioned=your_brand_mention is not None,
                            your_brand_rank=your_brand_mention.rank if your_brand_mention else None,
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
                            platform_model=result.platform_model,
                            raw_response=result.raw_response,
                            mentions=result.mentions,
                            citations=result.citations,
                            your_brand=actor_input.your_brand,
                            competitors=actor_input.competitors,
                        ))
                        
                except Exception as e:
                    logger.error(f"  Analysis failed: {e}")
                    error_tracker.add_error("analysis_failed", str(e))

            logger.info(f"  Analyzed {len(prompt_results)} responses")

            progress.complete_step("ANALYZE", items=len(prompt_results))

            # ============================================================
            # STEP 5: CALCULATE METRICS & BUILD OUTPUTS
            # ============================================================
            progress.start_step("METRICS", "Calculating visibility metrics")

            brand_metrics_list = []
            for brand in all_brands:
                metrics = metrics_calculator.calculate_brand_metrics(
                    brand,
                    prompt_results,
                    all_brands
                )
                brand_metrics_list.append(metrics)

            rankings = metrics_calculator.build_leaderboard(brand_metrics_list)
            platform_leaderboards = metrics_calculator.build_platform_leaderboards(
                brand_metrics_list,
                [p.value for p in actor_input.platforms]
            )

            for metrics in brand_metrics_list:
                rank_entry = next(
                    (r for r in rankings if r["brand"] == metrics.brand),
                    None
                )

                summary = format_brand_summary(metrics)
                summary["competitivePosition"]["rank"] = rank_entry["rank"] if rank_entry else 0
                summary["competitivePosition"]["totalBrands"] = len(all_brands)

                await Actor.push_data(summary)

            await Actor.push_data(format_leaderboard(rankings, platform_leaderboards))

            progress.complete_step("METRICS", items=len(brand_metrics_list))

            # ============================================================
            # STEP 6: FINALIZE
            # ============================================================
            progress.start_step("FINALIZE", "Finalizing run")

            completed_at = datetime.now(timezone.utc)
            events_charged = len(prompt_results)

            await Actor.push_data(format_run_summary(
                status="completed",
                category=actor_input.category,
                your_brand=actor_input.your_brand,
                competitors=actor_input.competitors,
                platforms=[p.value for p in actor_input.platforms],
                prompt_count=actor_input.prompt_count,
                started_at=started_at,
                completed_at=completed_at,
                prompts_processed=len(all_prompts),
                responses_collected=len(all_responses),
                events_charged=events_charged,
            ))

            if events_charged > 0:
                try:
                    await Actor.charge(
                        event_name="prompt-analyzed",
                        count=events_charged
                    )
                    logger.info(f"  Charged for {events_charged} prompt-analyzed events")
                except Exception as e:
                    logger.debug(f"  PPE charging skipped: {e}")

            if error_tracker.get_error_count() > 0 or len(error_tracker.warnings) > 0:
                await Actor.push_data({
                    "type": "error_summary",
                    "totalErrors": error_tracker.get_error_count(),
                    "totalWarnings": len(error_tracker.warnings),
                    "hasFatalErrors": error_tracker.has_fatal_errors(),
                    "errors": [
                        {
                            "errorType": e.error_type,
                            "message": e.message,
                            "context": e.context,
                            "recoverable": e.recoverable,
                        }
                        for e in error_tracker.errors[-10:]
                    ],
                    "warnings": error_tracker.warnings[-5:],
                })

            progress.complete_step("FINALIZE", items=1)

            # ============================================================
            # SUMMARY
            # ============================================================
            progress.log_summary()
            error_tracker.print_summary(logger)

            logger.info("")
            logger.info("=" * 60)
            logger.info("  RUN COMPLETED")
            logger.info("=" * 60)
            logger.info(f"  Prompts analyzed: {len(prompt_results)}")
            logger.info(f"  Brands tracked: {len(all_brands)}")
            logger.info(f"  Platforms queried: {len(actor_input.platforms)}")

            your_brand_metrics = next(
                (m for m in brand_metrics_list if m.brand == actor_input.your_brand),
                None
            )
            if your_brand_metrics:
                logger.info(f"")
                logger.info(f"  YOUR BRAND: {actor_input.your_brand}")
                logger.info(f"  Visibility Score: {your_brand_metrics.visibility_score}%")
                logger.info(f"  Citation Share: {your_brand_metrics.citation_share}%")
                logger.info(f"  Total Mentions: {your_brand_metrics.total_mentions}")

            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
