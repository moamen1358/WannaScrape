"""
Cloudflare Detection Plugin
===========================
Detects and handles Cloudflare challenge pages.

Detection methods:
1. CSS selectors for challenge elements
2. Page title patterns
3. Content phrases

Solving:
- Wait-based (Cloudflare auto-solves after browser verification)
- Turnstile CAPTCHA (requires API if present)
"""

import time
import logging

from playwright.sync_api import Page

from .base import (
    BaseDetection,
    DetectionResult,
    DetectionCategory,
    SolveMethod
)

logger = logging.getLogger("scraper.detections.cloudflare")


class CloudflareDetection(BaseDetection):
    """
    Cloudflare challenge detection and bypass.

    Cloudflare uses several verification methods:
    1. JavaScript challenge (auto-solves)
    2. Browser verification (auto-solves)
    3. Turnstile CAPTCHA (may need API)
    4. hCaptcha (needs API)
    """

    # === REQUIRED ATTRIBUTES ===
    name = "cloudflare"
    priority = 10  # Run early - Cloudflare is common
    category = DetectionCategory.CHALLENGE

    # === OPTIONAL ATTRIBUTES ===
    description = "Cloudflare WAF and bot management"
    requires_api = False  # Usually auto-solves
    solve_timeout = 45

    # === DETECTION PATTERNS ===
    selectors = [
        "#challenge-running",
        "#challenge-stage",
        ".cf-browser-verification",
        "#cf-challenge-running",
        "#cf-wrapper",
        "#cf-hcaptcha-container",
        ".cf-turnstile",
        "[data-turnstile-sitekey]",
    ]

    title_indicators = [
        "just a moment",
        "attention required",
        "checking your browser",
        "please wait",
    ]

    content_indicators = [
        "checking your browser before",
        "this process is automatic",
        "you will be redirected",
        "ray id:",
        "enable javascript and cookies",
        "ddos protection by",
        "please stand by",
        "verify you are human",
        "cloudflare",
    ]

    def detect(self, page: Page, url: str) -> DetectionResult:
        """
        Detect if Cloudflare challenge is present.

        Checks selectors, title, and content in that order.
        Returns early on first match for performance.
        """
        # Check CSS selectors first (fastest)
        matched_selector = self._check_selectors(page)
        if matched_selector:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=1.0,
                details={"method": "selector", "selector": matched_selector},
                solve_method=SolveMethod.WAIT
            )

        # Check page title
        matched_title = self._check_title(page)
        if matched_title:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=0.9,
                details={"method": "title", "indicator": matched_title},
                solve_method=SolveMethod.WAIT
            )

        # Check content (only for smaller pages to avoid performance hit)
        try:
            content = page.content() or ""
            if len(content) < 50000:
                matched_content = self._check_content(page)
                if matched_content:
                    # Lower confidence for content match (could be false positive)
                    return DetectionResult(
                        detected=True,
                        detection_type=self.name,
                        confidence=0.7,
                        details={"method": "content", "indicator": matched_content},
                        solve_method=SolveMethod.WAIT
                    )
        except Exception:
            pass

        return DetectionResult(
            detected=False,
            detection_type=self.name
        )

    def solve(
        self,
        page: Page,
        url: str,
        detection_result: DetectionResult
    ) -> bool:
        """
        Solve Cloudflare challenge by waiting.

        Cloudflare JavaScript challenges typically auto-solve
        after the browser passes verification checks.
        """
        logger.info("Cloudflare challenge detected, waiting for auto-solve...")

        start = time.time()
        check_interval = 3  # Check every 3 seconds

        while time.time() - start < self.solve_timeout:
            time.sleep(check_interval)

            # Re-check if challenge is still present
            new_result = self.detect(page, url)

            if not new_result.detected:
                elapsed = time.time() - start
                self._log_solve(True, f"Challenge passed after {elapsed:.1f}s")
                return True

            # Check if we're now on a different page (redirect after solve)
            current_url = page.url
            if current_url != url and "challenge" not in current_url.lower():
                elapsed = time.time() - start
                self._log_solve(True, f"Redirected after {elapsed:.1f}s")
                return True

            logger.debug(f"Still waiting for Cloudflare... ({time.time() - start:.1f}s)")

        self._log_solve(False, f"Timeout after {self.solve_timeout}s")
        return False

    def _check_for_turnstile(self, page: Page) -> bool:
        """Check if Cloudflare Turnstile CAPTCHA is present."""
        turnstile_selectors = [
            ".cf-turnstile",
            "[data-turnstile-sitekey]",
            "iframe[src*='challenges.cloudflare.com']"
        ]
        for selector in turnstile_selectors:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except Exception:
                pass
        return False
