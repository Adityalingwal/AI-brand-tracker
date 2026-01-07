"""Basic tests for AI Brand Tracker - for Apify daily health checks."""

import pytest
from src.config import ActorInput, Platform, APIKeys, BrandMention
from src.utils.validators import validate_input, InputValidationError
from src.analyzer.metrics_calculator import MetricsCalculator


class TestActorInput:
    """Test ActorInput parsing and validation."""

    def test_parse_raw_input_basic(self):
        """Test basic input parsing."""
        raw = {
            "category": "CRM software",
            "yourBrand": "Salesforce",
            "platforms": ["chatgpt"],
            "openaiApiKey": "sk-test-key",
        }
        
        result = ActorInput.from_raw_input(raw)
        
        assert result.category == "CRM software"
        assert result.your_brand == "Salesforce"
        assert Platform.CHATGPT in result.platforms
        assert result.api_keys.openai == "sk-test-key"

    def test_parse_raw_input_with_competitors(self):
        """Test parsing with competitors."""
        raw = {
            "category": "Email Marketing",
            "yourBrand": "Mailchimp",
            "competitors": ["SendGrid", "ConvertKit"],
            "platforms": ["gemini"],
            "googleApiKey": "test-key",
        }
        
        result = ActorInput.from_raw_input(raw)
        
        assert len(result.competitors) == 2
        assert "SendGrid" in result.competitors
        assert result.all_brands == ["Mailchimp", "SendGrid", "ConvertKit"]

    def test_parse_raw_input_multiple_platforms(self):
        """Test parsing with multiple platforms."""
        raw = {
            "category": "Project Management",
            "yourBrand": "Asana",
            "platforms": ["chatgpt", "claude", "gemini"],
            "openaiApiKey": "key1",
            "anthropicApiKey": "key2",
            "googleApiKey": "key3",
        }
        
        result = ActorInput.from_raw_input(raw)
        
        assert len(result.platforms) == 3
        assert Platform.CHATGPT in result.platforms
        assert Platform.CLAUDE in result.platforms
        assert Platform.GEMINI in result.platforms

    def test_default_prompt_count(self):
        """Test default prompt count."""
        raw = {
            "category": "Test",
            "yourBrand": "Test",
            "platforms": ["chatgpt"],
        }
        
        result = ActorInput.from_raw_input(raw)
        
        assert result.prompt_count == 5


class TestInputValidation:
    """Test input validation."""

    def test_valid_input(self):
        """Test that valid input passes validation."""
        actor_input = ActorInput(
            category="CRM software",
            your_brand="Salesforce",
            platforms=[Platform.CHATGPT],
            api_keys=APIKeys(openai="sk-test-key"),
        )
        
        errors = validate_input(actor_input)
        
        assert len(errors) == 0

    def test_missing_category(self):
        """Test validation fails for missing category."""
        actor_input = ActorInput(
            category="",
            your_brand="Salesforce",
            platforms=[Platform.CHATGPT],
            api_keys=APIKeys(openai="sk-test-key"),
        )
        
        errors = validate_input(actor_input)
        
        assert any(e.field == "category" for e in errors)

    def test_missing_api_key_for_platform(self):
        """Test validation fails when API key is missing for selected platform."""
        actor_input = ActorInput(
            category="CRM software",
            your_brand="Salesforce",
            platforms=[Platform.CHATGPT],
            api_keys=APIKeys(),  # No API keys
        )
        
        errors = validate_input(actor_input)
        
        assert any("openaiApiKey" in (e.field or "") for e in errors)

    def test_too_many_competitors(self):
        """Test validation fails for too many competitors."""
        actor_input = ActorInput(
            category="CRM software",
            your_brand="Salesforce",
            platforms=[Platform.CHATGPT],
            api_keys=APIKeys(openai="sk-test"),
            competitors=["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10", "c11"],
        )
        
        errors = validate_input(actor_input)
        
        assert any(e.field == "competitors" for e in errors)


class TestMetricsCalculator:
    """Test metrics calculations."""

    def test_visibility_score_calculation(self):
        """Test visibility score calculation."""
        calc = MetricsCalculator()
        
        # 8 out of 10 prompts mentioned = 80%
        score = calc.calculate_visibility_score(8, 10)
        
        assert score == 80.0

    def test_visibility_score_zero_prompts(self):
        """Test visibility score with zero prompts."""
        calc = MetricsCalculator()
        
        score = calc.calculate_visibility_score(0, 0)
        
        assert score == 0.0

    def test_citation_share_calculation(self):
        """Test citation share calculation."""
        calc = MetricsCalculator()
        
        # 25 out of 100 mentions = 25%
        share = calc.calculate_citation_share(25, 100)
        
        assert share == 25.0

    def test_determine_winner(self):
        """Test winner determination."""
        calc = MetricsCalculator()
        
        mentions = [
            BrandMention(brand="BrandA", count=3, rank=1, context="", is_recommended=True),
            BrandMention(brand="BrandB", count=5, rank=2, context="", is_recommended=False),
            BrandMention(brand="BrandC", count=2, rank=3, context="", is_recommended=False),
        ]
        
        winner = calc.determine_winner(mentions)
        
        assert winner == "BrandB"  # Highest count

    def test_determine_winner_tie_by_rank(self):
        """Test winner determination when counts are tied."""
        calc = MetricsCalculator()
        
        mentions = [
            BrandMention(brand="BrandA", count=3, rank=2, context="", is_recommended=True),
            BrandMention(brand="BrandB", count=3, rank=1, context="", is_recommended=False),
        ]
        
        winner = calc.determine_winner(mentions)
        
        assert winner == "BrandB"  # Same count, lower rank wins

    def test_determine_loser(self):
        """Test loser determination."""
        calc = MetricsCalculator()
        
        mentions = [
            BrandMention(brand="BrandA", count=5, rank=1, context="", is_recommended=True),
            BrandMention(brand="BrandB", count=2, rank=2, context="", is_recommended=False),
            BrandMention(brand="BrandC", count=1, rank=3, context="", is_recommended=False),
        ]
        
        loser = calc.determine_loser(mentions)
        
        assert loser == "BrandC"  # Lowest count


class TestAPIKeys:
    """Test API key handling."""

    def test_get_key_for_platform(self):
        """Test getting key for specific platform."""
        keys = APIKeys(
            openai="openai-key",
            anthropic="anthropic-key",
        )
        
        assert keys.get_key_for_platform(Platform.CHATGPT) == "openai-key"
        assert keys.get_key_for_platform(Platform.CLAUDE) == "anthropic-key"
        assert keys.get_key_for_platform(Platform.GEMINI) is None

    def test_get_first_available_key(self):
        """Test getting first available key."""
        keys = APIKeys(anthropic="only-this-key")
        
        key, platform = keys.get_first_available_key()
        
        assert key == "only-this-key"
        assert platform == Platform.CLAUDE

    def test_get_first_available_key_priority(self):
        """Test that Gemini is prioritized as first available."""
        keys = APIKeys(
            openai="openai-key",
            google="google-key",
        )
        
        key, platform = keys.get_first_available_key()
        
        # Gemini should be first priority
        assert key == "google-key"
        assert platform == Platform.GEMINI
