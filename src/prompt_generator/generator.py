"""Template-based prompt generator for brand visibility analysis."""

from typing import Any


class PromptGenerator:
    """Generate prompts for brand visibility analysis using pre-built templates."""

    TEMPLATES = [
        "What are the best {category} available today?",
        "Compare the top rated {category} options",
        "What is the most affordable {category}?",
        "Best {category} for small businesses and startups",
        "Which {category} is most recommended by users and experts?",
    ]

    def __init__(self, logger: Any):
        """
        Initialize prompt generator.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def generate(self, category: str, count: int) -> list[str]:
        """
        Generate prompts for the given category using templates.

        Args:
            category: Industry/niche to generate prompts for
            count: Number of prompts to generate (1-5)

        Returns:
            List of generated prompts
        """
        count = min(count, len(self.TEMPLATES))
        count = max(count, 1)

        prompts = []
        for i in range(count):
            prompt = self.TEMPLATES[i].format(category=category)
            prompts.append(prompt)

        self.logger.info(f"  Generated {len(prompts)} prompts from templates")
        return prompts
