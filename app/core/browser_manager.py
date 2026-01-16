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

logger = logging.getLogger("scraper.browser")


class BrowserManager:
    """
    Manages browser instances with anti-detection features.
    """

    def __init__(self, config: dict):
        self.config = config
        self.ua_manager = UserAgentManager()
        logger.info(f"Initialized with {self.ua_manager.get_total_user_agents()} user agents")

    def get_launch_args(self) -> list:
        """Get browser launch arguments for anti-detection."""
        return [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
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
        # Get a complete browser profile with consistent fingerprint
        browser_profile = self.ua_manager.get_random_profile()
        user_agent = browser_profile.user_agent

        # Get OS-matching viewport
        viewport = self.ua_manager.get_matching_viewport(browser_profile)
        location = self.ua_manager.get_random_location(prefer_english=True)

        # Get matching HTTP headers
        http_headers = self.ua_manager.get_matching_headers(browser_profile)

        # Build context options
        context_options: Dict[str, Any] = {
            "user_agent": user_agent,
            "viewport": viewport,
            "locale": location["locale"],
            "timezone_id": location["timezone_id"],
            "geolocation": location["geo"],
            "permissions": ['geolocation'],
            "extra_http_headers": http_headers,
        }

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

        logger.debug(f"Browser profile: viewport={viewport}, locale={location['locale']}, tz={location['timezone_id']}")

        context = browser.new_context(**context_options)

        # Inject anti-detection scripts at context level
        self.inject_anti_detection_scripts(context, is_context=True)

        profile_info = {
            "browser_profile": browser_profile,
            "viewport": viewport,
            "location": location,
            "referrer": referrer,
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
        self._setup_resource_blocking(page)

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

    def _setup_resource_blocking(self, page: Page):
        """Block images, media, and fonts to save bandwidth."""
        def block_resources(route):
            resource_type = route.request.resource_type
            if resource_type in ['image', 'media', 'font']:
                route.abort()
            else:
                route.continue_()

        page.route("**/*", block_resources)
        logger.debug("Resource blocking enabled (images, media, fonts)")


def get_random_viewport() -> dict:
    """Get a random but realistic viewport size."""
    return random.choice(COMMON_VIEWPORTS)
