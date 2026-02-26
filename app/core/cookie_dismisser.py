"""
Auto-dismiss cookie consent banners that block content extraction.

Handles popular consent management platforms:
- OneTrust, Cookiebot, CookieConsent, Osano, TrustArc
- GDPR/CCPA banners
- Generic cookie popups

Uses a fast-fail approach: tries each selector briefly (500ms)
and stops as soon as one works.
"""

import logging
from playwright.sync_api import Page

logger = logging.getLogger("scraper.cookies")

# Cookie accept button selectors — ordered by specificity (most specific first)
COOKIE_ACCEPT_SELECTORS = [
    # ── Popular consent platforms ──
    "#onetrust-accept-btn-handler",                                  # OneTrust
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",       # Cookiebot
    ".osano-cm-accept-all",                                          # Osano
    "#truste-consent-button",                                        # TrustArc
    "[data-tid='banner-accept']",                                    # Quantcast
    "#sp-cc-accept",                                                  # Amazon SP

    # ── ID-based selectors ──
    "#cookie-accept",
    "#accept-cookies",
    "#cookieAcceptButton",
    "#gdpr-cookie-accept",
    "#cookies-accept",
    "#cookie-consent-accept",
    "#btn-cookie-accept",

    # ── Class-based selectors ──
    ".cc-accept",
    ".cc-btn.cc-allow",
    ".cookie-accept-btn",
    ".cookie-accept",
    ".gdpr-accept",
    ".js-accept-cookies",
    ".accept-cookies-btn",
    ".cookie-consent__accept",

    # ── Data-attribute selectors ──
    "button[data-cookie-accept]",
    "[data-testid='cookie-accept']",
    "[data-action='accept-cookies']",
    "button[data-cookiebanner='accept_button']",

    # ── Text-based selectors (broader, try last) ──
    "button:has-text('Accept All')",
    "button:has-text('Accept all')",
    "button:has-text('Accept all cookies')",
    "button:has-text('Accept All Cookies')",
    "button:has-text('Accept Cookies')",
    "button:has-text('Accept Optional Cookies')",
    "button:has-text('Allow all')",
    "button:has-text('Allow All')",
    "button:has-text('Allow All Cookies')",
    "button:has-text('I Accept')",
    "button:has-text('I Agree')",
    "button:has-text('Got it')",
    "button:has-text('Agree')",
    "button:has-text('Agree and proceed')",
    "a:has-text('Accept All')",
    "a:has-text('Accept Cookies')",
    "a:has-text('I Agree')",
]

# Reject/close buttons (for sites where we want to reject optional cookies)
COOKIE_REJECT_SELECTORS = [
    "#onetrust-reject-all-handler",
    "button:has-text('Reject All')",
    "button:has-text('Reject Optional Cookies')",
    "button:has-text('Only Necessary')",
    "button:has-text('Decline')",
    ".cc-deny",
]


def dismiss_cookie_banner(page: Page, timeout_per_selector: int = 500) -> bool:
    """
    Try to dismiss any cookie consent banner on the page.

    Tries specific selectors first (OneTrust, Cookiebot, etc.),
    then falls back to text-based matching. Stops on first success.

    Args:
        page: Playwright page object
        timeout_per_selector: Max ms to wait for each selector visibility check

    Returns:
        True if a banner was dismissed, False otherwise
    """
    for selector in COOKIE_ACCEPT_SELECTORS:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=timeout_per_selector):
                btn.click(timeout=2000)
                logger.info(f"🍪 Cookie banner dismissed: {selector}")
                page.wait_for_timeout(300)
                return True
        except Exception:
            continue

    return False


def dismiss_cookie_banner_aggressive(page: Page) -> bool:
    """
    More aggressive cookie dismissal — tries accept first, then reject, then close.

    Use this when the standard dismiss doesn't work.

    Args:
        page: Playwright page object

    Returns:
        True if any banner was dismissed
    """
    # Try accepting first
    if dismiss_cookie_banner(page):
        return True

    # Try rejecting (still gets rid of the banner)
    for selector in COOKIE_REJECT_SELECTORS:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=500):
                btn.click(timeout=2000)
                logger.info(f"🍪 Cookie banner rejected: {selector}")
                page.wait_for_timeout(300)
                return True
        except Exception:
            continue

    # Try generic close buttons on cookie-related elements
    close_selectors = [
        "[class*='cookie'] button[class*='close']",
        "[class*='cookie'] [aria-label='Close']",
        "[class*='consent'] button[class*='close']",
        "[class*='consent'] [aria-label='Close']",
        "[id*='cookie'] button[class*='close']",
        ".cookie-banner .close",
        ".consent-banner .close",
    ]
    for selector in close_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=300):
                btn.click(timeout=1000)
                logger.info(f"🍪 Cookie banner closed: {selector}")
                page.wait_for_timeout(300)
                return True
        except Exception:
            continue

    return False
