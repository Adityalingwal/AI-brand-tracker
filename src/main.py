"""AI Brand Tracker - Track brand visibility across AI platforms."""

import asyncio
import os
import traceback
from datetime import datetime, timezone
from typing import Optional
from apify import Actor
from dotenv import load_dotenv
from .config import ActorInput, Platform
from .utils import validate_input, sanitize_error_message
from .error_handling import ExecutionTracker
from .browser_clients import ChatGPTBrowserClient, PerplexityBrowserClient, GeminiBrowserClient
from .analyzer import BrandAnalyzer

load_dotenv()

def create_browser_client(platform: Platform, logger):
    """Create a browser client for the given platform."""
    if platform == Platform.CHATGPT:
        return ChatGPTBrowserClient(logger, None)
    elif platform == Platform.PERPLEXITY:
        return PerplexityBrowserClient(logger, None)
    elif platform == Platform.GEMINI:
        return GeminiBrowserClient(logger, None)
    return None


async def query_platform(platform: Platform, prompts: list[str], logger, execution_tracker: ExecutionTracker) -> list[dict]:
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
                    execution_tracker.add_success(f"{platform.value}:{prompt_id}", {})
                    responses.append({
                        "prompt_id": prompt_id,
                        "prompt_text": prompt_text,
                        "platform": platform.value,
                        "response": result.response,
                        "success": True,
                    })
                else:
                    execution_tracker.add_error("query_failed", result.error or "Unknown", context=prompt_id)
                    responses.append({
                        "prompt_id": prompt_id,
                        "prompt_text": prompt_text,
                        "platform": platform.value,
                        "response": "",
                        "success": False,
                        "error": result.error,
                    })
                    
            except Exception as e:
                _error_msg = sanitize_error_message(e)
                execution_tracker.add_error("query_exception", _error_msg, context=prompt_id)
                responses.append({
                    "prompt_id": prompt_id,
                    "prompt_text": prompt_text[:200],
                    "platform": platform.value,
                    "response": "",
                    "success": False,
                    "error": _error_msg,
                })
        
    except Exception as e:
        _error_msg = sanitize_error_message(e)
        logger.error(f"[{platform.value}] Failed: {_error_msg}")
        execution_tracker.add_error("platform_failed", _error_msg, context=platform.value)
    finally:
        try:
            await client.close()
        except Exception:
            pass
    
    return responses


def get_analysis_api_key() -> Optional[str]:
    """Get Anthropic API key from environment."""
    return os.environ.get("ANTHROPIC_API_KEY")


async def main():
    """Main entry point."""

    async with Actor:
        logger = Actor.log
        execution_tracker = ExecutionTracker()
        started_at = datetime.now(timezone.utc)

        logger.info("AI Brand Tracker - Starting")

        try:
            raw_input = await Actor.get_input() or {}
            actor_input = ActorInput.from_raw_input(raw_input)

            validation_errors = validate_input(actor_input)
            if validation_errors:
                await Actor.push_data({
                    "type": "error",
                    "message": "Input validation failed",
                    "errors": [e.to_dict() for e in validation_errors],
                })
                return

            logger.info(f"Category: {actor_input.category}")
            logger.info(f"Brand: {actor_input.my_brand}")
            logger.info(f"Platforms: {[p.value for p in actor_input.platforms]}")

            all_prompts = actor_input.prompts
            
            tasks = [
                query_platform(platform, all_prompts, logger, execution_tracker)
                for platform in actor_input.platforms
            ]
            
            try:
                platform_results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=480.0  # 8 minutes for all platforms
                )
            except asyncio.TimeoutError:
                execution_tracker.add_error("timeout", "Platform queries exceeded time limit", recoverable=False)
                platform_results = []

            all_responses = []
            for result in platform_results:
                if isinstance(result, list):
                    all_responses.extend(result)
                elif isinstance(result, Exception):
                    pass

            valid_responses = [r for r in all_responses if r.get("success") and r.get("response")]

            if not valid_responses:
                logger.error("No valid responses to analyze")
                await Actor.push_data({
                    "type": "error",
                    "message": "No valid responses collected from platforms",
                })
                return

            analysis_key = get_analysis_api_key()

            if not analysis_key:
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
            try:
                charge_result = await Actor.charge(event_name="brand-analysis", count=1)
                if charge_result.event_charge_limit_reached:
                    logger.warning("User spending limit reached")
            except Exception:
                pass

            logger.info("=" * 40)
            logger.info("RESULTS")
            logger.info("=" * 40)
            logger.info(f"Brand: {actor_input.my_brand}")
            logger.info(f"Analyzed: {len(valid_responses)} responses")
            logger.info(f"Duration: {duration_ms/1000:.1f}s")
            logger.info("=" * 40)
            
        except Exception as e:
            error_msg = str(e)
            if "ANTHROPIC_API_KEY" in error_msg or "api_key" in error_msg.lower():
                error_msg = "API configuration error"
            logger.error(f"Error: {error_msg}")
            tb = traceback.format_exc()
            if "ANTHROPIC_API_KEY" in tb or "api_key" in tb.lower():
                logger.error("Error details hidden for security")
            else:
                traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
