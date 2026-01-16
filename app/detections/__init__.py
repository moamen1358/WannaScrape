"""
Bot Detection Plugin System
============================
Auto-discovering plugin architecture for bot detection systems.

Usage:
    from app.detections import DetectionRegistry

    # Get all registered detections
    registry = DetectionRegistry()

    # Run all detections on a page
    results = registry.detect_all(page, url)

    # Solve detected challenges
    for result in results:
        if result.detected:
            solved = registry.solve(result.detection_type, page, url)

Adding new detections:
    1. Create app/detections/yourdetection.py
    2. Inherit from BaseDetection
    3. Implement detect() and solve() methods
    4. That's it! Auto-registered on import.
"""

from .base import BaseDetection, DetectionResult
from .registry import DetectionRegistry

__all__ = ["BaseDetection", "DetectionResult", "DetectionRegistry"]
