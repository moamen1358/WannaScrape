"""
DataDome Detection Plugin
=========================
Detects DataDome bot protection.

This is an EXAMPLE of how easy it is to add new detections.
DataDome typically uses a combination of:
- JavaScript challenge
- CAPTCHA (GeeTest or custom)
- Cookie-based tracking

Adding this detection took < 10 minutes!
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

logger = logging.getLogger("scraper.detections.datadome")


class DataDomeDetection(BaseDetection):
    """
    DataDome bot protection detection and bypass.

    DataDome is used by many e-commerce and media sites.
    It uses device fingerprinting and behavior analysis.
    """

    # === REQUIRED ATTRIBUTES ===
    name = "datadome"
    priority = 25  # After Cloudflare, before CAPTCHAs
    category = DetectionCategory.CHALLENGE

    # === OPTIONAL ATTRIBUTES ===
    description = "DataDome bot management"
    requires_api = False  # Can sometimes be bypassed with waiting
    solve_timeout = 30

    # === DETECTION PATTERNS ===
    selectors = [
        "#datadome",
        ".datadome-captcha",
        "iframe[src*='datadome']",
        "iframe[src*='geo.captcha-delivery.com']",
        "#dd_captcha",
        ".dd-captcha",
    ]

    title_indicators = [
        "datadome",
        "blocked",
        "access denied",
    ]

    content_indicators = [
        "datadome",
        "captcha-delivery.com",
        "dd_captcha",
        "geo.captcha",
        "please verify you are human",
    ]

    def detect(self, page: Page, url: str) -> DetectionResult:
        """Detect DataDome challenge."""
        # Check for DataDome-specific selectors
        matched_selector = self._check_selectors(page)
        if matched_selector:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=1.0,
                details={"selector": matched_selector},
                solve_method=SolveMethod.WAIT
            )

        # Check for DataDome cookie
        try:
            cookies = page.context.cookies()
            for cookie in cookies:
                if "datadome" in cookie.get("name", "").lower():
                    # DataDome cookie present but might be valid
                    # Only flag if we see challenge content
                    if self._check_content(page):
                        return DetectionResult(
                            detected=True,
                            detection_type=self.name,
                            confidence=0.8,
                            details={"method": "cookie_and_content"},
                            solve_method=SolveMethod.WAIT
                        )
        except Exception:
            pass

        # Check page content
        matched_content = self._check_content(page, max_length=30000)
        if matched_content:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=0.7,
                details={"method": "content", "indicator": matched_content},
                solve_method=SolveMethod.WAIT
            )

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
        Attempt to solve DataDome challenge.

        DataDome often auto-solves after:
        1. JavaScript challenge completion
        2. Cookie validation
        3. Sometimes requires manual CAPTCHA

        We try waiting first, then report if CAPTCHA is needed.
        """
        logger.info("DataDome challenge detected, attempting bypass...")

        # Strategy 1: Wait for JS challenge to auto-solve
        for i in range(3):
            time.sleep(5)

            # Re-check detection
            new_result = self.detect(page, url)
            if not new_result.detected:
                self._log_solve(True, "Challenge auto-solved")
                return True

            # Check for redirect
            if page.url != url:
                self._log_solve(True, "Redirected past challenge")
                return True

            logger.debug(f"Still waiting for DataDome... attempt {i + 1}/3")

        # Strategy 2: Try refreshing (sometimes clears JS challenge)
        try:
            page.reload(wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)

            new_result = self.detect(page, url)
            if not new_result.detected:
                self._log_solve(True, "Challenge cleared after refresh")
                return True
        except Exception:
            pass

        # Check if it's a CAPTCHA that requires API
        if self._has_captcha(page):
            logger.warning("DataDome CAPTCHA detected - may require API solving")
            self._log_solve(False, "CAPTCHA requires API")
            return False

        self._log_solve(False, "Could not bypass DataDome")
        return False

    def _has_captcha(self, page: Page) -> bool:
        """Check if DataDome is showing a CAPTCHA (not just JS challenge)."""
        captcha_selectors = [
            "iframe[src*='geo.captcha-delivery.com']",
            ".geetest_holder",
            "#geetest_captcha",
        ]
        for selector in captcha_selectors:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except Exception:
                pass
        return False
