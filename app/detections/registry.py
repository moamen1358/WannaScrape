"""
Detection Registry
==================
Auto-discovers and manages all detection plugins.

The registry:
1. Automatically imports all .py files in app/detections/
2. Finds all BaseDetection subclasses
3. Instantiates and registers them
4. Provides methods to run detections by priority
"""

import importlib
import importlib.util
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Type, Any

from playwright.sync_api import Page

from .base import BaseDetection, DetectionResult, DetectionCategory

logger = logging.getLogger("scraper.detections.registry")


class DetectionRegistry:
    """
    Central registry for all detection plugins.

    Auto-discovers detection plugins from app/detections/ directory.
    Plugins are loaded once and cached for performance.

    Usage:
        registry = DetectionRegistry()

        # Detect all
        results = registry.detect_all(page, url)

        # Detect specific category
        results = registry.detect_by_category(page, url, DetectionCategory.CAPTCHA)

        # Solve a detection
        solved = registry.solve(result.detection_type, page, url, result)
    """

    _instance: Optional["DetectionRegistry"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        """Singleton pattern - only one registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None, auto_discover: bool = True):
        """
        Initialize the registry.

        Args:
            config: Configuration dict passed to all detections
            auto_discover: Whether to auto-discover plugins on init
        """
        # Only initialize once (singleton)
        if DetectionRegistry._initialized:
            return

        self.config = config or {}
        self._detections: Dict[str, BaseDetection] = {}
        self._detection_classes: Dict[str, Type[BaseDetection]] = {}

        if auto_discover:
            self._discover_plugins()

        DetectionRegistry._initialized = True
        logger.info(f"DetectionRegistry initialized with {len(self._detections)} plugins")

    def _discover_plugins(self):
        """
        Auto-discover all detection plugins in the detections directory.

        Imports all .py files (except __init__.py, base.py, registry.py)
        and registers any BaseDetection subclasses found.
        """
        # Get the detections directory
        detections_dir = Path(__file__).parent

        # Files to skip
        skip_files = {"__init__.py", "base.py", "registry.py"}

        # Find all Python files
        for file_path in detections_dir.glob("*.py"):
            if file_path.name in skip_files:
                continue

            try:
                self._import_plugin(file_path)
            except Exception as e:
                logger.warning(f"Failed to load plugin {file_path.name}: {e}")

        # Sort detections by priority
        self._sort_by_priority()

    def _import_plugin(self, file_path: Path):
        """Import a single plugin file and register its detections."""
        module_name = f"app.detections.{file_path.stem}"

        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all BaseDetection subclasses in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # Check if it's a class that inherits from BaseDetection
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseDetection)
                    and attr is not BaseDetection
                    and attr.name != "base"  # Skip base class
                ):
                    self._register_class(attr)

        except Exception as e:
            logger.error(f"Error importing {file_path}: {e}")
            raise

    def _register_class(self, detection_class: Type[BaseDetection]):
        """Register a detection class."""
        name = detection_class.name

        if name in self._detection_classes:
            logger.warning(f"Detection '{name}' already registered, skipping duplicate")
            return

        # Store the class
        self._detection_classes[name] = detection_class

        # Instantiate with config
        # Merge detection-specific config with global config (for shared settings like captcha API)
        try:
            detection_config = self.config.get("detections", {}).get(name, {})
            # Merge global captcha config for CAPTCHA detections
            merged_config = {**self.config, **detection_config}
            instance = detection_class(config=merged_config)

            if instance.enabled:
                self._detections[name] = instance
                logger.debug(f"Registered detection: {name} (priority: {instance.priority})")
            else:
                logger.debug(f"Skipped disabled detection: {name}")

        except Exception as e:
            logger.error(f"Failed to instantiate detection '{name}': {e}")

    def _sort_by_priority(self):
        """Sort detections by priority (lower first)."""
        sorted_items = sorted(
            self._detections.items(),
            key=lambda x: x[1].priority
        )
        self._detections = dict(sorted_items)

    # === PUBLIC API ===

    def register(self, detection_class: Type[BaseDetection]):
        """
        Manually register a detection class.

        Useful for testing or dynamic registration.

        Args:
            detection_class: A BaseDetection subclass
        """
        self._register_class(detection_class)
        self._sort_by_priority()

    def unregister(self, name: str):
        """Unregister a detection by name."""
        self._detections.pop(name, None)
        self._detection_classes.pop(name, None)

    def get(self, name: str) -> Optional[BaseDetection]:
        """Get a detection instance by name."""
        return self._detections.get(name)

    def list_all(self) -> List[str]:
        """List all registered detection names (sorted by priority)."""
        return list(self._detections.keys())

    def list_by_category(self, category: DetectionCategory) -> List[str]:
        """List detections in a specific category."""
        return [
            name for name, det in self._detections.items()
            if det.category == category
        ]

    def detect_all(
        self,
        page: Page,
        url: str,
        stop_on_first: bool = False
    ) -> List[DetectionResult]:
        """
        Run all detections on a page.

        Args:
            page: Playwright Page object
            url: The URL being scraped
            stop_on_first: Stop after first detection found

        Returns:
            List of DetectionResult objects (only detected=True results)
        """
        results = []

        for name, detection in self._detections.items():
            try:
                result = detection.detect(page, url)
                if result.detected:
                    results.append(result)
                    logger.info(f"Detected: {name} (confidence: {result.confidence:.2f})")

                    if stop_on_first:
                        break
            except Exception as e:
                logger.error(f"Detection '{name}' failed: {e}")

        return results

    def detect_by_category(
        self,
        page: Page,
        url: str,
        category: DetectionCategory
    ) -> List[DetectionResult]:
        """Run detections only in a specific category."""
        results = []

        for name, detection in self._detections.items():
            if detection.category != category:
                continue

            try:
                result = detection.detect(page, url)
                if result.detected:
                    results.append(result)
            except Exception as e:
                logger.error(f"Detection '{name}' failed: {e}")

        return results

    def solve(
        self,
        detection_name: str,
        page: Page,
        url: str,
        detection_result: Optional[DetectionResult] = None
    ) -> bool:
        """
        Solve a specific detection.

        Args:
            detection_name: Name of the detection to solve
            page: Playwright Page object
            url: The URL being scraped
            detection_result: Result from detect() (optional, will detect if not provided)

        Returns:
            True if solved, False otherwise
        """
        detection = self._detections.get(detection_name)
        if not detection:
            logger.warning(f"Detection '{detection_name}' not found")
            return False

        # Run detection first if result not provided
        if detection_result is None:
            detection_result = detection.detect(page, url)
            if not detection_result.detected:
                return True  # Nothing to solve

        try:
            return detection.solve(page, url, detection_result)
        except Exception as e:
            logger.error(f"Solve failed for '{detection_name}': {e}")
            return False

    def solve_all(
        self,
        page: Page,
        url: str,
        results: Optional[List[DetectionResult]] = None
    ) -> Dict[str, bool]:
        """
        Attempt to solve all detected challenges.

        Args:
            page: Playwright Page object
            url: The URL being scraped
            results: List of DetectionResults to solve (will detect_all if not provided)

        Returns:
            Dict mapping detection_name to solved status
        """
        if results is None:
            results = self.detect_all(page, url)

        solve_results = {}

        for result in results:
            name = result.detection_type
            solved = self.solve(name, page, url, result)
            solve_results[name] = solved

        return solve_results

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        categories = {}
        for det in self._detections.values():
            cat = det.category.value
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_detections": len(self._detections),
            "by_category": categories,
            "detections": [
                {
                    "name": det.name,
                    "priority": det.priority,
                    "category": det.category.value,
                    "enabled": det.enabled,
                    "requires_api": det.requires_api
                }
                for det in self._detections.values()
            ]
        }

    @classmethod
    def reset(cls):
        """Reset the singleton (useful for testing)."""
        cls._instance = None
        cls._initialized = False
