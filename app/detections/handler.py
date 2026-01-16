"""
Detection Handler
=================
High-level interface for running detections in the scraper.

This module provides a simple API for the scraper to use:
- handle_detections(page, url) - Detect and solve all challenges
- Returns a DetectionResult with status

Usage in scraper.py:
    from app.detections.handler import DetectionHandler

    handler = DetectionHandler(config)
    result = handler.handle_detections(page, url)
    if result.blocked:
        # Handle blocked state
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from playwright.sync_api import Page

from .registry import DetectionRegistry
from .base import DetectionResult, DetectionCategory

logger = logging.getLogger("scraper.detections.handler")


@dataclass
class HandlerResult:
    """Result of detection handling."""
    detected_any: bool = False
    all_solved: bool = True
    blocked: bool = False
    detections: List[str] = field(default_factory=list)
    solve_results: Dict[str, bool] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)


class DetectionHandler:
    """
    High-level detection handler for the scraper.

    Provides a simple interface to:
    1. Run all detections
    2. Attempt to solve detected challenges
    3. Report results

    Example:
        handler = DetectionHandler(config)
        result = handler.handle_detections(page, url)

        if result.blocked:
            logger.warning(f"Blocked by: {result.detections}")
        elif result.detected_any:
            logger.info(f"Solved: {result.solve_results}")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the detection handler.

        Args:
            config: Configuration dict (passed to DetectionRegistry)
        """
        self.config = config or {}
        self.registry = DetectionRegistry(config=self.config)

    def handle_detections(
        self,
        page: Page,
        url: str,
        max_solve_attempts: int = 2
    ) -> HandlerResult:
        """
        Run all detections and attempt to solve any found.

        Args:
            page: Playwright Page object
            url: The URL being scraped
            max_solve_attempts: Max times to retry solving

        Returns:
            HandlerResult with detection and solving status
        """
        result = HandlerResult()

        # Run all detections
        detections = self.registry.detect_all(page, url)

        if not detections:
            logger.debug("No bot detection systems found")
            return result

        result.detected_any = True
        result.detections = [d.detection_type for d in detections]

        logger.info(f"Detected {len(detections)} challenge(s): {result.detections}")

        # Attempt to solve each detection
        for detection in detections:
            name = detection.detection_type
            solved = False

            for attempt in range(max_solve_attempts):
                logger.debug(f"Solving {name} (attempt {attempt + 1}/{max_solve_attempts})")

                solved = self.registry.solve(name, page, url, detection)
                result.solve_results[name] = solved

                if solved:
                    logger.info(f"Solved: {name}")
                    break

            if not solved:
                result.all_solved = False
                logger.warning(f"Failed to solve: {name}")

        # Check if we're still blocked
        result.blocked = not result.all_solved

        # Add details
        result.details = {
            "detections_found": len(detections),
            "detections_solved": sum(1 for v in result.solve_results.values() if v),
            "detection_names": result.detections,
        }

        return result

    def handle_by_category(
        self,
        page: Page,
        url: str,
        category: DetectionCategory
    ) -> HandlerResult:
        """
        Run detections for a specific category only.

        Useful for running CAPTCHA detection separately from challenges.

        Args:
            page: Playwright Page object
            url: The URL being scraped
            category: The detection category to run

        Returns:
            HandlerResult with detection and solving status
        """
        result = HandlerResult()

        detections = self.registry.detect_by_category(page, url, category)

        if not detections:
            return result

        result.detected_any = True
        result.detections = [d.detection_type for d in detections]

        # Solve
        for detection in detections:
            name = detection.detection_type
            solved = self.registry.solve(name, page, url, detection)
            result.solve_results[name] = solved

            if not solved:
                result.all_solved = False

        result.blocked = not result.all_solved
        return result

    def quick_check(self, page: Page, url: str) -> bool:
        """
        Quick check if any detection is present (no solving).

        Args:
            page: Playwright Page object
            url: The URL being scraped

        Returns:
            True if any detection found, False otherwise
        """
        detections = self.registry.detect_all(page, url, stop_on_first=True)
        return len(detections) > 0

    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return self.registry.get_stats()


# === BACKWARD COMPATIBILITY ===
# These functions maintain compatibility with the old Cloudflare module

def is_cloudflare_challenge(page: Page) -> bool:
    """
    Backward compatible function for Cloudflare detection.

    Deprecated: Use DetectionHandler instead.
    """
    registry = DetectionRegistry()
    cloudflare = registry.get("cloudflare")
    if cloudflare:
        result = cloudflare.detect(page, page.url)
        return result.detected
    return False


def wait_for_cloudflare(page: Page, max_wait: int = 45) -> bool:
    """
    Backward compatible function for Cloudflare solving.

    Deprecated: Use DetectionHandler instead.
    """
    registry = DetectionRegistry()
    cloudflare = registry.get("cloudflare")
    if cloudflare:
        result = cloudflare.detect(page, page.url)
        if result.detected:
            cloudflare.solve_timeout = max_wait
            return cloudflare.solve(page, page.url, result)
    return True  # No Cloudflare detected = success
