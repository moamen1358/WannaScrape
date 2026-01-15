"""
Prometheus metrics for monitoring the web scraper.

Exposes metrics at /metrics endpoint for Prometheus scraping.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time
from typing import Callable, Any


# Application info
APP_INFO = Info('scraper', 'Web scraper application information')
APP_INFO.info({
    'version': '2.0.0',
    'python_version': '3.10',
})

# Request metrics
REQUESTS_TOTAL = Counter(
    'scraper_requests_total',
    'Total number of scrape requests',
    ['endpoint', 'status']
)

REQUESTS_IN_PROGRESS = Gauge(
    'scraper_requests_in_progress',
    'Number of requests currently being processed',
    ['endpoint']
)

REQUEST_DURATION = Histogram(
    'scraper_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint'],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
)

# Scraping metrics
SCRAPE_TOTAL = Counter(
    'scraper_scrapes_total',
    'Total number of scrape attempts',
    ['status', 'error_type']
)

SCRAPE_DURATION = Histogram(
    'scraper_scrape_duration_seconds',
    'Scrape operation duration in seconds',
    buckets=[1.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0, 300.0]
)

CONTENT_SIZE = Histogram(
    'scraper_content_size_bytes',
    'Size of extracted content in bytes',
    buckets=[1000, 5000, 10000, 50000, 100000, 500000]
)

# Anti-detection metrics
CLOUDFLARE_CHALLENGES = Counter(
    'scraper_cloudflare_challenges_total',
    'Total Cloudflare challenges encountered',
    ['status']
)

CAPTCHA_ATTEMPTS = Counter(
    'scraper_captcha_attempts_total',
    'Total CAPTCHA solving attempts',
    ['status']
)

RATE_LIMIT_HITS = Counter(
    'scraper_rate_limit_hits_total',
    'Total rate limit hits'
)

# Browser metrics
BROWSER_SESSIONS = Gauge(
    'scraper_browser_sessions_active',
    'Number of active browser sessions'
)

POPUPS_DISMISSED = Counter(
    'scraper_popups_dismissed_total',
    'Total popups/cookie banners dismissed'
)

# Proxy metrics
PROXY_REQUESTS = Counter(
    'scraper_proxy_requests_total',
    'Total requests through proxies',
    ['proxy_status']
)

# Search metrics
SEARCH_TOTAL = Counter(
    'scraper_searches_total',
    'Total search requests',
    ['status']
)


def track_request(endpoint: str) -> Callable:
    """Decorator to track request metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            REQUESTS_IN_PROGRESS.labels(endpoint=endpoint).inc()
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                REQUESTS_IN_PROGRESS.labels(endpoint=endpoint).dec()
                REQUESTS_TOTAL.labels(endpoint=endpoint, status=status).inc()
                REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            REQUESTS_IN_PROGRESS.labels(endpoint=endpoint).inc()
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                REQUESTS_IN_PROGRESS.labels(endpoint=endpoint).dec()
                REQUESTS_TOTAL.labels(endpoint=endpoint, status=status).inc()
                REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def record_scrape(status: str, error_type: str = "none", duration: float = 0, content_size: int = 0):
    """Record scrape metrics."""
    SCRAPE_TOTAL.labels(status=status, error_type=error_type).inc()
    if duration > 0:
        SCRAPE_DURATION.observe(duration)
    if content_size > 0:
        CONTENT_SIZE.observe(content_size)


def record_cloudflare(status: str):
    """Record Cloudflare challenge metrics."""
    CLOUDFLARE_CHALLENGES.labels(status=status).inc()


def record_captcha(status: str):
    """Record CAPTCHA attempt metrics."""
    CAPTCHA_ATTEMPTS.labels(status=status).inc()


def record_rate_limit():
    """Record rate limit hit."""
    RATE_LIMIT_HITS.inc()


def record_popup_dismissed():
    """Record popup dismissal."""
    POPUPS_DISMISSED.inc()


def record_proxy_request(status: str):
    """Record proxy request."""
    PROXY_REQUESTS.labels(proxy_status=status).inc()


def record_search(status: str):
    """Record search request."""
    SEARCH_TOTAL.labels(status=status).inc()


def get_metrics() -> bytes:
    """Generate Prometheus metrics output."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST
