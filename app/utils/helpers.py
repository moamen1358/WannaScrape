"""
Helper utilities for the scraper.
"""

import os
import json
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from urllib.parse import urlparse

logger = logging.getLogger("scraper.helpers")


def get_referrer(target_url: str) -> Optional[str]:
    """Generate a realistic referrer based on target URL."""
    domain = urlparse(target_url).netloc

    referrers = [
        (f"https://www.google.com/search?q={domain.replace('.', '+')}", 0.4),
        ("https://www.google.com/", 0.2),
        ("https://news.google.com/", 0.15),
        (None, 0.15),
        ("https://t.co/", 0.05),
        ("https://www.facebook.com/", 0.05),
    ]

    r = random.random()
    cumulative = 0
    for ref, weight in referrers:
        cumulative += weight
        if r <= cumulative:
            return ref
    return None


def classify_error(error_msg: str, page_content: str = "", page_title: str = "") -> dict:
    """Classify error type for debugging and ban detection."""
    from app.config.constants import ACCESS_DENIED_INDICATORS, CAPTCHA_PHRASES

    error_lower = error_msg.lower()
    title_lower = page_title.lower() if page_title else ""
    content_lower = page_content[:2000].lower() if page_content else ""

    classification = {
        "type": "unknown",
        "likely_ban": False,
        "retry_recommended": True,
        "details": ""
    }

    # Timeout errors
    if any(x in error_lower for x in ["timeout", "timed out", "timeouterror"]):
        classification["type"] = "timeout"
        classification["details"] = "Request timed out"
        return classification

    # Network errors
    if any(x in error_lower for x in ["connection", "network", "dns", "refused"]):
        classification["type"] = "network"
        classification["details"] = "Network connection issue"
        return classification

    # Cloudflare
    if "cloudflare" in content_lower or "cf-" in content_lower:
        classification["type"] = "cloudflare"
        classification["retry_recommended"] = True
        classification["details"] = "Cloudflare challenge"
        return classification

    # CAPTCHA detection
    if any(x in content_lower for x in CAPTCHA_PHRASES):
        classification["type"] = "bot_detection"
        classification["likely_ban"] = True
        classification["retry_recommended"] = True
        classification["details"] = "CAPTCHA or bot detection"
        return classification

    # Access denied
    if any(x in title_lower for x in ACCESS_DENIED_INDICATORS):
        classification["type"] = "access_denied"
        classification["likely_ban"] = True
        classification["retry_recommended"] = False
        classification["details"] = "Access denied by site"
        return classification

    return classification


def save_failure_screenshot(page, url: str, reason: str, extra_info: str = "") -> Optional[str]:
    """Save screenshot and metadata when scraping fails."""
    try:
        screenshots_dir = Path("data/screenshots") / datetime.now().strftime("%Y-%m-%d")
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        domain = urlparse(url).netloc.replace(".", "_")
        timestamp = datetime.now().strftime("%H%M%S")
        safe_reason = reason.replace(" ", "_")[:30]

        base_name = f"{timestamp}_{safe_reason}_{domain}"[:80]
        png_path = screenshots_dir / f"{base_name}.png"
        json_path = screenshots_dir / f"{base_name}.json"

        page.screenshot(path=str(png_path), full_page=False)

        metadata = {
            "url": url,
            "reason": reason,
            "extra_info": extra_info,
            "timestamp": datetime.now().isoformat(),
            "page_title": page.title() if page else None,
        }
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Screenshot saved: {png_path}")
        return str(png_path)
    except Exception as e:
        logger.warning(f"Failed to save screenshot: {e}")
        return None


def load_config(config_path: str = "config/config.json") -> dict:
    """Load configuration from JSON file."""
    from app.config.constants import DEFAULT_CONFIG

    try:
        with open(config_path) as f:
            config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
    except FileNotFoundError:
        logger.warning(f"Config not found at {config_path}, using defaults")
        return DEFAULT_CONFIG
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config: {e}")
        return DEFAULT_CONFIG
