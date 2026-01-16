"""
reCAPTCHA Detection Plugin
==========================
Detects and solves Google reCAPTCHA v2 and v3.

Requires external API (2captcha, capsolver) for solving.
"""

import time
import re
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

logger = logging.getLogger("scraper.detections.recaptcha")


class RecaptchaDetection(BaseDetection):
    """
    Google reCAPTCHA v2/v3 detection and solving.

    Detection:
    - Checks for reCAPTCHA iframe and elements
    - Extracts sitekey for API solving

    Solving:
    - Uses 2captcha or capsolver API
    - Injects solution into page
    """

    # === REQUIRED ATTRIBUTES ===
    name = "recaptcha"
    priority = 30  # After Cloudflare
    category = DetectionCategory.CAPTCHA

    # === OPTIONAL ATTRIBUTES ===
    description = "Google reCAPTCHA v2/v3"
    requires_api = True
    solve_timeout = 120

    # === DETECTION PATTERNS ===
    selectors = [
        "iframe[src*='recaptcha']",
        ".g-recaptcha",
        "#recaptcha",
        "iframe[title*='reCAPTCHA']",
        "[data-sitekey]",
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

        if not self.enabled:
            logger.debug("reCAPTCHA solving disabled (no API key)")

    def detect(self, page: Page, url: str) -> DetectionResult:
        """Detect reCAPTCHA on page."""
        matched_selector = self._check_selectors(page)

        if matched_selector:
            sitekey = self._extract_sitekey(page)
            version = self._detect_version(page)

            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=1.0,
                details={
                    "selector": matched_selector,
                    "sitekey": sitekey,
                    "version": version,
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
        """Solve reCAPTCHA using API service."""
        if not self.enabled:
            logger.warning("reCAPTCHA solving disabled - no API key configured")
            return False

        sitekey = detection_result.details.get("sitekey")
        if not sitekey:
            logger.error("No sitekey found for reCAPTCHA")
            return False

        logger.info(f"Solving reCAPTCHA with {self.service} (sitekey: {sitekey[:20]}...)")

        if self.service == "2captcha":
            return self._solve_with_2captcha(page, url, sitekey)
        elif self.service == "capsolver":
            return self._solve_with_capsolver(page, url, sitekey)
        else:
            logger.error(f"Unknown CAPTCHA service: {self.service}")
            return False

    def _extract_sitekey(self, page: Page) -> Optional[str]:
        """Extract reCAPTCHA sitekey from page."""
        try:
            # Try data-sitekey attribute
            sitekey = page.evaluate("""
                () => {
                    const el = document.querySelector('.g-recaptcha, [data-sitekey]');
                    return el ? el.getAttribute('data-sitekey') : null;
                }
            """)
            if sitekey:
                return sitekey

            # Try iframe src parameter
            iframe_src = page.evaluate("""
                () => {
                    const iframe = document.querySelector('iframe[src*="recaptcha"]');
                    return iframe ? iframe.src : null;
                }
            """)
            if iframe_src and 'k=' in iframe_src:
                match = re.search(r'k=([^&]+)', iframe_src)
                if match:
                    return match.group(1)

            return None
        except Exception:
            return None

    def _detect_version(self, page: Page) -> str:
        """Detect reCAPTCHA version (v2 or v3)."""
        try:
            # v3 typically has invisible class or action parameter
            is_v3 = page.evaluate("""
                () => {
                    const el = document.querySelector('.g-recaptcha');
                    if (el && el.getAttribute('data-size') === 'invisible') return true;
                    if (el && el.getAttribute('data-action')) return true;
                    return false;
                }
            """)
            return "v3" if is_v3 else "v2"
        except Exception:
            return "v2"

    def _solve_with_2captcha(self, page: Page, url: str, sitekey: str) -> bool:
        """Solve using 2captcha API."""
        try:
            with httpx.Client(timeout=30) as client:
                # Create task
                response = client.post(
                    f"{self.TWOCAPTCHA_API}/in.php",
                    data={
                        "key": self.api_key,
                        "method": "userrecaptcha",
                        "googlekey": sitekey,
                        "pageurl": url,
                        "json": 1
                    }
                )
                result = response.json()

                if result.get("status") != 1:
                    logger.error(f"2captcha task creation failed: {result}")
                    return False

                task_id = result["request"]
                logger.info(f"2captcha task created: {task_id}")

                # Poll for result
                solution = self._poll_2captcha(client, task_id)
                if not solution:
                    return False

                return self._inject_solution(page, solution)

        except Exception as e:
            logger.error(f"2captcha solving failed: {e}")
            return False

    def _poll_2captcha(self, client: httpx.Client, task_id: str) -> Optional[str]:
        """Poll 2captcha for solution."""
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
                logger.info("reCAPTCHA solved!")
                return result.get("request")
            elif result.get("request") == "CAPCHA_NOT_READY":
                logger.debug("Waiting for solution...")
                continue
            else:
                logger.error(f"2captcha error: {result}")
                return None

        logger.error("2captcha timeout")
        return None

    def _solve_with_capsolver(self, page: Page, url: str, sitekey: str) -> bool:
        """Solve using Capsolver API."""
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{self.CAPSOLVER_API}/createTask",
                    json={
                        "clientKey": self.api_key,
                        "task": {
                            "type": "ReCaptchaV2TaskProxyLess",
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

                # Poll for result
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
                        solution = result.get("solution", {}).get("gRecaptchaResponse")
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
        """Inject reCAPTCHA solution into page."""
        try:
            page.evaluate(f"""
                () => {{
                    // Set response textarea
                    const textarea = document.querySelector('#g-recaptcha-response, textarea[name="g-recaptcha-response"]');
                    if (textarea) {{
                        textarea.style.display = 'block';
                        textarea.value = '{solution}';
                        textarea.style.display = 'none';
                    }}

                    // Trigger callback if available
                    if (typeof ___grecaptcha_cfg !== 'undefined') {{
                        Object.keys(___grecaptcha_cfg.clients).forEach(key => {{
                            const client = ___grecaptcha_cfg.clients[key];
                            if (client && client.Y && client.Y.Y && client.Y.Y.callback) {{
                                client.Y.Y.callback('{solution}');
                            }}
                        }});
                    }}
                }}
            """)
            logger.info("reCAPTCHA solution injected")
            page.wait_for_timeout(2000)
            return True
        except Exception as e:
            logger.error(f"Failed to inject solution: {e}")
            return False
