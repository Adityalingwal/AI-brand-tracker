"""AI Brand Tracker - Track brand visibility across AI platforms."""

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional
from apify import Actor

# Load .env file for local development (Apify uses environment variables directly)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment variables

from .config import ActorInput, Platform
from .utils import validate_input
from .error_handling import ErrorTracker
from .browser_clients import ChatGPTBrowserClient, PerplexityBrowserClient, GeminiBrowserClient
from .analyzer import BrandAnalyzer


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


def get_analysis_api_key() -> Optional[str]:
    """Get Anthropic API key from environment."""
    return os.environ.get("ANTHROPIC_API_KEY")


async def main():
    """Main entry point."""

    async with Actor:
        logger = Actor.log
        error_tracker = ErrorTracker()
        started_at = datetime.now(timezone.utc)

        logger.info("AI Brand Tracker - Starting")

        try:
            raw_input = await Actor.get_input() or {}
            actor_input = ActorInput.from_raw_input(raw_input)

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

            all_prompts = actor_input.prompts

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

            valid_responses = [r for r in all_responses if r["success"] and r["response"]]

            if not valid_responses:
                logger.error("No valid responses to analyze")
                await Actor.push_data({
                    "type": "error",
                    "message": "No valid responses collected from platforms",
                })
                return

            analysis_key = get_analysis_api_key()

            if not analysis_key:
                logger.error("ANTHROPIC_API_KEY not configured")
                await Actor.push_data({
                    "type": "error",
                    "message": "ANTHROPIC_API_KEY environment variable not set",
                })
                return

            analyzer = BrandAnalyzer(analysis_key, logger)

            platform_responses = [
                {
                    "platform": resp["platform"],
                    "prompt_text": resp["prompt_text"],
                    "response": resp["response"],
                }
                for resp in valid_responses
            ]

            output = await analyzer.analyze_all_responses(
                my_brand=actor_input.my_brand,
                competitors=actor_input.competitors,
                category=actor_input.category,
                platform_responses=platform_responses,
            )

            if not output:
                logger.error("Analysis failed to generate output")
                await Actor.push_data({
                    "type": "error",
                    "message": "Analysis failed",
                })
                return

            completed_at = datetime.now(timezone.utc)
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            output["executionMetadata"] = {
                "startedAt": started_at.isoformat(),
                "completedAt": completed_at.isoformat(),
                "durationMs": duration_ms,
                "totalResponses": len(valid_responses),
                "platformsQueried": [p.value for p in actor_input.platforms],
            }

            await Actor.push_data(output)

            events_charged = len(valid_responses)
            if events_charged > 0:
                try:
                    await Actor.charge(event_name="prompt-analyzed", count=events_charged)
                except Exception:
                    pass

            logger.info("=" * 40)
            logger.info("RESULTS")
            logger.info("=" * 40)
            logger.info(f"Brand: {actor_input.my_brand}")
            logger.info(f"Analyzed: {events_charged} responses")
            logger.info(f"Duration: {duration_ms/1000:.1f}s")
            logger.info("=" * 40)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
