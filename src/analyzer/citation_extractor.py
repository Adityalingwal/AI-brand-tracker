"""Extract citations (URLs) from AI responses."""

import re
from typing import Any


class CitationExtractor:
    """Extract URLs/citations from AI responses."""

    # URL regex pattern
    URL_PATTERN = re.compile(
        r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s\)\]\}\"\'<>]*',
        re.IGNORECASE
    )

    def __init__(self, logger: Any):
        """
        Initialize citation extractor.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def extract(self, response_text: str) -> list[str]:
        """
        Extract URLs from response text.

        Args:
            response_text: The AI response to analyze

        Returns:
            List of unique URLs found
        """
        if not response_text:
            return []

        # Find all URLs
        urls = self.URL_PATTERN.findall(response_text)

        # Clean up URLs (remove trailing punctuation)
        cleaned_urls = []
        for url in urls:
            # Remove trailing punctuation that might have been captured
            url = url.rstrip('.,;:!?)')

            # Basic validation
            if self._is_valid_url(url):
                cleaned_urls.append(url)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in cleaned_urls:
            url_lower = url.lower()
            if url_lower not in seen:
                seen.add(url_lower)
                unique_urls.append(url)

        return unique_urls

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not a placeholder."""
        if not url:
            return False

        # Skip common placeholder/example URLs
        skip_patterns = [
            'example.com',
            'placeholder',
            'yoursite',
            'website.com',
            'domain.com',
            'localhost',
            '127.0.0.1',
        ]

        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False

        # Must have a valid domain structure
        if '.' not in url:
            return False

        return True
