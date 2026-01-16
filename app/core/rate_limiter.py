"""
Domain Rate Limiter
===================
Track request frequency per domain to avoid detection.
"""

import random
import time
import logging
from urllib.parse import urlparse

logger = logging.getLogger("scraper.rate_limiter")


class DomainRateLimiter:
    """
    Track request frequency per domain to avoid detection.

    Features:
    - Hourly request limits per domain
    - Minimum delays between requests
    - Dynamic delay scaling based on request frequency

    Usage:
        limiter = DomainRateLimiter()

        can_request, wait_time, reason = limiter.can_request(url)
        if not can_request:
            time.sleep(wait_time)

        # Make request...
        limiter.record_request(url)
    """

    def __init__(
        self,
        max_requests_per_domain_per_hour: int = 30,
        min_delay_between_requests: float = 5.0,
        max_delay_between_requests: float = 15.0
    ):
        """
        Initialize the rate limiter.

        Args:
            max_requests_per_domain_per_hour: Maximum requests allowed per domain per hour
            min_delay_between_requests: Minimum seconds between requests to same domain
            max_delay_between_requests: Maximum seconds for random delay calculation
        """
        self.max_requests_per_hour = max_requests_per_domain_per_hour
        self.min_delay = min_delay_between_requests
        self.max_delay = max_delay_between_requests

        # {domain: [timestamp1, timestamp2, ...]}
        self.domain_requests: dict = {}

        # {domain: last_request_timestamp}
        self.last_request: dict = {}

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc.lower()

    def _clean_old_requests(self, domain: str):
        """Remove requests older than 1 hour."""
        cutoff = time.time() - 3600  # 1 hour ago
        if domain in self.domain_requests:
            self.domain_requests[domain] = [
                ts for ts in self.domain_requests[domain] if ts > cutoff
            ]

    def can_request(self, url: str) -> tuple:
        """
        Check if we can make a request to this domain.

        Args:
            url: The URL to check

        Returns:
            Tuple of (can_request: bool, wait_time: float, reason: str)
        """
        domain = self._extract_domain(url)
        self._clean_old_requests(domain)

        now = time.time()

        # Check hourly limit
        requests_in_hour = len(self.domain_requests.get(domain, []))
        if requests_in_hour >= self.max_requests_per_hour:
            oldest = min(self.domain_requests[domain]) if self.domain_requests.get(domain) else now
            wait_time = 3600 - (now - oldest) + random.uniform(60, 300)
            return False, wait_time, f"Rate limit: {requests_in_hour}/{self.max_requests_per_hour} requests to {domain} in last hour"

        # Check minimum interval
        last = self.last_request.get(domain, 0)
        elapsed = now - last
        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed + random.uniform(0, 3)
            return False, wait_time, f"Too soon since last request to {domain}"

        return True, 0, "OK"

    def record_request(self, url: str):
        """
        Record that a request was made.

        Args:
            url: The URL that was requested
        """
        domain = self._extract_domain(url)
        now = time.time()

        if domain not in self.domain_requests:
            self.domain_requests[domain] = []

        self.domain_requests[domain].append(now)
        self.last_request[domain] = now

        logger.debug(f"Recorded request to {domain}. Total in last hour: {len(self.domain_requests[domain])}")

    def get_recommended_delay(self, url: str) -> float:
        """
        Get recommended delay before making request.

        Scales delay based on how many requests have been made recently.

        Args:
            url: The URL to get delay for

        Returns:
            Recommended delay in seconds
        """
        domain = self._extract_domain(url)
        self._clean_old_requests(domain)

        requests_in_hour = len(self.domain_requests.get(domain, []))

        # Scale delay based on request frequency
        # More requests = longer delays
        base_delay = random.uniform(self.min_delay, self.max_delay)

        if requests_in_hour > 10:
            # Add extra delay if we've made many requests
            extra_delay = (requests_in_hour - 10) * 2
            base_delay += min(extra_delay, 60)  # Cap at 60s extra

        return base_delay

    def get_stats(self, url: str = None) -> dict:
        """
        Get rate limiting statistics.

        Args:
            url: Optional URL to get domain-specific stats

        Returns:
            Dict with statistics
        """
        if url:
            domain = self._extract_domain(url)
            self._clean_old_requests(domain)
            return {
                "domain": domain,
                "requests_last_hour": len(self.domain_requests.get(domain, [])),
                "max_per_hour": self.max_requests_per_hour,
                "last_request": self.last_request.get(domain)
            }

        return {
            "domains_tracked": len(self.domain_requests),
            "total_requests_last_hour": sum(len(v) for v in self.domain_requests.values()),
            "max_per_hour_per_domain": self.max_requests_per_hour
        }
