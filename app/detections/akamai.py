"""
Akamai Bot Manager Detection Plugin
====================================
Detects and handles Akamai Bot Manager / EdgeSuite protection.

Akamai serves a generic "Access Denied" page with a reference ID
and a link to errors.edgesuite.net when it blocks automated traffic.

Detection methods:
- Page title: "Access Denied"
- Content: edgesuite.net reference, Akamai-specific reference IDs
- Selectors: Akamai challenge elements

Solving methods:
- Wait-based (some JS challenges auto-resolve)
- Page reload with delay
- Cannot bypass hard IP/fingerprint blocks (returns False)
"""

import time
import logging
from typing import Optional

from playwright.sync_api import Page

from .base import (
    BaseDetection,
    DetectionResult,
    DetectionCategory,
    SolveMethod
)

logger = logging.getLogger("scraper.detections.akamai")


class AkamaiDetection(BaseDetection):
    """
    Akamai Bot Manager detection and bypass.

    Akamai uses several blocking methods:
    1. Hard block - "Access Denied" page with edgesuite.net reference
    2. JavaScript challenge - auto-solving browser check
    3. Sensor data collection via _abck cookie

    Hard blocks (edgesuite.net) typically cannot be bypassed without
    proxy rotation or different browser fingerprints.
    """

    # === REQUIRED ATTRIBUTES ===
    name = "akamai"
    priority = 25  # Standard challenge priority (20-40 range)
    category = DetectionCategory.CHALLENGE

    # === OPTIONAL ATTRIBUTES ===
    description = "Akamai Bot Manager / EdgeSuite protection"
    requires_api = False
    solve_timeout = 30

    # === DETECTION PATTERNS ===
    selectors = [
        "#ak-challenge",
        "#akamai-challenge-js",
        "script[src*='akamaized']",
        "script[src*='akamai']",
    ]

    title_indicators = [
        "access denied",
    ]

    content_indicators = [
        "errors.edgesuite.net",
        "akamai",
        "ak_bmsc",
        "/_sec/cp_challenge",
        "reference #",
    ]

    def detect(self, page: Page, url: str) -> DetectionResult:
        """
        Detect if Akamai Bot Manager is blocking the page.

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
            # Title alone could be generic — check content to confirm Akamai
            is_hard_block = self._is_edgesuite_block(page)
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=1.0 if is_hard_block else 0.8,
                details={
                    "method": "title",
                    "indicator": matched_title,
                    "hard_block": is_hard_block,
                },
                solve_method=SolveMethod.BYPASS if is_hard_block else SolveMethod.WAIT
            )

        # Check page content (only for smaller pages — block pages are small)
        matched_content = self._check_content(page, max_length=50000)
        if matched_content:
            is_hard_block = self._is_edgesuite_block(page)
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=0.9 if is_hard_block else 0.7,
                details={
                    "method": "content",
                    "indicator": matched_content,
                    "hard_block": is_hard_block,
                },
                solve_method=SolveMethod.BYPASS if is_hard_block else SolveMethod.WAIT
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
        Attempt to solve/bypass Akamai protection.

        Hard blocks (edgesuite.net "Access Denied") typically cannot be
        solved by waiting — they require a different IP or fingerprint.
        JS challenges may auto-resolve after browser verification.
        """
        is_hard_block = detection_result.details.get("hard_block", False)

        if is_hard_block:
            logger.warning(
                "Akamai hard block detected (edgesuite.net). "
                "This usually requires proxy rotation or a different fingerprint."
            )
            # Still try a reload in case it was transient
            try:
                page.reload(wait_until="domcontentloaded", timeout=15000)
                time.sleep(3)

                new_result = self.detect(page, url)
                if not new_result.detected:
                    self._log_solve(True, "Solved after reload")
                    return True
            except Exception:
                pass

            self._log_solve(False, "Hard block — cannot bypass without proxy/fingerprint change")
            return False

        # JS challenge — wait for auto-solve
        logger.info("Akamai JS challenge detected, waiting for auto-solve...")

        start = time.time()
        check_interval = 3

        while time.time() - start < self.solve_timeout:
            time.sleep(check_interval)

            new_result = self.detect(page, url)
            if not new_result.detected:
                elapsed = time.time() - start
                self._log_solve(True, f"Challenge passed after {elapsed:.1f}s")
                return True

            # Check for redirect (challenge passed)
            current_url = page.url
            if current_url != url and "challenge" not in current_url.lower():
                elapsed = time.time() - start
                self._log_solve(True, f"Redirected after {elapsed:.1f}s")
                return True

            logger.debug(f"Still waiting for Akamai... ({time.time() - start:.1f}s)")

        # Last resort: try a reload
        try:
            page.reload(wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)

            if not self.detect(page, url).detected:
                self._log_solve(True, "Solved after reload")
                return True
        except Exception:
            pass

        self._log_solve(False, f"Timeout after {self.solve_timeout}s")
        return False

    def _is_edgesuite_block(self, page: Page) -> bool:
        """Check if this is a hard Akamai block via edgesuite.net reference."""
        try:
            content = (page.content() or "").lower()
            return "edgesuite.net" in content
        except Exception:
            return False
