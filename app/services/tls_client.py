"""
TLS/JA3 Fingerprint Client
==========================
Uses curl_cffi to make HTTP requests with browser-like TLS fingerprints.
This prevents detection by anti-bot systems that fingerprint the TLS handshake.

Why this matters:
- Python's requests library has a distinctive TLS fingerprint
- Anti-bot systems (Cloudflare, Akamai, PerimeterX) can identify Python bots by TLS
- curl_cffi impersonates real browser TLS fingerprints (Chrome, Firefox, Safari, Edge)
"""

import logging
import random
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

try:
    from curl_cffi import requests as cffi_requests
    from curl_cffi.requests import Session as CffiSession
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    cffi_requests = None
    CffiSession = None

# Fallback to standard requests if curl_cffi not available
import requests as std_requests

logger = logging.getLogger("tls_client")

# Available browser impersonations in curl_cffi
# These represent real browser TLS fingerprints
BROWSER_IMPERSONATIONS = [
    "chrome120",
    "chrome119",
    "chrome116",
    "chrome110",
    "chrome107",
    "chrome104",
    "chrome101",
    "chrome100",
    "chrome99",
    "edge101",
    "edge99",
    "safari15_5",
    "safari15_3",
    "safari17_0",
]

# Chrome versions are most common, weight them higher
WEIGHTED_IMPERSONATIONS = [
    "chrome120", "chrome120", "chrome120",  # Most common
    "chrome119", "chrome119",
    "chrome116", "chrome116",
    "chrome110",
    "edge101",
    "safari17_0",
    "safari15_5",
]


@dataclass
class TLSResponse:
    """Wrapper for HTTP response with TLS info."""
    status_code: int
    content: bytes
    text: str
    headers: Dict[str, str]
    url: str
    impersonation: str
    ok: bool

    def raise_for_status(self):
        """Raise an exception for 4xx/5xx status codes."""
        if 400 <= self.status_code < 600:
            raise TLSHTTPError(f"HTTP {self.status_code}", response=self)

    def json(self):
        """Parse response as JSON."""
        import json
        return json.loads(self.text)


class TLSHTTPError(Exception):
    """HTTP error with response attached."""
    def __init__(self, message: str, response: Optional[TLSResponse] = None):
        super().__init__(message)
        self.response = response


