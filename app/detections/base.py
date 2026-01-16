"""
Base Detection Class
====================
Abstract base class for all bot detection plugins.

Every detection plugin must inherit from this class and implement:
- detect(): Check if this detection system is present
- solve(): Attempt to bypass/solve the detection
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
import logging

from playwright.sync_api import Page

logger = logging.getLogger("scraper.detections")


class DetectionCategory(Enum):
    """Categories of bot detection systems."""
    CHALLENGE = "challenge"      # Cloudflare, PerimeterX challenges
    CAPTCHA = "captcha"          # reCAPTCHA, hCaptcha, etc.
    FINGERPRINT = "fingerprint"  # Canvas, WebGL fingerprinting
    BEHAVIORAL = "behavioral"    # Mouse/keyboard analysis
    RATE_LIMIT = "rate_limit"    # Request frequency limits


class SolveMethod(Enum):
    """How the detection can be solved."""
    WAIT = "wait"                # Just wait for it to pass
    API = "api"                  # Requires external API (2captcha, etc.)
    BEHAVIORAL = "behavioral"   # Simulate human behavior
    BYPASS = "bypass"           # Technical bypass/spoof
    NONE = "none"               # Cannot be solved automatically


@dataclass
class DetectionResult:
    """Result of a detection check."""
    detected: bool
    detection_type: str
    confidence: float = 1.0  # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    solve_method: SolveMethod = SolveMethod.NONE

    def __bool__(self) -> bool:
        return self.detected


class BaseDetection(ABC):
    """
    Abstract base class for bot detection plugins.

    Subclasses are automatically registered when defined.
    Just create a new file in app/detections/ and inherit from this class.

    Example:
        class DataDomeDetection(BaseDetection):
            name = "datadome"
            priority = 50
            category = DetectionCategory.CHALLENGE

            def detect(self, page, url):
                # Your detection logic
                ...

            def solve(self, page, url, detection_result):
                # Your solving logic
                ...
    """

    # === REQUIRED CLASS ATTRIBUTES (override in subclass) ===
    name: str = "base"  # Unique identifier for this detection
    priority: int = 100  # Lower = runs first (10-90 recommended)
    category: DetectionCategory = DetectionCategory.CHALLENGE

    # === OPTIONAL CLASS ATTRIBUTES ===
    description: str = ""  # Human-readable description
    enabled: bool = True   # Can be disabled without removing
    requires_api: bool = False  # Needs external API key
    solve_timeout: int = 60  # Max seconds to attempt solving

    # === SELECTORS (override in subclass) ===
    selectors: List[str] = []  # CSS selectors that indicate this detection
    title_indicators: List[str] = []  # Page title patterns
    content_indicators: List[str] = []  # Page content patterns

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize detection with optional config.

        Args:
            config: Configuration dict (from config.json or passed directly)
        """
        self.config = config or {}
        self._setup()

    def _setup(self):  # noqa: B027
        """
        Override this for custom initialization.
        Called after __init__ with self.config available.
        
        This is intentionally not abstract - subclasses can optionally
        override this method for custom setup logic.
        """
        pass

    @abstractmethod
    def detect(self, page: Page, url: str) -> DetectionResult:
        """
        Check if this bot detection is present on the page.

        Args:
            page: Playwright Page object
            url: The URL being scraped

        Returns:
            DetectionResult with detected=True/False and details
        """
        raise NotImplementedError

    @abstractmethod
    def solve(
        self,
        page: Page,
        url: str,
        detection_result: DetectionResult
    ) -> bool:
        """
        Attempt to solve/bypass this detection.

        Args:
            page: Playwright Page object
            url: The URL being scraped
            detection_result: Result from detect() with details

        Returns:
            True if solved successfully, False otherwise
        """
        raise NotImplementedError

    # === HELPER METHODS (use in subclasses) ===

    def _check_selectors(self, page: Page) -> Optional[str]:
        """Check if any of our selectors are present on the page."""
        for selector in self.selectors:
            try:
                if page.locator(selector).count() > 0:
                    logger.debug(f"[{self.name}] Detected via selector: {selector}")
                    return selector
            except Exception:
                continue
        return None

    def _check_title(self, page: Page) -> Optional[str]:
        """Check if page title matches any indicators."""
        try:
            title = (page.title() or "").lower()
            for indicator in self.title_indicators:
                if indicator.lower() in title:
                    logger.debug(f"[{self.name}] Detected via title: {indicator}")
                    return indicator
        except Exception:
            pass
        return None

    def _check_content(self, page: Page, max_length: int = 50000) -> Optional[str]:
        """Check if page content matches any indicators."""
        try:
            content = page.content() or ""
            if len(content) > max_length:
                return None  # Skip large pages for performance

            content_lower = content.lower()
            for indicator in self.content_indicators:
                if indicator.lower() in content_lower:
                    logger.debug(f"[{self.name}] Detected via content: {indicator}")
                    return indicator
        except Exception:
            pass
        return None

    def _wait_for_element_gone(
        self,
        page: Page,
        selector: str,
        timeout: int = 30
    ) -> bool:
        """Wait for a selector to disappear (challenge passed)."""
        import time

        start = time.time()
        while time.time() - start < timeout:
            try:
                if page.locator(selector).count() == 0:
                    return True
                if not page.locator(selector).first.is_visible(timeout=500):
                    return True
            except Exception:
                return True  # Element gone
            time.sleep(1)
        return False

    def _log_detection(self, detected: bool, reason: str = ""):
        """Log detection result."""
        if detected:
            logger.info(f"[{self.name}] Detected: {reason}")
        else:
            logger.debug(f"[{self.name}] Not detected")

    def _log_solve(self, success: bool, reason: str = ""):
        """Log solve result."""
        if success:
            logger.info(f"[{self.name}] Solved: {reason}")
        else:
            logger.warning(f"[{self.name}] Failed to solve: {reason}")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, priority={self.priority})>"
