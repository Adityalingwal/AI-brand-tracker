"""AI Brand Visibility - Track brand visibility across AI platforms."""

import asyncio
import traceback
from datetime import datetime, timezone
from typing import Optional
from apify import Actor
from dotenv import load_dotenv
from openai import AsyncOpenAI
from .config import ActorInput, Platform
from .utils import validate_input, sanitize_error_message
from .error_handling import ExecutionTracker
from .api_clients import (
    ChatGPTApiClient,
    create_openrouter_client,
    get_openrouter_api_key,
)
from .browser_clients import GeminiBrowserClient
from .analyzer import BrandAnalyzer

load_dotenv()

def create_platform_client(
    platform: Platform,
    logger,
    openrouter_api_key: Optional[str] = None,
    openrouter_client: Optional[AsyncOpenAI] = None,
):
    """Create a platform client for the given platform."""
    if platform == Platform.CHATGPT:
        return ChatGPTApiClient(
            logger,
            api_key=openrouter_api_key,
            client=openrouter_client,
        )
    elif platform == Platform.GEMINI:
        return GeminiBrowserClient(logger)
    return None


async def query_platform(
    platform: Platform,
    prompts: list[str],
    logger,
    execution_tracker: ExecutionTracker,
    openrouter_api_key: Optional[str] = None,
    openrouter_client: Optional[AsyncOpenAI] = None,
) -> list[dict]:
    """Query a single platform with all prompts."""
    responses = []
    client = create_platform_client(
        platform,
        logger,
        openrouter_api_key=openrouter_api_key,
        openrouter_client=openrouter_client,
    )
    
    if not client:
        logger.warning(f"[{platform.value}] No client available - skipping")
        return responses
    
    uses_browser = getattr(client, "uses_browser", True)
    if uses_browser:
        logger.info(f"[{platform.value}] Initializing browser...")
    
    try:
        await client.initialize()
        if uses_browser:
            logger.info(f"[{platform.value}] Browser ready - querying {len(prompts)} prompt(s)")
        else:
            logger.info(f"[{platform.value}] Querying {len(prompts)} prompt(s)")
        
        for i, prompt_text in enumerate(prompts):
            prompt_id = f"{platform.value}_{i:03d}"
            logger.info(f"[{platform.value}] Querying prompt {i+1}/{len(prompts)}...")
            
            try:
                result = await client.query_with_retry(prompt_text, max_retries=2)
                
                if result.success:
                    execution_tracker.add_success(f"{platform.value}:{prompt_id}", {})
                    logger.info(f"[{platform.value}] ✓ Prompt {i+1} succeeded ({len(result.response)} chars)")
                    responses.append({
                        "prompt_id": prompt_id,
                        "prompt_text": prompt_text,
                        "platform": platform.value,
                        "response": result.response,
                        "success": True,
                    })
                else:
                    execution_tracker.add_error("query_failed", result.error or "Unknown", context=prompt_id)
                    logger.warning(f"[{platform.value}] ✗ Prompt {i+1} failed: {result.error}")
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
                logger.error(f"[{platform.value}] ✗ Prompt {i+1} exception: {_error_msg}")
                responses.append({
                    "prompt_id": prompt_id,
                    "prompt_text": prompt_text[:200],
                    "platform": platform.value,
                    "response": "",
                    "success": False,
                    "error": _error_msg,
                })
        
        success_count = sum(1 for r in responses if r.get("success"))
        logger.info(f"[{platform.value}] Completed: {success_count}/{len(prompts)} prompts succeeded")
        
    except Exception as e:
        _error_msg = sanitize_error_message(e)
        failure_type = "Browser initialization" if uses_browser else "Platform query initialization"
        logger.error(f"[{platform.value}] ✗ {failure_type} failed: {_error_msg}")
        execution_tracker.add_error("platform_failed", _error_msg, context=platform.value)
    finally:
        try:
            await client.close()
        except Exception:
            pass
    
    return responses

async def main():
    """Main entry point."""

    async with Actor:
        logger = Actor.log
        execution_tracker = ExecutionTracker()
        started_at = datetime.now(timezone.utc)
        openrouter_client: Optional[AsyncOpenAI] = None

        logger.info("AI Brand Visibility - Starting")

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
            openrouter_api_key = get_openrouter_api_key()
            openrouter_client = create_openrouter_client(openrouter_api_key)

            if not openrouter_api_key or not openrouter_client:
                await Actor.push_data({
                    "type": "error",
                    "message": "OPENROUTER_API_KEY environment variable not set",
                })
                return
            
            tasks = [
                query_platform(
                    platform,
                    all_prompts,
                    logger,
                    execution_tracker,
                    openrouter_api_key=openrouter_api_key,
                    openrouter_client=openrouter_client,
                )
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

            analyzer = BrandAnalyzer(
                openrouter_api_key,
                logger,
                client=openrouter_client,
            )

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
            error_msg = sanitize_error_message(e)
            logger.error(f"Error: {error_msg}")
            tb = traceback.format_exc()
            if (
                "OPENROUTER_API_KEY" in tb
                or "api_key" in tb.lower()
                or "sk-or-" in tb.lower()
            ):
                logger.error("Error details hidden for security")
            else:
                traceback.print_exc()
        finally:
            if openrouter_client:
                try:
                    await openrouter_client.close()
                except Exception:
                    pass


if __name__ == "__main__":
    asyncio.run(main())
