"""
Custom exceptions for the web scraper.

Provides structured error handling with error types and metadata.
"""

from typing import Optional, Dict, Any


class ScraperError(Exception):
    """Base exception for all scraper errors."""
    
    error_type: str = "scraper_error"
    likely_ban: bool = False
    
    def __init__(
        self, 
        message: str, 
        error_type: str = None,
        likely_ban: bool = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        if error_type:
            self.error_type = error_type
        if likely_ban is not None:
            self.likely_ban = likely_ban
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": self.message,
            "error_type": self.error_type,
            "likely_ban": self.likely_ban,
            **self.details
        }


class TimeoutError(ScraperError):
    """Raised when scrape operation exceeds timeout."""
    
    error_type = "timeout"
    likely_ban = False
    
    def __init__(
        self, 
        message: str, 
        elapsed_time: float,
        stage: str = "",
        screenshot_path: Optional[str] = None
    ):
        super().__init__(message, details={
            "elapsed_time": elapsed_time,
            "stage": stage,
            "screenshot": screenshot_path
        })
        self.elapsed_time = elapsed_time
        self.stage = stage
        self.screenshot_path = screenshot_path


class AccessDeniedError(ScraperError):
    """Raised when access is denied (403, blocked, etc)."""
    
    error_type = "access_denied"
    likely_ban = True
    
    def __init__(
        self, 
        message: str,
        status_code: Optional[int] = None,
        url: Optional[str] = None
    ):
        super().__init__(message, details={
            "status_code": status_code,
            "url": url
        })


class CloudflareError(ScraperError):
    """Raised when Cloudflare challenge cannot be bypassed."""
    
    error_type = "cloudflare"
    likely_ban = True
    
    def __init__(self, message: str, url: Optional[str] = None):
        super().__init__(message, details={"url": url})


class CaptchaError(ScraperError):
    """Raised when CAPTCHA cannot be solved."""
    
    error_type = "captcha"
    likely_ban = False
    
    def __init__(
        self, 
        message: str,
        captcha_type: Optional[str] = None,
        url: Optional[str] = None
    ):
        super().__init__(message, details={
            "captcha_type": captcha_type,
            "url": url
        })


class ContentExtractionError(ScraperError):
    """Raised when article content cannot be extracted."""
    
    error_type = "extraction_failed"
    likely_ban = False
    
    def __init__(
        self, 
        message: str,
        url: Optional[str] = None,
        html_size: Optional[int] = None
    ):
        super().__init__(message, details={
            "url": url,
            "html_size": html_size
        })


class NetworkError(ScraperError):
    """Raised for network-related failures."""
    
    error_type = "network"
    likely_ban = False
    
    def __init__(
        self, 
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        super().__init__(message, details={
            "url": url,
            "status_code": status_code
        })


class ProxyError(ScraperError):
    """Raised when proxy connection fails."""
    
    error_type = "proxy"
    likely_ban = False
    
    def __init__(self, message: str, proxy: Optional[str] = None):
        super().__init__(message, details={"proxy": proxy})


class ExpiredLinkError(ScraperError):
    """Raised when a Google News or similar link has expired."""
    
    error_type = "expired_link"
    likely_ban = False
    
    def __init__(self, message: str, url: Optional[str] = None):
        super().__init__(message, details={"url": url})


class RateLimitError(ScraperError):
    """Raised when rate limit is hit."""
    
    error_type = "rate_limit"
    likely_ban = True
    
    def __init__(
        self, 
        message: str,
        retry_after: Optional[int] = None,
        url: Optional[str] = None
    ):
        super().__init__(message, details={
            "retry_after": retry_after,
            "url": url
        })


# Exception registry for classification
EXCEPTION_MAP = {
    "timeout": TimeoutError,
    "access_denied": AccessDeniedError,
    "cloudflare": CloudflareError,
    "captcha": CaptchaError,
    "extraction_failed": ContentExtractionError,
    "network": NetworkError,
    "proxy": ProxyError,
    "expired_link": ExpiredLinkError,
    "rate_limit": RateLimitError,
}


def classify_exception(error_type: str) -> type:
    """Get exception class for error type."""
    return EXCEPTION_MAP.get(error_type, ScraperError)
