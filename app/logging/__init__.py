"""
Logging module for the web scraper.
"""

from app.logging.logger import (
    setup_logging,
    get_scrape_logger,
    get_correlation_id,
    set_correlation_id,
    ScrapeLogger,
    ScrapeSession,
)

__all__ = [
    "setup_logging",
    "get_scrape_logger",
    "get_correlation_id",
    "set_correlation_id",
    "ScrapeLogger",
    "ScrapeSession",
]
