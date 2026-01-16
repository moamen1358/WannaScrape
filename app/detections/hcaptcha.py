"""
hCaptcha Detection Plugin
=========================
Detects and solves hCaptcha challenges.

Requires external API (2captcha, capsolver) for solving.
"""

import time
import logging
from typing import Optional

import httpx
from playwright.sync_api import Page

from .base import (
    BaseDetection,
    DetectionResult,
    DetectionCategory,
    SolveMethod
)

logger = logging.getLogger("scraper.detections.hcaptcha")


class HcaptchaDetection(BaseDetection):
    """
    hCaptcha detection and solving.

    hCaptcha is commonly used as a Cloudflare alternative.
    Requires API key for automated solving.
    """

    # === REQUIRED ATTRIBUTES ===
    name = "hcaptcha"
    priority = 35
    category = DetectionCategory.CAPTCHA

    # === OPTIONAL ATTRIBUTES ===
    description = "hCaptcha challenge"
    requires_api = True
    solve_timeout = 120

    # === DETECTION PATTERNS ===
    selectors = [
        "iframe[src*='hcaptcha']",
        ".h-captcha",
        "#hcaptcha",
        "[data-hcaptcha-sitekey]",
    ]

    # === API CONFIGURATION ===
    TWOCAPTCHA_API = "https://2captcha.com"
    CAPSOLVER_API = "https://api.capsolver.com"

    def _setup(self):
        """Setup API configuration."""
        captcha_config = self.config.get("captcha", {})
        self.api_key = captcha_config.get("api_key", "")
        self.service = captcha_config.get("service", "2captcha")
        self.enabled = captcha_config.get("enabled", False) and bool(self.api_key)

    def detect(self, page: Page, url: str) -> DetectionResult:
        """Detect hCaptcha on page."""
        matched_selector = self._check_selectors(page)

        if matched_selector:
            sitekey = self._extract_sitekey(page)

            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=1.0,
                details={
                    "selector": matched_selector,
                    "sitekey": sitekey,
                },
                solve_method=SolveMethod.API if self.enabled else SolveMethod.NONE
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
        """Solve hCaptcha using API service."""
        if not self.enabled:
            logger.warning("hCaptcha solving disabled - no API key configured")
            return False

        sitekey = detection_result.details.get("sitekey")
        if not sitekey:
            logger.error("No sitekey found for hCaptcha")
            return False

        logger.info(f"Solving hCaptcha with {self.service}")

        if self.service == "2captcha":
            return self._solve_with_2captcha(page, url, sitekey)
        elif self.service == "capsolver":
            return self._solve_with_capsolver(page, url, sitekey)
        else:
            logger.error(f"Unknown CAPTCHA service: {self.service}")
            return False

    def _extract_sitekey(self, page: Page) -> Optional[str]:
        """Extract hCaptcha sitekey from page."""
        try:
            return page.evaluate("""
                () => {
                    const el = document.querySelector('.h-captcha, [data-sitekey], [data-hcaptcha-sitekey]');
                    return el ? (el.getAttribute('data-sitekey') || el.getAttribute('data-hcaptcha-sitekey')) : null;
                }
            """)
        except Exception:
            return None

    def _solve_with_2captcha(self, page: Page, url: str, sitekey: str) -> bool:
        """Solve using 2captcha API."""
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{self.TWOCAPTCHA_API}/in.php",
                    data={
                        "key": self.api_key,
                        "method": "hcaptcha",
                        "sitekey": sitekey,
                        "pageurl": url,
                        "json": 1
                    }
                )
                result = response.json()

                if result.get("status") != 1:
                    logger.error(f"2captcha task creation failed: {result}")
                    return False

                task_id = result["request"]

                # Poll for result
                start_time = time.time()
                while time.time() - start_time < self.solve_timeout:
                    time.sleep(5)

                    response = client.get(
                        f"{self.TWOCAPTCHA_API}/res.php",
                        params={
                            "key": self.api_key,
                            "action": "get",
                            "id": task_id,
                            "json": 1
                        }
                    )
                    result = response.json()

                    if result.get("status") == 1:
                        return self._inject_solution(page, result.get("request"))
                    elif result.get("request") == "CAPCHA_NOT_READY":
                        continue
                    else:
                        logger.error(f"2captcha error: {result}")
                        return False

                logger.error("2captcha timeout")
                return False

        except Exception as e:
            logger.error(f"2captcha solving failed: {e}")
            return False

    def _solve_with_capsolver(self, page: Page, url: str, sitekey: str) -> bool:
        """Solve using Capsolver API."""
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{self.CAPSOLVER_API}/createTask",
                    json={
                        "clientKey": self.api_key,
                        "task": {
                            "type": "HCaptchaTaskProxyLess",
                            "websiteURL": url,
                            "websiteKey": sitekey
                        }
                    }
                )
                result = response.json()

                if result.get("errorId") != 0:
                    logger.error(f"Capsolver error: {result}")
                    return False

                task_id = result.get("taskId")

                start_time = time.time()
                while time.time() - start_time < self.solve_timeout:
                    time.sleep(3)

                    response = client.post(
                        f"{self.CAPSOLVER_API}/getTaskResult",
                        json={
                            "clientKey": self.api_key,
                            "taskId": task_id
                        }
                    )
                    result = response.json()

                    if result.get("status") == "ready":
                        solution = result.get("solution", {}).get("token")
                        if solution:
                            return self._inject_solution(page, solution)
                    elif result.get("status") == "processing":
                        continue
                    else:
                        logger.error(f"Capsolver error: {result}")
                        return False

                logger.error("Capsolver timeout")
                return False

        except Exception as e:
            logger.error(f"Capsolver solving failed: {e}")
            return False

    def _inject_solution(self, page: Page, solution: str) -> bool:
        """Inject hCaptcha solution into page."""
        try:
            page.evaluate(f"""
                () => {{
                    const textarea = document.querySelector('[name="h-captcha-response"], textarea[name="h-captcha-response"]');
                    if (textarea) {{
                        textarea.value = '{solution}';
                    }}

                    // Also try iframe approach
                    const iframe = document.querySelector('iframe[src*="hcaptcha"]');
                    if (iframe && iframe.contentDocument) {{
                        const iframeTextarea = iframe.contentDocument.querySelector('textarea');
                        if (iframeTextarea) iframeTextarea.value = '{solution}';
                    }}
                }}
            """)
            logger.info("hCaptcha solution injected")
            page.wait_for_timeout(2000)
            return True
        except Exception as e:
            logger.error(f"Failed to inject solution: {e}")
            return False
