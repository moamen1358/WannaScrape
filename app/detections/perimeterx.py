"""
PerimeterX Detection Plugin
===========================
Detects and solves PerimeterX (HUMAN) bot protection.

PerimeterX uses a "Press & Hold" challenge that requires
behavioral solving (mouse simulation).
"""

import time
import random
import logging

from playwright.sync_api import Page

from .base import (
    BaseDetection,
    DetectionResult,
    DetectionCategory,
    SolveMethod
)

logger = logging.getLogger("scraper.detections.perimeterx")


class PerimeterXDetection(BaseDetection):
    """
    PerimeterX (now HUMAN) bot protection.

    Detection:
    - Press & Hold button challenge
    - PX cookie checks
    - Blocked page patterns

    Solving:
    - Behavioral simulation (mouse hold with micro-movements)
    - No API required
    """

    # === REQUIRED ATTRIBUTES ===
    name = "perimeterx"
    priority = 20  # High priority - behavioral
    category = DetectionCategory.CHALLENGE

    # === OPTIONAL ATTRIBUTES ===
    description = "PerimeterX (HUMAN) Press & Hold challenge"
    requires_api = False  # Behavioral only
    solve_timeout = 30

    # === DETECTION PATTERNS ===
    selectors = [
        "#px-captcha",
        "button:has-text('Press & Hold')",
        "div[aria-label='Press & Hold']",
        ".px-captcha-container",
        "#px-captcha-container",
    ]

    title_indicators = [
        "access denied",
        "please verify",
        "human verification",
    ]

    content_indicators = [
        "press and hold",
        "press & hold",
        "px-captcha",
        "perimeterx",
        "human verification",
    ]

    def detect(self, page: Page, url: str) -> DetectionResult:
        """Detect PerimeterX challenge."""
        # Check selectors
        matched_selector = self._check_selectors(page)
        if matched_selector:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=1.0,
                details={"selector": matched_selector},
                solve_method=SolveMethod.BEHAVIORAL
            )

        # Check content for smaller pages
        matched_content = self._check_content(page, max_length=30000)
        if matched_content:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=0.8,
                details={"method": "content", "indicator": matched_content},
                solve_method=SolveMethod.BEHAVIORAL
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
        Solve PerimeterX Press & Hold challenge.

        Uses behavioral simulation with:
        - Natural mouse movement to button
        - Press and hold for 4-6 seconds
        - Micro-movements during hold
        - Natural release
        """
        logger.info("Attempting PerimeterX Press & Hold bypass...")

        selector = detection_result.details.get("selector")
        if not selector:
            # Try to find the button
            for sel in self.selectors:
                try:
                    if page.locator(sel).count() > 0:
                        selector = sel
                        break
                except Exception:
                    continue

        if not selector:
            logger.warning("Could not find Press & Hold button")
            return False

        try:
            button = page.locator(selector).first
            if not button.is_visible(timeout=2000):
                logger.warning("Press & Hold button not visible")
                return False

            # Get button position
            box = button.bounding_box()
            if not box:
                logger.warning("Could not get button bounding box")
                return False

            center_x = box['x'] + box['width'] / 2
            center_y = box['y'] + box['height'] / 2

            # Move to button with natural motion
            logger.debug("Moving to button...")
            self._natural_move_to(page, center_x, center_y, box)

            # Brief pause before clicking
            time.sleep(random.uniform(0.1, 0.2))

            # Press and hold
            logger.info("Pressing and holding...")
            page.mouse.down()

            hold_duration = random.uniform(4.0, 6.0)
            hold_start = time.time()

            # Micro-movements during hold
            logger.debug(f"Holding for {hold_duration:.1f}s with micro-movements...")
            while time.time() - hold_start < hold_duration:
                # Small random movements within button bounds
                new_x = center_x + random.gauss(0, 1.5)
                new_y = center_y + random.gauss(0, 1.5)

                # Keep within button bounds
                new_x = max(box['x'] + 3, min(box['x'] + box['width'] - 3, new_x))
                new_y = max(box['y'] + 3, min(box['y'] + box['height'] - 3, new_y))

                page.mouse.move(new_x, new_y)
                time.sleep(random.uniform(0.04, 0.08))

            # Release
            page.mouse.up()
            actual_hold = time.time() - hold_start
            logger.info(f"Released after {actual_hold:.1f}s")

            # Wait for challenge to process
            page.wait_for_timeout(1500)

            # Check if challenge passed
            return self._check_solved(page, selector)

        except Exception as e:
            logger.error(f"PerimeterX bypass error: {e}")
            return False

    def _natural_move_to(self, page: Page, target_x: float, target_y: float, box: dict):
        """Move mouse to target with natural bezier curve motion."""
        # Get current approximate position (use box corner as start)
        start_x = box['x'] - 50 + random.uniform(-20, 20)
        start_y = box['y'] - 30 + random.uniform(-20, 20)

        # Generate bezier control points
        distance = ((target_x - start_x) ** 2 + (target_y - start_y) ** 2) ** 0.5
        steps = max(10, min(25, int(distance / 20)))

        # Control points for curve
        dx = target_x - start_x
        dy = target_y - start_y

        # Perpendicular offset for curve
        perp_x = -dy / (distance + 0.001)
        perp_y = dx / (distance + 0.001)
        curve_offset = distance * random.uniform(0.1, 0.3) * random.choice([-1, 1])

        cp1_x = start_x + dx * 0.3 + perp_x * curve_offset
        cp1_y = start_y + dy * 0.3 + perp_y * curve_offset
        cp2_x = start_x + dx * 0.7 + perp_x * curve_offset * 0.5
        cp2_y = start_y + dy * 0.7 + perp_y * curve_offset * 0.5

        # Move along bezier curve
        for i in range(steps + 1):
            t = i / steps
            # Ease in-out
            t = t * t * (3 - 2 * t)

            # Cubic bezier
            u = 1 - t
            x = u**3 * start_x + 3 * u**2 * t * cp1_x + 3 * u * t**2 * cp2_x + t**3 * target_x
            y = u**3 * start_y + 3 * u**2 * t * cp1_y + 3 * u * t**2 * cp2_y + t**3 * target_y

            # Add slight tremor
            x += random.gauss(0, 0.5)
            y += random.gauss(0, 0.5)

            page.mouse.move(x, y)
            time.sleep(random.uniform(0.002, 0.005))

    def _check_solved(self, page: Page, original_selector: str) -> bool:
        """Check if the challenge was solved."""
        try:
            # Check if button is gone
            if page.locator(original_selector).count() == 0:
                self._log_solve(True, "Challenge element gone")
                return True

            # Check if button is hidden
            if not page.locator(original_selector).first.is_visible(timeout=500):
                self._log_solve(True, "Challenge element hidden")
                return True

        except Exception:
            self._log_solve(True, "Challenge element check failed (likely passed)")
            return True

        # Check page title
        title = page.title().lower()
        if "denied" not in title and "blocked" not in title and "verify" not in title:
            self._log_solve(True, "Page title indicates success")
            return True

        self._log_solve(False, "Challenge still present")
        return False
