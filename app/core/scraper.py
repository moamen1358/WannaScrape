"""
Main WebScraper class - production-ready web scraping with anti-detection.

This is the core scraping logic that uses the modular components:
- BrowserManager for browser setup and anti-detection
- CaptchaSolver for CAPTCHA handling
- ContentExtractor for article extraction
- ProxyManager for proxy rotation
"""

import time
import random
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

from ddgs import DDGS
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.captcha_solver import CaptchaSolver
from app.core.browser_manager import BrowserManager
from app.core.content_extractor import ContentExtractor, check_expired_link
from app.utils.proxy_manager import ProxyManager, load_proxies_from_file, mask_proxy
from app.utils.human_behavior import simulate_human_behavior
from app.utils.helpers import classify_error, save_failure_screenshot, load_config
from app.config.constants import POPUP_SELECTORS
from app.config.settings import get_data_dir
from app.logging.logger import get_scrape_logger, set_correlation_id

# Detection plugin system
from app.detections.handler import DetectionHandler

# Import advanced anti-detection if available
try:
    from app.core.rate_limiter import DomainRateLimiter
    from app.core.session_manager import SessionManager
    HAS_ADVANCED_ANTI_DETECTION = True
except ImportError:
    HAS_ADVANCED_ANTI_DETECTION = False

logger = logging.getLogger("scraper.core")


class ScrapeTimeoutError(Exception):
    """Raised when scrape operation exceeds maximum timeout."""

    def __init__(self, message: str, elapsed_time: float, screenshot_path: str = None):
        super().__init__(message)
        self.elapsed_time = elapsed_time
        self.screenshot_path = screenshot_path


class TimeoutChecker:
    """Tracks elapsed time and raises exception when timeout is exceeded."""

    def __init__(self, max_timeout: int, url: str):
        self.max_timeout = max_timeout
        self.url = url
        self.start_time = time.time()

    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    def remaining(self) -> float:
        """Get remaining time in seconds."""
        return max(0, self.max_timeout - self.elapsed())

    def check(self, stage: str = ""):
        """Check if timeout exceeded and raise if so."""
        elapsed = self.elapsed()
        if elapsed >= self.max_timeout:
            logger.error(f"TIMEOUT after {elapsed:.1f}s at stage: {stage}")
            raise ScrapeTimeoutError(
                f"Scrape timed out after {elapsed:.1f}s at stage: {stage}",
                elapsed_time=elapsed,
                screenshot_path=None
            )


