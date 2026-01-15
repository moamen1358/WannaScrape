"""
Monitoring and metrics for the web scraper.
"""

from app.monitoring.metrics import (
    track_request,
    record_scrape,
    record_cloudflare,
    record_captcha,
    record_rate_limit,
    record_popup_dismissed,
    record_proxy_request,
    record_search,
    get_metrics,
    get_metrics_content_type,
    REQUESTS_TOTAL,
    REQUESTS_IN_PROGRESS,
    REQUEST_DURATION,
    SCRAPE_TOTAL,
    SCRAPE_DURATION,
    BROWSER_SESSIONS,
)

__all__ = [
    "track_request",
    "record_scrape",
    "record_cloudflare",
    "record_captcha",
    "record_rate_limit",
    "record_popup_dismissed",
    "record_proxy_request",
    "record_search",
    "get_metrics",
    "get_metrics_content_type",
    "REQUESTS_TOTAL",
    "REQUESTS_IN_PROGRESS",
    "REQUEST_DURATION",
    "SCRAPE_TOTAL",
    "SCRAPE_DURATION",
    "BROWSER_SESSIONS",
]
