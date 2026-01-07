"""
AI Brand Tracker - Main Orchestration.

Track brand visibility across AI platforms (ChatGPT, Claude, Gemini).
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional
from apify import Actor

from .config import ActorInput, Platform, PromptResult, BrandMention, PLATFORM_MODELS
from .utils import ProgressTracker, validate_input, InputValidationError
from .error_handling import ErrorTracker
from .prompt_generator import PromptGenerator
from .platforms import (
    BasePlatformClient,
    OpenAIClient,
    AnthropicClient,
    GoogleClient,
)
from .analyzer import MentionExtractor, MetricsCalculator
from .output import (
    format_prompt_result,
    format_brand_summary,
    format_leaderboard,
    format_run_summary,
)


def create_platform_client(
    platform: Platform,
    api_key: str,
    logger
) -> Optional[BasePlatformClient]:
    """Create a platform client for the given platform."""
    if platform == Platform.CHATGPT:
        return OpenAIClient(api_key, logger)
    elif platform == Platform.CLAUDE:
        return AnthropicClient(api_key, logger)
    elif platform == Platform.GEMINI:
        return GoogleClient(api_key, logger)
    return None


async def main():
    """Main entry point for the AI Brand Tracker actor."""

    async with Actor:
        logger = Actor.log
        progress = ProgressTracker(logger)
        error_tracker = ErrorTracker()
        started_at = datetime.now(timezone.utc)

        logger.info("")
        logger.info("=" * 60)
        logger.info("  AI Brand Tracker")
        logger.info("=" * 60)
        logger.info("  Track brand visibility across AI platforms")
        logger.info("=" * 60)

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

            # Push error to dataset (Apify requirement)
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
        progress.start_step("PROMPTS", "Generating prompts")

        # Get first available API key for prompt generation
        gen_key, gen_platform = actor_input.api_keys.get_first_available_key()

        if not gen_key or not gen_platform:
            logger.error("  No API key available for prompt generation")
            await Actor.push_data({
                "type": "error",
                "status": "failed",
                "message": "No API key available for prompt generation",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return

        logger.info(f"  Using {gen_platform.value} for prompt generation")

        prompt_generator = PromptGenerator(gen_key, gen_platform, logger)
        generated_prompts = await prompt_generator.generate(
            actor_input.category,
            actor_input.prompt_count
        )

        # Add custom prompts
        all_prompts = generated_prompts + actor_input.custom_prompts

        logger.info(f"  Generated: {len(generated_prompts)} prompts")
        logger.info(f"  Custom: {len(actor_input.custom_prompts)} prompts")
        logger.info(f"  Total: {len(all_prompts)} prompts")

        progress.complete_step("PROMPTS", items=len(all_prompts))

        # ============================================================
        # STEP 3: QUERY AI PLATFORMS (PARALLEL EXECUTION)
        # ============================================================
        progress.start_step("QUERY", f"Querying {len(actor_input.platforms)} AI platforms in parallel")

        # Create platform clients
        platform_clients: dict[Platform, BasePlatformClient] = {}
        for platform in actor_input.platforms:
            api_key = actor_input.api_keys.get_key_for_platform(platform)
            if api_key:
                client = create_platform_client(platform, api_key, logger)
                if client:
                    platform_clients[platform] = client
                    logger.info(f"  Initialized {platform.value} client")

        # Batch size for parallel prompt execution (to avoid rate limits)
        BATCH_SIZE = 5

        async def query_single_prompt(client: BasePlatformClient, platform: Platform, prompt_text: str, prompt_id: str) -> dict:
            """Query a single prompt on a platform."""
            try:
                result = await client.query_with_retry(prompt_text, max_retries=2)
                if result.success:
                    error_tracker.add_success(
                        f"{platform.value}:{prompt_id}",
                        {"prompt": prompt_text[:50]}
                    )
                    return {
                        "prompt_id": prompt_id,
                        "prompt_text": prompt_text,
                        "platform": platform.value,
                        "model": result.model,
                        "response": result.response,
                        "success": True,
                    }
                else:
                    error_tracker.add_error(
                        "query_failed",
                        result.error or "Unknown error",
                        context=f"{platform.value}:{prompt_id}"
                    )
                    return {
                        "prompt_id": prompt_id,
                        "prompt_text": prompt_text,
                        "platform": platform.value,
                        "model": result.model,
                        "response": "",
                        "success": False,
                        "error": result.error,
                    }
            except Exception as e:
                error_tracker.add_error(
                    "query_exception",
                    str(e),
                    context=f"{platform.value}:{prompt_id}"
                )
                return {
                    "prompt_id": prompt_id,
                    "prompt_text": prompt_text,
                    "platform": platform.value,
                    "model": "",
                    "response": "",
                    "success": False,
                    "error": str(e),
                }

        async def query_platform(platform: Platform, client: BasePlatformClient) -> list[dict]:
            """Query all prompts on a single platform in batches."""
            logger.info(f"  Starting {platform.value}...")
            platform_responses = []
            
            # Process prompts in batches
            for batch_start in range(0, len(all_prompts), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(all_prompts))
                batch_prompts = all_prompts[batch_start:batch_end]
                
                # Create tasks for this batch
                tasks = []
                for i, prompt_text in enumerate(batch_prompts):
                    prompt_idx = batch_start + i
                    prompt_id = f"{platform.value}_prompt_{prompt_idx:03d}"
                    tasks.append(query_single_prompt(client, platform, prompt_text, prompt_id))
                
                # Execute batch in parallel
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        error_tracker.add_error("batch_exception", str(result))
                    elif isinstance(result, dict):
                        platform_responses.append(result)
                
                # Small delay between batches to be safe
                if batch_end < len(all_prompts):
                    await asyncio.sleep(0.3)
            
            logger.info(f"  Completed {platform.value}: {len(platform_responses)} responses")
            return platform_responses

        # Query all platforms in parallel
        logger.info(f"  Running {len(platform_clients)} platforms in parallel...")
        platform_tasks = [
            query_platform(platform, client) 
            for platform, client in platform_clients.items()
        ]
        platform_results = await asyncio.gather(*platform_tasks, return_exceptions=True)

        # Collect all responses
        all_responses: list[dict] = []
        for result in platform_results:
            if isinstance(result, Exception):
                error_tracker.add_error("platform_exception", str(result))
            elif isinstance(result, list):
                all_responses.extend(result)

        logger.info(f"")
        logger.info(f"  Collected {len(all_responses)} responses")

        progress.complete_step(
            "QUERY",
            items=len(all_responses),
            details=f"{error_tracker.get_success_count()} successful"
        )

        # ============================================================
        # STEP 4: ANALYZE RESPONSES
        # ============================================================
        progress.start_step("ANALYZE", "Analyzing responses for brand mentions and citations")

        # Initialize analyzers (use same key as prompt generation)
        mention_extractor = MentionExtractor(gen_key, gen_platform, logger)
        metrics_calculator = MetricsCalculator()

        all_brands = actor_input.all_brands
        prompt_results: list[PromptResult] = []

        for i, response_data in enumerate(all_responses):
            if not response_data["success"] or not response_data["response"]:
                continue

            progress.log_progress(
                i + 1,
                len(all_responses),
                f"Analyzing {response_data['platform']}:{response_data['prompt_id']}"
            )

            try:
                # Extract mentions and citations in single LLM call
                extraction_result = await mention_extractor.extract(
                    response_data["response"],
                    all_brands
                )

                mentions = extraction_result.mentions
                citations = extraction_result.citations

                # Determine winner/loser
                prompt_winner = metrics_calculator.determine_winner(mentions)
                prompt_loser = metrics_calculator.determine_loser(mentions)

                # Check your brand
                your_brand_mention = next(
                    (m for m in mentions if m.brand.lower() == actor_input.your_brand.lower()),
                    None
                )

                # Build prompt result
                prompt_result = PromptResult(
                    prompt_id=response_data["prompt_id"],
                    prompt_text=response_data["prompt_text"],
                    platform=response_data["platform"],
                    platform_model=response_data["model"],
                    raw_response=response_data["response"],
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

                prompt_results.append(prompt_result)

                # Push prompt_result to dataset immediately
                await Actor.push_data(format_prompt_result(
                    prompt_id=prompt_result.prompt_id,
                    prompt_text=prompt_result.prompt_text,
                    platform=prompt_result.platform,
                    platform_model=prompt_result.platform_model,
                    raw_response=prompt_result.raw_response,
                    mentions=prompt_result.mentions,
                    citations=prompt_result.citations,
                    your_brand=actor_input.your_brand,
                    competitors=actor_input.competitors,
                ))

            except Exception as e:
                error_tracker.add_error(
                    "analysis_failed",
                    str(e),
                    context=f"{response_data['platform']}:{response_data['prompt_id']}"
                )

        logger.info(f"  Analyzed {len(prompt_results)} responses")

        progress.complete_step("ANALYZE", items=len(prompt_results))

        # ============================================================
        # STEP 5: CALCULATE METRICS & BUILD OUTPUTS
        # ============================================================
        progress.start_step("METRICS", "Calculating visibility metrics")

        # Calculate metrics for each brand
        brand_metrics_list = []
        for brand in all_brands:
            metrics = metrics_calculator.calculate_brand_metrics(
                brand,
                prompt_results,
                all_brands
            )
            brand_metrics_list.append(metrics)

        # Build leaderboard
        rankings = metrics_calculator.build_leaderboard(brand_metrics_list)
        platform_leaderboards = metrics_calculator.build_platform_leaderboards(
            brand_metrics_list,
            [p.value for p in actor_input.platforms]
        )

        # Update brand summaries with competitive position
        for metrics in brand_metrics_list:
            # Find rank in leaderboard
            rank_entry = next(
                (r for r in rankings if r["brand"] == metrics.brand),
                None
            )

            # Format and push brand_summary
            summary = format_brand_summary(metrics)
            summary["competitivePosition"]["rank"] = rank_entry["rank"] if rank_entry else 0
            summary["competitivePosition"]["totalBrands"] = len(all_brands)

            await Actor.push_data(summary)

        # Push leaderboard
        await Actor.push_data(format_leaderboard(rankings, platform_leaderboards))

        progress.complete_step("METRICS", items=len(brand_metrics_list))

        # ============================================================
        # STEP 6: FINALIZE
        # ============================================================
        progress.start_step("FINALIZE", "Finalizing run")

        completed_at = datetime.now(timezone.utc)
        events_charged = len(prompt_results)

        # Push run_summary
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

        # Charge for events (PPE)
        if events_charged > 0:
            try:
                await Actor.charge(
                    event_name="prompt-analyzed",
                    count=events_charged
                )
                logger.info(f"  Charged for {events_charged} prompt-analyzed events")
            except Exception as e:
                logger.debug(f"  PPE charging skipped: {e}")

        # Push error/warning summary to dataset if there were any issues
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
                    for e in error_tracker.errors[-10:]  # Last 10 errors
                ],
                "warnings": error_tracker.warnings[-5:],  # Last 5 warnings
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
        logger.info(f"  Platforms queried: {len(platform_clients)}")

        # Show quick visibility summary
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


if __name__ == "__main__":
    asyncio.run(main())
