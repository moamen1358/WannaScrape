"""
Core scraping modules.
"""

from app.core.scraper import WebScraper, ScrapeTimeoutError
from app.core.captcha_solver import CaptchaSolver
from app.core.browser_manager import BrowserManager
from app.core.content_extractor import ContentExtractor
from app.core.exceptions import (
    ScraperError,
    TimeoutError,
    AccessDeniedError,
    CloudflareError,
    CaptchaError,
    ContentExtractionError,
    NetworkError,
    ProxyError,
    ExpiredLinkError,
    RateLimitError,
)

__all__ = [
    "WebScraper",
    "ScrapeTimeoutError",
    "CaptchaSolver",
    "BrowserManager",
    "ContentExtractor",
    "ScraperError",
    "TimeoutError",
    "AccessDeniedError",
    "CloudflareError",
    "CaptchaError",
    "ContentExtractionError",
    "NetworkError",
    "ProxyError",
    "ExpiredLinkError",
    "RateLimitError",
]
