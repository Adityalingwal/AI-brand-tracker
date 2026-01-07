"""Progress tracking utilities."""

import time
from typing import Optional, Any
from dataclasses import dataclass, field


@dataclass
class StepInfo:
    """Information about a processing step."""
    name: str
    description: str
    started_at: float
    completed_at: Optional[float] = None
    items: int = 0
    details: Optional[str] = None
    success: bool = True


class ProgressTracker:
    """Track progress through processing steps."""

    def __init__(self, logger: Any):
        self.logger = logger
        self.steps: list[StepInfo] = []
        self.current_step: Optional[StepInfo] = None
        self.start_time: float = time.time()

    def start_step(self, name: str, description: str) -> None:
        """Start a new processing step."""
        self.current_step = StepInfo(
            name=name,
            description=description,
            started_at=time.time()
        )

        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info(f"  STEP: {name}")
        self.logger.info(f"  {description}")
        self.logger.info("=" * 60)

    def complete_step(
        self,
        name: str,
        items: int = 0,
        details: Optional[str] = None,
        success: bool = True
    ) -> None:
        """Complete the current step."""
        if self.current_step and self.current_step.name == name:
            self.current_step.completed_at = time.time()
            self.current_step.items = items
            self.current_step.details = details
            self.current_step.success = success
            self.steps.append(self.current_step)

            duration = self.current_step.completed_at - self.current_step.started_at
            status = "OK" if success else "FAILED"

            self.logger.info("")
            if items > 0:
                self.logger.info(f"  {status}: {name} - {items} items ({duration:.1f}s)")
            else:
                self.logger.info(f"  {status}: {name} ({duration:.1f}s)")

            if details:
                self.logger.info(f"  Details: {details}")

            self.current_step = None

    def log_progress(self, current: int, total: int, message: str) -> None:
        """Log progress within a step."""
        percent = (current / total * 100) if total > 0 else 0
        self.logger.info(f"  [{current}/{total}] ({percent:.0f}%) {message}")

    def log_summary(self) -> None:
        """Log final summary of all steps."""
        total_duration = time.time() - self.start_time

        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("  EXECUTION SUMMARY")
        self.logger.info("=" * 60)

        for step in self.steps:
            duration = (step.completed_at or time.time()) - step.started_at
            status = "OK" if step.success else "FAILED"

            if step.items > 0:
                self.logger.info(f"  [{status}] {step.name}: {step.items} items ({duration:.1f}s)")
            else:
                self.logger.info(f"  [{status}] {step.name} ({duration:.1f}s)")

        self.logger.info("-" * 60)
        self.logger.info(f"  Total Duration: {total_duration:.1f}s")
        self.logger.info("=" * 60)

    def get_summary(self) -> dict:
        """Get summary as dictionary."""
        return {
            "steps": [
                {
                    "name": s.name,
                    "items": s.items,
                    "duration_ms": int((s.completed_at or time.time()) - s.started_at) * 1000,
                    "success": s.success,
                }
                for s in self.steps
            ],
            "total_duration_ms": int((time.time() - self.start_time) * 1000),
        }
