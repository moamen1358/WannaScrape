"""
CAPTCHA solving integration supporting multiple services and CAPTCHA types.

Supported services: 2captcha, capsolver
Supported CAPTCHA types: reCAPTCHA v2/v3, hCaptcha, image CAPTCHA, Turnstile, PerimeterX
"""

import time
import random
import logging
import httpx
from typing import Optional, Dict
from playwright.sync_api import Page

logger = logging.getLogger("scraper.captcha")


class CaptchaSolver:
    """
    CAPTCHA solving integration supporting multiple services and CAPTCHA types.
    """

    TWOCAPTCHA_API = "https://2captcha.com"
    CAPSOLVER_API = "https://api.capsolver.com"

    def __init__(self, config: dict):
        self.enabled = config.get("enabled", False)
        self.service = config.get("service", "2captcha")
        self.api_key = config.get("api_key", "")
        self.timeout = config.get("timeout", 120)
        self.max_retries = config.get("max_retries", 3)

        if self.enabled and not self.api_key:
            logger.warning("CAPTCHA solving enabled but no API key provided")
            self.enabled = False

    def detect_captcha_type(self, page: Page) -> Optional[Dict]:
        """Detect what type of CAPTCHA is present on the page."""
        try:
            # Check for reCAPTCHA
            recaptcha_selectors = [
                "iframe[src*='recaptcha']",
                ".g-recaptcha",
                "#recaptcha",
                "iframe[title*='reCAPTCHA']"
            ]
            for selector in recaptcha_selectors:
                if page.locator(selector).count() > 0:
                    sitekey = self._extract_recaptcha_sitekey(page)
                    return {"type": "recaptcha_v2", "sitekey": sitekey}

            # Check for hCaptcha
            hcaptcha_selectors = [
                "iframe[src*='hcaptcha']",
                ".h-captcha",
                "#hcaptcha"
            ]
            for selector in hcaptcha_selectors:
                if page.locator(selector).count() > 0:
                    sitekey = self._extract_hcaptcha_sitekey(page)
                    return {"type": "hcaptcha", "sitekey": sitekey}

            # Check for Cloudflare Turnstile
            turnstile_selectors = [
                "iframe[src*='challenges.cloudflare.com']",
                ".cf-turnstile",
                "[data-turnstile-sitekey]"
            ]
            for selector in turnstile_selectors:
                if page.locator(selector).count() > 0:
                    sitekey = self._extract_turnstile_sitekey(page)
                    return {"type": "turnstile", "sitekey": sitekey}

            # Check for PerimeterX Press & Hold
            px_selectors = [
                "#px-captcha",
                "button:has-text('Press & Hold')",
                "div[aria-label='Press & Hold']"
            ]
            for selector in px_selectors:
                if page.locator(selector).count() > 0:
                    return {"type": "perimeterx", "selector": selector}

            # Check for image CAPTCHA
            image_captcha_selectors = [
                "img[src*='captcha']",
                ".captcha-image",
                "#captcha-image"
            ]
            for selector in image_captcha_selectors:
                if page.locator(selector).count() > 0:
                    return {"type": "image", "selector": selector}

            return None
        except Exception as e:
            logger.debug(f"Error detecting CAPTCHA type: {e}")
            return None

    def _extract_recaptcha_sitekey(self, page: Page) -> Optional[str]:
        """Extract reCAPTCHA sitekey from page."""
        try:
            sitekey = page.evaluate("""
                () => {
                    const el = document.querySelector('.g-recaptcha, [data-sitekey]');
                    return el ? el.getAttribute('data-sitekey') : null;
                }
            """)
            if sitekey:
                return sitekey

            iframe_src = page.evaluate("""
                () => {
                    const iframe = document.querySelector('iframe[src*="recaptcha"]');
                    return iframe ? iframe.src : null;
                }
            """)
            if iframe_src and 'k=' in iframe_src:
                import re
                match = re.search(r'k=([^&]+)', iframe_src)
                if match:
                    return match.group(1)

            return None
        except Exception:
            return None

    def _extract_hcaptcha_sitekey(self, page: Page) -> Optional[str]:
        """Extract hCaptcha sitekey from page."""
        try:
            return page.evaluate("""
                () => {
                    const el = document.querySelector('.h-captcha, [data-sitekey]');
                    return el ? el.getAttribute('data-sitekey') : null;
                }
            """)
        except Exception:
            return None

    def _extract_turnstile_sitekey(self, page: Page) -> Optional[str]:
        """Extract Cloudflare Turnstile sitekey from page."""
        try:
            return page.evaluate("""
                () => {
                    const el = document.querySelector('.cf-turnstile, [data-turnstile-sitekey]');
                    return el ? (el.getAttribute('data-sitekey') || el.getAttribute('data-turnstile-sitekey')) : null;
                }
            """)
        except Exception:
            return None

    def solve(self, page: Page, url: str) -> bool:
        """
        Detect and solve any CAPTCHA present on the page.
        Returns True if CAPTCHA was solved successfully.
        """
        captcha_info = self.detect_captcha_type(page)
        if not captcha_info:
            logger.debug("No CAPTCHA detected")
            return False

        captcha_type = captcha_info["type"]
        logger.info(f"CAPTCHA detected: {captcha_type}")

        # Handle PerimeterX separately (behavioral, not API-based)
        if captcha_type == "perimeterx":
            return self._solve_perimeterx(page, captcha_info.get("selector"))

        # For API-based solving (requires API key)
        if not self.enabled:
            logger.warning(f"CAPTCHA type '{captcha_type}' requires API key to solve")
            return False

        if self.service == "2captcha":
            return self._solve_with_2captcha(page, url, captcha_info)
        elif self.service == "capsolver":
            return self._solve_with_capsolver(page, url, captcha_info)

        logger.warning(f"Unknown CAPTCHA service: {self.service}")
        return False

    def _solve_with_2captcha(self, page: Page, url: str, captcha_info: dict) -> bool:
        """Solve CAPTCHA using 2captcha service."""
        captcha_type = captcha_info["type"]

        try:
            if captcha_type == "recaptcha_v2":
                return self._solve_recaptcha_2captcha(page, url, captcha_info.get("sitekey"))
            elif captcha_type == "hcaptcha":
                return self._solve_hcaptcha_2captcha(page, url, captcha_info.get("sitekey"))
            elif captcha_type == "turnstile":
                return self._solve_turnstile_2captcha(page, url, captcha_info.get("sitekey"))
            elif captcha_type == "image":
                return self._solve_image_2captcha(page, captcha_info.get("selector"))
            else:
                logger.warning(f"Unsupported CAPTCHA type for 2captcha: {captcha_type}")
                return False
        except Exception as e:
            logger.error(f"2captcha solving failed: {e}")
            return False

    def _solve_recaptcha_2captcha(self, page: Page, url: str, sitekey: str) -> bool:
        """Solve reCAPTCHA v2 using 2captcha."""
        if not sitekey:
            logger.error("No sitekey found for reCAPTCHA")
            return False

        logger.info(f"Solving reCAPTCHA v2 with 2captcha (sitekey: {sitekey[:20]}...)")

        with httpx.Client(timeout=30) as client:
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

            solution = self._poll_2captcha_result(client, task_id)
            if not solution:
                return False

            return self._inject_recaptcha_solution(page, solution)

    def _solve_hcaptcha_2captcha(self, page: Page, url: str, sitekey: str) -> bool:
        """Solve hCaptcha using 2captcha."""
        if not sitekey:
            logger.error("No sitekey found for hCaptcha")
            return False

        logger.info(f"Solving hCaptcha with 2captcha (sitekey: {sitekey[:20]}...)")

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
            solution = self._poll_2captcha_result(client, task_id)
            if not solution:
                return False

            return self._inject_hcaptcha_solution(page, solution)

    def _solve_turnstile_2captcha(self, page: Page, url: str, sitekey: str) -> bool:
        """Solve Cloudflare Turnstile using 2captcha."""
        if not sitekey:
            logger.error("No sitekey found for Turnstile")
            return False

        logger.info(f"Solving Turnstile with 2captcha (sitekey: {sitekey[:20]}...)")

        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{self.TWOCAPTCHA_API}/in.php",
                data={
                    "key": self.api_key,
                    "method": "turnstile",
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
            solution = self._poll_2captcha_result(client, task_id)
            if not solution:
                return False

            return self._inject_turnstile_solution(page, solution)

    def _solve_image_2captcha(self, page: Page, selector: str) -> bool:
        """Solve image CAPTCHA using 2captcha."""
        try:
            img_element = page.locator(selector).first
            img_src = img_element.get_attribute("src")

            if img_src.startswith("data:"):
                img_base64 = img_src.split(",")[1]
            else:
                img_base64 = page.evaluate(f"""
                    async () => {{
                        const response = await fetch('{img_src}');
                        const blob = await response.blob();
                        return new Promise((resolve) => {{
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result.split(',')[1]);
                            reader.readAsDataURL(blob);
                        }});
                    }}
                """)

            logger.info("Solving image CAPTCHA with 2captcha...")

            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{self.TWOCAPTCHA_API}/in.php",
                    data={
                        "key": self.api_key,
                        "method": "base64",
                        "body": img_base64,
                        "json": 1
                    }
                )
                result = response.json()

                if result.get("status") != 1:
                    logger.error(f"2captcha task creation failed: {result}")
                    return False

                task_id = result["request"]
                solution = self._poll_2captcha_result(client, task_id)
                if not solution:
                    return False

                input_selectors = [
                    "input[name*='captcha']",
                    "input[id*='captcha']",
                    "input[placeholder*='captcha' i]",
                    "input[type='text']"
                ]
                for inp_selector in input_selectors:
                    inp = page.locator(inp_selector).first
                    if inp.is_visible():
                        inp.fill(solution)
                        logger.info("Image CAPTCHA solution injected")
                        return True

                return False
        except Exception as e:
            logger.error(f"Image CAPTCHA solving failed: {e}")
            return False

    def _poll_2captcha_result(self, client: httpx.Client, task_id: str) -> Optional[str]:
        """Poll 2captcha for result."""
        start_time = time.time()

        while time.time() - start_time < self.timeout:
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
                solution = result.get("request")
                logger.info("CAPTCHA solved successfully!")
                return solution
            elif result.get("request") == "CAPCHA_NOT_READY":
                logger.debug("CAPTCHA not ready yet, waiting...")
                continue
            else:
                logger.error(f"2captcha error: {result}")
                return None

        logger.error("CAPTCHA solving timeout")
        return None

    def _inject_recaptcha_solution(self, page: Page, solution: str) -> bool:
        """Inject reCAPTCHA solution into the page."""
        try:
            page.evaluate(f"""
                () => {{
                    const textarea = document.querySelector('#g-recaptcha-response, textarea[name="g-recaptcha-response"]');
                    if (textarea) {{
                        textarea.style.display = 'block';
                        textarea.value = '{solution}';
                        textarea.style.display = 'none';
                    }}

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
            logger.error(f"Failed to inject reCAPTCHA solution: {e}")
            return False

    def _inject_hcaptcha_solution(self, page: Page, solution: str) -> bool:
        """Inject hCaptcha solution into the page."""
        try:
            page.evaluate(f"""
                () => {{
                    const textarea = document.querySelector('[name="h-captcha-response"], textarea[name="h-captcha-response"]');
                    if (textarea) {{
                        textarea.value = '{solution}';
                    }}

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
            logger.error(f"Failed to inject hCaptcha solution: {e}")
            return False

    def _inject_turnstile_solution(self, page: Page, solution: str) -> bool:
        """Inject Turnstile solution into the page."""
        try:
            page.evaluate(f"""
                () => {{
                    const input = document.querySelector('[name="cf-turnstile-response"], input[name="cf-turnstile-response"]');
                    if (input) {{
                        input.value = '{solution}';
                    }}
                }}
            """)
            logger.info("Turnstile solution injected")
            page.wait_for_timeout(2000)
            return True
        except Exception as e:
            logger.error(f"Failed to inject Turnstile solution: {e}")
            return False

    def _solve_with_capsolver(self, page: Page, url: str, captcha_info: dict) -> bool:
        """Solve CAPTCHA using Capsolver service."""
        captcha_type = captcha_info["type"]
        sitekey = captcha_info.get("sitekey")

        task_type_map = {
            "recaptcha_v2": "ReCaptchaV2TaskProxyLess",
            "hcaptcha": "HCaptchaTaskProxyLess",
            "turnstile": "AntiTurnstileTaskProxyLess"
        }

        if captcha_type not in task_type_map:
            logger.warning(f"Unsupported CAPTCHA type for Capsolver: {captcha_type}")
            return False

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{self.CAPSOLVER_API}/createTask",
                    json={
                        "clientKey": self.api_key,
                        "task": {
                            "type": task_type_map[captcha_type],
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
                while time.time() - start_time < self.timeout:
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
                        solution = result.get("solution", {}).get("gRecaptchaResponse") or \
                                   result.get("solution", {}).get("token")
                        if solution:
                            if captcha_type == "recaptcha_v2":
                                return self._inject_recaptcha_solution(page, solution)
                            elif captcha_type == "hcaptcha":
                                return self._inject_hcaptcha_solution(page, solution)
                            elif captcha_type == "turnstile":
                                return self._inject_turnstile_solution(page, solution)
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

    def _solve_perimeterx(self, page: Page, selector: str) -> bool:
        """Solve PerimeterX Press & Hold challenge - FAST mode."""
        logger.info("Attempting PerimeterX Press & Hold bypass (fast mode)...")

        try:
            button = page.locator(selector).first
            if not button.is_visible(timeout=2000):
                logger.warning("Press & Hold button not visible")
                return False

            box = button.bounding_box()
            if not box:
                logger.warning("Could not get button bounding box")
                return False

            center_x = box['x'] + box['width'] / 2
            center_y = box['y'] + box['height'] / 2

            logger.debug("Moving to button...")
            page.mouse.move(center_x + random.uniform(-5, 5), center_y + random.uniform(-3, 3), steps=8)
            time.sleep(random.uniform(0.05, 0.1))

            logger.info("Pressing and holding...")
            final_x = center_x + random.uniform(-3, 3)
            final_y = center_y + random.uniform(-2, 2)
            page.mouse.move(final_x, final_y)

            page.mouse.down()

            hold_duration = random.uniform(4.0, 6.0)
            hold_start = time.time()

            logger.debug(f"Holding for {hold_duration:.1f}s...")

            while time.time() - hold_start < hold_duration:
                new_x = final_x + random.gauss(0, 1.0)
                new_y = final_y + random.gauss(0, 1.0)
                new_x = max(box['x'] + 3, min(box['x'] + box['width'] - 3, new_x))
                new_y = max(box['y'] + 3, min(box['y'] + box['height'] - 3, new_y))
                page.mouse.move(new_x, new_y)
                time.sleep(random.uniform(0.04, 0.08))

            page.mouse.up()
            logger.info(f"Released after {time.time() - hold_start:.1f}s")

            page.wait_for_timeout(1500)

            try:
                if page.locator(selector).count() == 0:
                    logger.info("PerimeterX passed! (element gone)")
                    return True
                if not page.locator(selector).first.is_visible(timeout=500):
                    logger.info("PerimeterX passed! (element hidden)")
                    return True
            except Exception:
                pass

            title = page.title().lower()
            if "denied" not in title and "blocked" not in title and "confirm" not in title:
                logger.info("PerimeterX passed (title changed)")
                return True

            logger.warning("PerimeterX challenge not solved")
            return False

        except Exception as e:
            logger.error(f"PerimeterX bypass error: {e}")
            return False
