"""Error tracking for the actor."""

from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ErrorRecord:
    """Record of an error that occurred."""
    error_type: str
    message: str
    context: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    recoverable: bool = True


@dataclass
class SuccessRecord:
    """Record of a successful operation."""
    operation: str
    details: Optional[dict] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ErrorTracker:
    """Track errors and successes during actor execution."""

    def __init__(self):
        self.errors: list[ErrorRecord] = []
        self.successes: list[SuccessRecord] = []
        self.warnings: list[str] = []

    def add_error(
        self,
        error_type: str,
        message: str,
        context: Optional[str] = None,
        recoverable: bool = True
    ) -> None:
        """Add an error record."""
        self.errors.append(ErrorRecord(
            error_type=error_type,
            message=message,
            context=context,
            recoverable=recoverable,
        ))

    def add_success(self, operation: str, details: Optional[dict] = None) -> None:
        """Add a success record."""
        self.successes.append(SuccessRecord(
            operation=operation,
            details=details,
        ))

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def get_error_count(self) -> int:
        """Get total number of errors."""
        return len(self.errors)

    def get_success_count(self) -> int:
        """Get total number of successes."""
        return len(self.successes)

    def has_fatal_errors(self) -> bool:
        """Check if there are any non-recoverable errors."""
        return any(not e.recoverable for e in self.errors)

    def get_summary(self) -> dict:
        """Get summary of all tracked events."""
        return {
            "successes": self.get_success_count(),
            "errors": self.get_error_count(),
            "warnings": len(self.warnings),
            "fatal_errors": sum(1 for e in self.errors if not e.recoverable),
        }

    def print_summary(self, logger: Any) -> None:
        """Print summary to logger."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("  ERROR TRACKING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  Successes: {self.get_success_count()}")
        logger.info(f"  Errors: {self.get_error_count()}")
        logger.info(f"  Warnings: {len(self.warnings)}")

        if self.errors:
            logger.info("")
            logger.info("  Errors:")
            for error in self.errors[-5:]:  # Show last 5 errors
                logger.info(f"    - [{error.error_type}] {error.message}")
            if len(self.errors) > 5:
                logger.info(f"    ... and {len(self.errors) - 5} more")

        if self.warnings:
            logger.info("")
            logger.info("  Warnings:")
            for warning in self.warnings[-3:]:  # Show last 3 warnings
                logger.info(f"    - {warning}")
            if len(self.warnings) > 3:
                logger.info(f"    ... and {len(self.warnings) - 3} more")

        logger.info("=" * 60)