class WebScraper:
    """
    Production-ready web scraper with comprehensive anti-detection.

    Features:
    - 50+ rotating user agents
    - 30+ location profiles
    - Canvas/WebGL fingerprint spoofing
    - Human behavior simulation
    - CAPTCHA solving (2captcha, capsolver)
    - Proxy rotation with health tracking
    - Session persistence
    - Comprehensive logging
    """

    def __init__(self, config_path: str = None, proxies: List[dict] = None):
        self.ddgs = DDGS()

        # Load configuration
        self.config = load_config(config_path)

        # Initialize managers
        self.browser_manager = BrowserManager(self.config)
        self.content_extractor = ContentExtractor()

        # Load proxies
        if proxies is None and self.config.get("proxies", {}).get("enabled"):
            from app.config.settings import get_config_dir
            proxy_file = self.config["proxies"].get("proxy_file", f"{get_config_dir()}/proxies.txt")
            proxies = load_proxies_from_file(proxy_file)

        self.proxy_manager = ProxyManager(proxies) if proxies else None

        # Initialize CAPTCHA solver (shared by detection plugins)
        captcha_config = self.config.get("captcha", {})
        self.captcha_solver = CaptchaSolver(captcha_config)

        # Initialize detection plugin system
        self.detection_handler = DetectionHandler(config=self.config)
        logger.info(f"Detection plugins loaded: {self.detection_handler.registry.list_all()}")

        # Initialize advanced features if available
        if HAS_ADVANCED_ANTI_DETECTION:
            rate_config = self.config.get("rate_limiting", {})
            self.domain_rate_limiter = DomainRateLimiter(
                max_requests_per_domain_per_hour=rate_config.get("max_requests_per_domain_per_hour", 30),
                min_delay_between_requests=rate_config.get("min_delay_between_requests", 5),
                max_delay_between_requests=rate_config.get("max_delay_between_requests", 15)
            )
            self.session_manager = SessionManager(sessions_dir=f"{get_data_dir()}/sessions")
        else:
            self.domain_rate_limiter = None
            self.session_manager = None

        # Rate limiting state
        self.last_request_time = 0
        self.min_request_interval = self.config.get("rate_limiting", {}).get("min_delay_between_requests", 5)

        # Initialize scrape logger
        self.scrape_logger = get_scrape_logger()

        logger.info("WebScraper initialized with anti-detection features")

    def _apply_rate_limiting(self):
        """Ensure minimum time between requests."""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed + random.uniform(0, 3)
                logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
        self.last_request_time = time.time()

    def _check_domain_rate_limit(self, url: str) -> tuple[bool, float, str]:
        """Check domain-level rate limiting."""
        if not self.domain_rate_limiter:
            return True, 0, ""
        return self.domain_rate_limiter.can_request(url)

    def _dismiss_popups(self, page) -> int:
        """Attempt to dismiss common popups and cookie banners."""
        dismissed = 0
        for selector in POPUP_SELECTORS:
            try:
                button = page.locator(selector).first
                if button.is_visible(timeout=1000):
                    button.click(timeout=2000)
                    page.wait_for_timeout(500)
                    dismissed += 1
                    logger.debug(f"Dismissed popup: {selector}")
            except Exception:
                continue

        # Try Escape key as fallback
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        return dismissed

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def extract_article(
        self,
        url: str,
        headless: Optional[bool] = None,
        storage_state_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract article content from a URL with full anti-detection.

        Args:
            url: The URL to scrape
            headless: Run browser in headless mode (default from config)
            storage_state_path: Path to browser state for session persistence

        Returns:
            Dict with article data or error information
        """
        if headless is None:
            headless = self.config.get("browser", {}).get("headless", True)

        # Check domain rate limit
        can_request, wait_time, reason = self._check_domain_rate_limit(url)
        if not can_request:
            logger.warning(f"Domain rate limit: {reason}")
            if wait_time > 300:
                return {
                    "error": f"Domain rate limit exceeded: {reason}",
                    "url": url,
                    "retry_after": wait_time
                }
            logger.info(f"Waiting {wait_time:.1f}s before request...")
            time.sleep(wait_time)

        # Apply rate limiting
        self._apply_rate_limiting()

        # Record request if using domain rate limiter
        if self.domain_rate_limiter:
            self.domain_rate_limiter.record_request(url)

        # Start logging session
        session_id = self.scrape_logger.start_session(url)

        max_retries = self.config.get("retry", {}).get("max_attempts", 3)
        max_timeout = self.config.get("max_scrape_timeout", 120)
        last_error = "Unknown error"
        proxy = None
        profile_info = {}

        # Log timeout
        self.scrape_logger.log_timeout(session_id, max_timeout)

        # Check for saved session
        if storage_state_path is None and self.session_manager:
            if self.session_manager.should_use_session(url):
                storage_state_path = self.session_manager.get_session(url)

        for attempt in range(max_retries):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
                time.sleep(random.uniform(3, 8))

                # Switch proxy on retry
                if self.proxy_manager and proxy:
                    self.proxy_manager.mark_failed(proxy, cooldown_seconds=60)

            timeout_checker = TimeoutChecker(max_timeout, url)

            try:
                with sync_playwright() as p:
                    # Launch browser
                    browser_start = time.time()
                    slow_mo = self.browser_manager.get_slow_mo()
                    browser = p.chromium.launch(
                        headless=headless,
                        slow_mo=slow_mo,
                        args=self.browser_manager.get_launch_args()
                    )
                    browser_launch_time = time.time() - browser_start

                    # Log browser launch
                    self.scrape_logger.log_browser_launch(session_id, headless, slow_mo, browser_launch_time)

                    # Get proxy
                    if self.proxy_manager:
                        proxy = self.proxy_manager.get_proxy()
                        if proxy:
                            logger.debug(f"Using proxy: {mask_proxy(proxy)}")

                    # Create context with anti-detection
                    context, profile_info = self.browser_manager.create_context(
                        browser, url, proxy, storage_state_path
                    )

                    # Log detailed browser profile and fingerprint
                    viewport = profile_info.get("viewport", {})
                    location = profile_info.get("location", {})
                    browser_profile = profile_info.get("browser_profile")

                    self.scrape_logger.log_browser_profile(
                        session_id,
                        viewport,
                        location.get("locale", "en-US"),
                        location.get("timezone", "UTC")
                    )

                    # Log session start with fingerprint
                    fingerprint = {
                        "browser": f"{browser_profile.browser.upper()} v{browser_profile.version}" if browser_profile else "N/A",
                        "user_agent": browser_profile.user_agent if browser_profile else "N/A",
                        "viewport": viewport,
                        "location": location,
                        "proxy": mask_proxy(proxy) if proxy else "Direct (no proxy)",
                        "referrer": profile_info.get("referrer", "https://www.google.com/")
                    }
                    self.scrape_logger.log_session_start(session_id, attempt + 1, max_retries, fingerprint)

                    # Log anti-detection
                    self.scrape_logger.log_anti_detection(session_id, "context")

                    # Setup page
                    page = self.browser_manager.setup_page(context)

                    # Log stealth mode and page-level anti-detection
                    self.scrape_logger.log_stealth_mode(session_id)
                    self.scrape_logger.log_anti_detection(session_id, "page")

                    timeout_checker.check("browser_setup")

                    # Navigate with strategies
                    strategies = self.config.get("strategies", [
                        {"wait": "domcontentloaded", "timeout": 40000, "sleep": 4}
                    ])

                    for strategy in strategies:
                        try:
                            # Log navigation start
                            self.scrape_logger.log_navigation_start(
                                session_id,
                                strategy["wait"],
                                strategy["timeout"] / 1000
                            )

                            nav_start = time.time()
                            page.goto(url, wait_until=strategy["wait"], timeout=strategy["timeout"])
                            final_url = page.url
                            page_title = page.title()
                            nav_time = time.time() - nav_start

                            # Log page loaded
                            self.scrape_logger.log_page_loaded(session_id, final_url, page_title, nav_time)
                            timeout_checker.check("page_loaded")

                            # Wait for content
                            page.wait_for_timeout(1000)

                            # Dismiss popups
                            self._dismiss_popups(page)
                            timeout_checker.check("popup_handling")

                            # Handle bot detection using plugin system
                            detection_result = self.detection_handler.handle_detections(
                                page, url, max_solve_attempts=2
                            )

                            if detection_result.detected_any:
                                # Log what was detected
                                for det_name in detection_result.detections:
                                    if det_name == "cloudflare":
                                        self.scrape_logger.log_cloudflare(
                                            session_id, True, int(timeout_checker.remaining())
                                        )
                                    else:
                                        solved = detection_result.solve_results.get(det_name, False)
                                        self.scrape_logger.log_captcha(session_id, det_name, True, solved)

                                # If still blocked after solving attempts, retry
                                if detection_result.blocked:
                                    logger.warning(f"Still blocked by: {detection_result.detections}")
                                    continue

                                # Wait for page to settle after solving
                                try:
                                    page.wait_for_load_state('networkidle', timeout=10000)
                                except Exception:
                                    pass

                            timeout_checker.check("detection_handling")

                            # Human behavior simulation
                            self.scrape_logger.log_human_behavior_start(session_id)
                            human_start = time.time()
                            behavior_stats = simulate_human_behavior(page, config=self.config)
                            human_duration = time.time() - human_start

                            # Log human behavior completion
                            self.scrape_logger.log_human_behavior(
                                session_id,
                                behavior_stats.get("mouse_moves", 2),
                                behavior_stats.get("scrolls", 2),
                                human_duration,
                                viewport
                            )
                            timeout_checker.check("human_behavior")

                            # Check for access denied
                            page_content = page.content()
                            page_title = page.title()
                            error_class = classify_error("", page_content, page_title)

                            if error_class["likely_ban"] and len(page_content) < 15000:
                                screenshot_path = save_failure_screenshot(page, url, error_class["type"], "Access denied detected")
                                if self.proxy_manager and proxy:
                                    self.proxy_manager.mark_failed(proxy, cooldown_seconds=180)
                                self.scrape_logger.log_error(
                                    session_id,
                                    error_class["type"],
                                    "Access denied - likely bot detection",
                                    likely_ban=True,
                                    page_url=page.url,
                                    page_title=page_title,
                                    html_size=len(page_content),
                                    recommendation=error_class["details"],
                                    screenshot_path=screenshot_path
                                )
                                raise Exception(f"Access Denied - Type: {error_class['type']}")

                            # Extract content
                            extraction_start = time.time()
                            extraction = self.content_extractor.extract(page)
                            extraction_time = time.time() - extraction_start

                            if extraction["success"]:
                                # Mark proxy as successful
                                if self.proxy_manager and proxy:
                                    self.proxy_manager.mark_success(proxy)

                                # Save session
                                if self.session_manager:
                                    try:
                                        self.session_manager.save_session(context, url)
                                    except Exception:
                                        pass

                                # Log content metrics
                                result_data = extraction["data"]
                                html_content = page.content()
                                self.scrape_logger.log_content_metrics(
                                    session_id,
                                    result_data.get("title", "N/A"),
                                    final_url,
                                    len(html_content),
                                    result_data.get("text", ""),
                                    extraction["method"]
                                )

                                # Add profile info to result
                                result = extraction["data"]
                                result["html_size"] = len(html_content)
                                result["extraction_method"] = extraction["method"]
                                result["final_url"] = final_url
                                if profile_info.get("browser_profile"):
                                    bp = profile_info["browser_profile"]
                                    result["user_agent_used"] = f"{bp.browser}/{bp.version}"
                                if profile_info.get("location"):
                                    result["location_used"] = profile_info["location"].get("name", "unknown")

                                browser.close()
                                self.scrape_logger.complete_session(session_id, True, result, extraction_time)
                                return result

                            # Extraction failed
                            break

                        except ScrapeTimeoutError:
                            raise
                        except Exception as e:
                            last_error = str(e)
                            if "Access Denied" in last_error:
                                raise
                            continue

                    # Check for expired link
                    if check_expired_link(page.content()):
                        screenshot_path = save_failure_screenshot(page, url, "expired_link", "Google News link expired")
                        browser.close()
                        result = {
                            "error": "Google News article link expired or unavailable.",
                            "error_type": "expired_link",
                            "final_url": page.url,
                            "screenshot": screenshot_path
                        }
                        self.scrape_logger.complete_session(session_id, False, result, screenshot_path=screenshot_path)
                        return result

                    browser.close()

            except ScrapeTimeoutError as timeout_err:
                # Try to capture screenshot before browser closes
                screenshot_path = None
                try:
                    if 'page' in locals() and page:
                        screenshot_path = save_failure_screenshot(page, url, "timeout", f"Timed out at {timeout_err.elapsed_time:.1f}s")
                except Exception:
                    pass

                self.scrape_logger.log_error(
                    session_id,
                    "timeout",
                    str(timeout_err),
                    likely_ban=False,
                    page_url=url,
                    screenshot_path=screenshot_path
                )
                self.scrape_logger.complete_session(
                    session_id,
                    False,
                    {"error_type": "timeout", "error": str(timeout_err)},
                    screenshot_path=screenshot_path
                )
                return {
                    "error": f"Scrape timed out after {timeout_err.elapsed_time:.1f}s",
                    "error_type": "timeout",
                    "likely_ban": False,
                    "final_url": url,
                    "screenshot": screenshot_path
                }

            except Exception as e:
                last_error = str(e)
                error_class = classify_error(last_error)

                # Try to capture screenshot on exception
                screenshot_path = None
                try:
                    if 'page' in locals() and page:
                        page_title = page.title() if page else None
                        html_size = len(page.content()) if page else None
                        screenshot_path = save_failure_screenshot(page, url, error_class["type"], last_error[:100])
                except Exception:
                    page_title = None
                    html_size = None

                self.scrape_logger.log_error(
                    session_id,
                    error_class["type"],
                    last_error,
                    likely_ban=error_class["likely_ban"],
                    page_url=url,
                    page_title=page_title if 'page_title' in locals() else None,
                    html_size=html_size if 'html_size' in locals() else None,
                    recommendation=error_class["details"],
                    screenshot_path=screenshot_path
                )

                if attempt == max_retries - 1:
                    break

        # All retries failed - use the last screenshot if we captured one
        error_class = classify_error(last_error)
        last_screenshot = screenshot_path if 'screenshot_path' in locals() else None
        result = {
            "error": f"Failed after {max_retries} attempts. Last error: {last_error}",
            "error_type": error_class["type"],
            "likely_ban": error_class["likely_ban"],
            "recommendation": error_class["details"],
            "final_url": url,
            "screenshot": last_screenshot
        }
        self.scrape_logger.complete_session(
            session_id,
            False,
            result,
            screenshot_path=last_screenshot,
            retries_attempted=max_retries
        )
        return result

    def find_source_from_text(self, text: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for the source of a text snippet using DuckDuckGo.

        Args:
            text: The text snippet to search for
            num_results: Number of results to return

        Returns:
            List of potential source URLs
        """
        results = []
        try:
            query = f'"{text}"' if len(text) < 200 else text
            search_results = self.ddgs.text(query, region='us-en', max_results=num_results)
            if search_results:
                for res in search_results:
                    results.append({
                        "title": res.get("title"),
                        "url": res.get("href"),
                        "description": res.get("body")
                    })
            return results
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]

    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return self.scrape_logger.get_stats()

    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection plugin statistics."""
        if self.detection_handler:
            return self.detection_handler.get_stats()
        return {"error": "Detection plugins not available"}
