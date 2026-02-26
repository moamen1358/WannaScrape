"""
Browser management and anti-detection script injection.
Handles browser context creation, stealth mode, and fingerprint randomization.
"""

import random
import logging
from typing import Optional, Dict, Any
from playwright.sync_api import Browser, BrowserContext, Page
from playwright_stealth import Stealth

from app.config.constants import (
    CANVAS_NOISE_SCRIPT,
    WEBGL_SPOOF_SCRIPT,
    BROWSER_PATCHES_SCRIPT,
    COMMON_VIEWPORTS,
)
from app.services.user_agents import UserAgentManager
from app.utils.helpers import get_referrer
from app.core.fingerprint_manager import FingerprintManager

logger = logging.getLogger("scraper.browser")


class BrowserManager:
    """
    Manages browser instances with anti-detection features.
    """

    def __init__(self, config: dict):
        self.config = config
        self.ua_manager = UserAgentManager()

        # Initialize fingerprint manager
        fp_config = config.get("fingerprint", {})
        fp_enabled = fp_config.get("enabled", True)
        self.fingerprint_manager = FingerprintManager(enabled=fp_enabled)
        self.use_fingerprint_rotation = fp_enabled

        logger.info(
            f"Initialized with {self.ua_manager.get_total_user_agents()} user agents, "
            f"fingerprint rotation: {'ON' if fp_enabled else 'OFF'}"
        )

    def get_launch_args(self) -> list:
        """Get browser launch arguments for anti-detection."""
        return [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-features=CrossSiteDocumentBlockingIfIsolating',
            '--ignore-certificate-errors',
        ]

    def get_slow_mo(self) -> int:
        """Get randomized slow_mo value from config."""
        base_slow_mo = self.config.get("browser", {}).get("slow_mo", 100)
        return random.randint(int(base_slow_mo * 0.8), int(base_slow_mo * 1.2))

    def create_context(
        self,
        browser: Browser,
        url: str,
        proxy: Optional[dict] = None,
        storage_state_path: Optional[str] = None,
    ) -> tuple[BrowserContext, dict]:
        """
        Create a new browser context with anti-detection features.

        Returns:
            Tuple of (BrowserContext, profile_info dict)
        """
        fingerprint = None

        if self.use_fingerprint_rotation:
            # Use fingerprint manager for a consistent, rotating fingerprint
            fingerprint = self.fingerprint_manager.get_fingerprint()
            user_agent = fingerprint.user_agent
            viewport = fingerprint.viewport
            location = self.ua_manager.get_random_location(prefer_english=True)

            # Override location timezone with fingerprint timezone for consistency
            location["timezone_id"] = fingerprint.timezone

            # Get browser profile that matches the user agent (for logging)
            browser_profile = self.ua_manager.get_random_profile()
            browser_profile.user_agent = user_agent

            # Build context options from fingerprint
            context_options: Dict[str, Any] = {
                **self.fingerprint_manager.get_context_options(fingerprint),
                "geolocation": location["geo"],
                "permissions": ['geolocation'],
                "ignore_https_errors": True,
            }
        else:
            # Legacy mode: use UserAgentManager
            browser_profile = self.ua_manager.get_random_profile()
            user_agent = browser_profile.user_agent
            viewport = self.ua_manager.get_matching_viewport(browser_profile)
            location = self.ua_manager.get_random_location(prefer_english=True)

            context_options: Dict[str, Any] = {
                "user_agent": user_agent,
                "viewport": viewport,
                "locale": location["locale"],
                "timezone_id": location["timezone_id"],
                "geolocation": location["geo"],
                "permissions": ['geolocation'],
                "ignore_https_errors": True,
            }

        # Get matching HTTP headers
        http_headers = self.ua_manager.get_matching_headers(browser_profile)
        context_options["extra_http_headers"] = http_headers

        # Add referrer
        referrer = get_referrer(url)
        if referrer:
            context_options["extra_http_headers"]["Referer"] = referrer

        # Add storage state if provided
        if storage_state_path:
            from pathlib import Path
            if Path(storage_state_path).exists():
                context_options["storage_state"] = storage_state_path

        # Add proxy if provided
        if proxy:
            context_options["proxy"] = {
                "server": proxy["server"],
                "username": proxy.get("username"),
                "password": proxy.get("password"),
            }

        logger.debug(f"Browser profile: viewport={viewport}, locale={location.get('locale', 'en-US')}, tz={location.get('timezone_id', 'UTC')}")

        context = browser.new_context(**context_options)

        # Inject anti-detection scripts at context level
        self.inject_anti_detection_scripts(context, is_context=True)

        # Inject fingerprint overrides if using fingerprint rotation
        if fingerprint:
            override_script = self.fingerprint_manager.get_override_script(fingerprint)
            context.add_init_script(override_script)
            logger.debug("Injected fingerprint override scripts")

        profile_info = {
            "browser_profile": browser_profile,
            "viewport": viewport,
            "location": location,
            "referrer": referrer,
            "fingerprint": fingerprint,
        }

        return context, profile_info

    def setup_page(self, context: BrowserContext) -> Page:
        """
        Create and configure a new page with stealth mode.
        """
        page = context.new_page()

        # Apply stealth mode
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
        logger.debug("Stealth mode applied")

        # Inject anti-detection at page level for redundancy
        self.inject_anti_detection_scripts(page, is_context=False)

        # Block unnecessary resources
        block_list = self.config.get("anti_detection", {}).get("block_resources", ["image", "media", "font"])
        self._setup_resource_blocking(page, block_list)

        return page

    def inject_anti_detection_scripts(self, target, is_context: bool = False):
        """
        Inject all anti-detection JavaScript.

        Args:
            target: Either a BrowserContext or Page object
            is_context: If True, inject at context level (applies to all pages)
        """
        try:
            target_type = "context" if is_context else "page"

            target.add_init_script(CANVAS_NOISE_SCRIPT)
            target.add_init_script(WEBGL_SPOOF_SCRIPT)
            target.add_init_script(BROWSER_PATCHES_SCRIPT)

            # Import and inject advanced anti-detection
            try:
                from app.services.anti_detection import inject_advanced_anti_detection
                inject_advanced_anti_detection(target, is_context=is_context)
            except ImportError:
                pass

            logger.debug(f"Injected anti-detection scripts at {target_type} level")
        except Exception as e:
            logger.warning(f"Failed to inject anti-detection scripts: {e}")

    def _setup_resource_blocking(self, page: Page, block_list: list = None):
        """Block specified resource types to save bandwidth and speed up loading."""
        if block_list is None:
            block_list = ['image', 'media', 'font']

        # Also block known tracking/analytics domains for speed
        tracking_domains = [
            'google-analytics.com', 'googletagmanager.com',
            'facebook.net', 'doubleclick.net', 'hotjar.com',
            'newrelic.com', 'sentry.io', 'segment.io',
        ]

        def block_resources(route):
            resource_type = route.request.resource_type
            url = route.request.url

            # Block by resource type
            if resource_type in block_list:
                route.abort()
                return

            # Block tracking/analytics domains for speed
            for domain in tracking_domains:
                if domain in url:
                    route.abort()
                    return

            route.continue_()

        page.route("**/*", block_resources)
        logger.debug(f"Resource blocking enabled: {block_list} + tracking domains")


def get_random_viewport() -> dict:
    """Get a random but realistic viewport size."""
    return random.choice(COMMON_VIEWPORTS)
