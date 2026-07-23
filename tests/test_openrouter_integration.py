"""Tests for the OpenRouter-backed query and analysis flow."""

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.analyzer.analyzer import BrandAnalyzer, build_analysis_response_format
from src.analyzer.prompts.analysis_prompt import build_analysis_prompt
from src.api_clients.chatgpt_client import ChatGPTApiClient
from src.api_clients.openrouter_client import (
    OPENROUTER_BASE_URL,
    create_openrouter_client,
    get_openrouter_api_key,
)
from src.config import ActorInput
from src.utils.security import sanitize_error_message
from src.utils.validators import validate_input


class FakeLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(("info", message))

    def warning(self, message):
        self.messages.append(("warning", message))

    def error(self, message):
        self.messages.append(("error", message))


class FakeCompletions:
    def __init__(self, response_text):
        self.response_text = response_text
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.response_text),
                ),
            ],
        )


class FakeOpenRouterClient:
    def __init__(self, response_text):
        self.completions = FakeCompletions(response_text)
        self.chat = SimpleNamespace(completions=self.completions)


class OpenRouterConfigurationTests(unittest.IsolatedAsyncioTestCase):
    def test_api_key_is_read_only_from_openrouter_environment_variable(self):
        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "test-openrouter-key"},
            clear=True,
        ):
            self.assertEqual(get_openrouter_api_key(), "test-openrouter-key")

        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(get_openrouter_api_key())
            self.assertIsNone(create_openrouter_client())

    async def test_client_points_to_openrouter(self):
        client = create_openrouter_client("test-openrouter-key")
        self.assertIsNotNone(client)
        self.assertEqual(str(client.base_url), f"{OPENROUTER_BASE_URL}/")
        self.assertEqual(
            client.default_headers["X-OpenRouter-Title"],
            "AI Brand Visibility",
        )
        await client.close()

    async def test_chatgpt_query_uses_openrouter_model_slug(self):
        fake_client = FakeOpenRouterClient("Brand A is a strong option.")
        client = ChatGPTApiClient(
            FakeLogger(),
            api_key="test-openrouter-key",
            client=fake_client,
        )

        result = await client.query("What are the best CRM tools?")

        self.assertTrue(result.success)
        call = fake_client.completions.calls[0]
        self.assertEqual(call["model"], "openai/gpt-4.1-nano")
        self.assertEqual(call["messages"][-1]["role"], "user")


class StructuredAnalysisTests(unittest.IsolatedAsyncioTestCase):
    def test_response_schema_is_strict_and_run_specific(self):
        response_format = build_analysis_response_format(
            competitors=["Brand B"],
            platforms=["chatgpt", "gemini"],
        )
        schema = response_format["json_schema"]["schema"]

        self.assertTrue(response_format["json_schema"]["strict"])
        self.assertFalse(schema["additionalProperties"])
        competitor_properties = schema[
            "properties"
        ]["competitorBrandPerformance"]["properties"]
        self.assertEqual(list(competitor_properties), ["Brand B"])
        platform_schema = schema[
            "properties"
        ]["myBrandPerformance"]["properties"]["platformPerformance"]
        self.assertEqual(
            platform_schema["required"],
            ["chatgpt", "gemini"],
        )

    async def test_analyzer_requests_private_strict_structured_output(self):
        expected_output = {
            "summary": {
                "category": "wrong",
                "myBrand": "wrong",
                "competitors": [],
            },
            "myBrandPerformance": {
                "brand": "wrong",
                "platformPerformance": {
                    "gemini": {
                        "summary": "Brand A leads.",
                        "promptsMentionSummary": "No major gap.",
                    },
                },
            },
            "competitorBrandPerformance": {
                "Brand B": {
                    "platformPerformance": {
                        "gemini": {
                            "summary": "Brand B trails.",
                            "promptsMentionSummary": "Missing from one query.",
                        },
                    },
                },
            },
        }
        fake_client = FakeOpenRouterClient(json.dumps(expected_output))
        analyzer = BrandAnalyzer(
            "test-openrouter-key",
            FakeLogger(),
            client=fake_client,
        )

        output = await analyzer.analyze_all_responses(
            my_brand="Brand A",
            competitors=["Brand B"],
            category="CRM",
            platform_responses=[
                {
                    "platform": "gemini",
                    "prompt_text": "Best CRM?",
                    "response": "Brand A and Brand B.",
                },
            ],
        )

        self.assertIsNotNone(output)
        self.assertEqual(output["summary"]["category"], "CRM")
        self.assertEqual(output["summary"]["myBrand"], "Brand A")
        self.assertEqual(output["summary"]["competitors"], ["Brand B"])
        self.assertEqual(output["myBrandPerformance"]["brand"], "Brand A")

        call = fake_client.completions.calls[0]
        self.assertEqual(call["model"], "openai/gpt-4.1-mini")
        self.assertEqual(call["response_format"]["type"], "json_schema")
        self.assertEqual(
            call["extra_body"]["provider"],
            {
                "require_parameters": True,
                "data_collection": "deny",
            },
        )
        self.assertEqual(call["messages"][0]["role"], "system")
        self.assertIn("untrusted", call["messages"][0]["content"])

    def test_prompt_contains_only_one_competitor_performance_example(self):
        prompt = build_analysis_prompt(
            "Brand A",
            ["Brand B"],
            [
                {
                    "platform": "gemini",
                    "prompt_text": "Best CRM?",
                    "response": "Brand A.",
                },
            ],
            "CRM",
        )
        self.assertEqual(prompt.count('"competitorBrandPerformance"'), 1)


class SecurityTests(unittest.TestCase):
    def test_openrouter_secret_errors_are_redacted(self):
        error = RuntimeError(
            "Authorization: Bearer sk-or-sensitive-value"
        )
        sanitized = sanitize_error_message(error)

        self.assertEqual(sanitized, "Internal error occurred")
        self.assertNotIn("sk-or-", sanitized)


class InputValidationTests(unittest.TestCase):
    def test_api_input_over_limits_is_rejected_instead_of_silently_truncated(self):
        actor_input = ActorInput.from_raw_input({
            "category": "CRM",
            "myBrand": "Brand A",
            "competitors": ["1", "2", "3", "4", "5", "6"],
            "platforms": ["chatgpt"],
            "prompts": ["1", "2", "3", "4"],
        })

        errors = validate_input(actor_input)
        self.assertEqual(len(actor_input.competitors), 6)
        self.assertEqual(len(actor_input.prompts), 4)
        self.assertEqual(
            {error.field for error in errors},
            {"competitors", "prompts"},
        )


if __name__ == "__main__":
    unittest.main()