class TLSClient:
    """
    HTTP client with browser TLS fingerprint impersonation.

    Usage:
        client = TLSClient()
        response = client.get("https://example.com", headers={"User-Agent": "..."})

    Or as a drop-in replacement:
        response = tls_get("https://example.com", headers=headers, proxies=proxies)
    """

    def __init__(self, impersonate: Optional[str] = None, rotate_impersonation: bool = True):
        """
        Initialize TLS client.

        Args:
            impersonate: Specific browser to impersonate (e.g., "chrome120")
            rotate_impersonation: If True, randomly rotate browser fingerprint per request
        """
        self.impersonate = impersonate
        self.rotate_impersonation = rotate_impersonation
        self._session: Optional[CffiSession] = None

        if not CURL_CFFI_AVAILABLE:
            logger.warning(
                "curl_cffi not installed. Falling back to standard requests. "
                "Install with: pip install curl_cffi"
            )

    def _get_impersonation(self) -> str:
        """Get browser impersonation to use."""
        if self.impersonate:
            return self.impersonate
        if self.rotate_impersonation:
            return random.choice(WEIGHTED_IMPERSONATIONS)
        return "chrome120"  # Default to latest Chrome

    def _create_session(self, impersonate: str) -> CffiSession:
        """Create a curl_cffi session with browser impersonation."""
        if not CURL_CFFI_AVAILABLE:
            return None
        return CffiSession(impersonate=impersonate)

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        proxies: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        **kwargs
    ) -> TLSResponse:
        """
        Make a GET request with browser TLS fingerprint.

        Args:
            url: URL to fetch
            headers: HTTP headers
            proxies: Proxy configuration {"http": "...", "https": "..."}
            timeout: Request timeout in seconds
            **kwargs: Additional arguments passed to curl_cffi

        Returns:
            TLSResponse object
        """
        impersonate = self._get_impersonation()

        if CURL_CFFI_AVAILABLE:
            try:
                # Convert proxies format if needed
                proxy = None
                if proxies:
                    proxy = proxies.get("https") or proxies.get("http")

                response = cffi_requests.get(
                    url,
                    headers=headers,
                    proxy=proxy,
                    timeout=timeout,
                    impersonate=impersonate,
                    **kwargs
                )

                logger.debug(f"TLS request with {impersonate} fingerprint to {url}")

                return TLSResponse(
                    status_code=response.status_code,
                    content=response.content,
                    text=response.text,
                    headers=dict(response.headers),
                    url=str(response.url),
                    impersonation=impersonate,
                    ok=response.ok
                )
            except Exception as e:
                logger.warning(f"curl_cffi request failed: {e}. Falling back to requests.")

        # Fallback to standard requests
        response = std_requests.get(
            url,
            headers=headers,
            proxies=proxies,
            timeout=timeout
        )

        return TLSResponse(
            status_code=response.status_code,
            content=response.content,
            text=response.text,
            headers=dict(response.headers),
            url=response.url,
            impersonation="requests_fallback",
            ok=response.ok
        )

    def post(
        self,
        url: str,
        data: Optional[Union[Dict, str, bytes]] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
        proxies: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        **kwargs
    ) -> TLSResponse:
        """Make a POST request with browser TLS fingerprint."""
        impersonate = self._get_impersonation()

        if CURL_CFFI_AVAILABLE:
            try:
                proxy = None
                if proxies:
                    proxy = proxies.get("https") or proxies.get("http")

                response = cffi_requests.post(
                    url,
                    data=data,
                    json=json,
                    headers=headers,
                    proxy=proxy,
                    timeout=timeout,
                    impersonate=impersonate,
                    **kwargs
                )

                logger.debug(f"TLS POST request with {impersonate} fingerprint to {url}")

                return TLSResponse(
                    status_code=response.status_code,
                    content=response.content,
                    text=response.text,
                    headers=dict(response.headers),
                    url=str(response.url),
                    impersonation=impersonate,
                    ok=response.ok
                )
            except Exception as e:
                logger.warning(f"curl_cffi POST failed: {e}. Falling back to requests.")

        # Fallback
        response = std_requests.post(
            url,
            data=data,
            json=json,
            headers=headers,
            proxies=proxies,
            timeout=timeout
        )

        return TLSResponse(
            status_code=response.status_code,
            content=response.content,
            text=response.text,
            headers=dict(response.headers),
            url=response.url,
            impersonation="requests_fallback",
            ok=response.ok
        )


# Global client instance for convenience functions
_default_client = TLSClient()


def tls_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    proxies: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    impersonate: Optional[str] = None,
    **kwargs
) -> TLSResponse:
    """
    Convenience function for GET requests with browser TLS fingerprint.

    Drop-in replacement for requests.get() with TLS fingerprint impersonation.

    Args:
        url: URL to fetch
        headers: HTTP headers
        proxies: Proxy configuration
        timeout: Request timeout
        impersonate: Specific browser to impersonate (optional)

    Returns:
        TLSResponse object (compatible with requests.Response)
    """
    if impersonate:
        client = TLSClient(impersonate=impersonate, rotate_impersonation=False)
        return client.get(url, headers=headers, proxies=proxies, timeout=timeout, **kwargs)
    return _default_client.get(url, headers=headers, proxies=proxies, timeout=timeout, **kwargs)


def tls_post(
    url: str,
    data: Optional[Union[Dict, str, bytes]] = None,
    json: Optional[Dict] = None,
    headers: Optional[Dict[str, str]] = None,
    proxies: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    impersonate: Optional[str] = None,
    **kwargs
) -> TLSResponse:
    """
    Convenience function for POST requests with browser TLS fingerprint.
    """
    if impersonate:
        client = TLSClient(impersonate=impersonate, rotate_impersonation=False)
        return client.post(url, data=data, json=json, headers=headers, proxies=proxies, timeout=timeout, **kwargs)
    return _default_client.post(url, data=data, json=json, headers=headers, proxies=proxies, timeout=timeout, **kwargs)


def get_available_impersonations() -> list:
    """Return list of available browser impersonations."""
    return BROWSER_IMPERSONATIONS.copy()


def is_tls_client_available() -> bool:
    """Check if TLS fingerprint client is available."""
    return CURL_CFFI_AVAILABLE
