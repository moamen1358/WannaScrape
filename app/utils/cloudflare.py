"""
Cloudflare challenge detection and bypass.
"""

import time
import logging

logger = logging.getLogger("scraper.cloudflare")


def is_cloudflare_challenge(page) -> bool:
    """
    Smart Cloudflare challenge detection.
    Only triggers on REAL Cloudflare challenge pages, not articles that mention Cloudflare.
    """
    try:
        cf_selectors = [
            "#challenge-running",
            "#challenge-stage",
            ".cf-browser-verification",
            "#cf-challenge-running",
            "#cf-wrapper",
            "#cf-hcaptcha-container",
            ".cf-turnstile",
        ]

        for selector in cf_selectors:
            if page.locator(selector).count() > 0:
                logger.debug(f"Cloudflare detected via selector: {selector}")
                return True

        page_title = (page.title() or "").lower()
        cf_title_indicators = ["just a moment", "attention required", "checking your browser"]
        if any(indicator in page_title for indicator in cf_title_indicators):
            logger.debug(f"Cloudflare detected via title: {page_title}")
            return True

        page_content = page.content() or ""
        content_length = len(page_content)

        if content_length < 50000:
            page_text = (page.text_content("body") or "").lower()

            challenge_phrases = [
                "checking your browser before",
                "this process is automatic",
                "you will be redirected",
                "ray id:",
                "enable javascript and cookies",
                "ddos protection by",
                "please stand by",
                "verify you are human",
            ]

            for phrase in challenge_phrases:
                if phrase in page_text:
                    logger.debug(f"Cloudflare detected via phrase: {phrase}")
                    return True

        return False
    except Exception as e:
        logger.debug(f"Cloudflare detection error: {e}")
        return False


def wait_for_cloudflare(page, max_wait: int = 45) -> bool:
    """Wait for Cloudflare challenge to resolve."""
    if not is_cloudflare_challenge(page):
        return True

    logger.info("Cloudflare challenge detected, waiting...")
    start = time.time()

    while time.time() - start < max_wait:
        time.sleep(3)

        if not is_cloudflare_challenge(page):
            logger.info(f"Cloudflare challenge passed after {time.time() - start:.1f}s")
            return True

        logger.debug(f"Still waiting for Cloudflare... ({time.time() - start:.1f}s)")

    logger.warning(f"Cloudflare challenge timeout after {max_wait}s")
    return False
