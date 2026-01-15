"""
Tests for custom exceptions.
"""

import pytest
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
    classify_exception,
)


class TestScraperError:
    """Tests for base ScraperError."""
    
    def test_basic_error(self):
        """Test basic error creation."""
        error = ScraperError("Test error")
        assert str(error) == "Test error"
        assert error.error_type == "scraper_error"
        assert error.likely_ban is False
    
    def test_error_with_details(self):
        """Test error with custom details."""
        error = ScraperError(
            "Test error",
            error_type="custom",
            likely_ban=True,
            details={"key": "value"}
        )
        assert error.error_type == "custom"
        assert error.likely_ban is True
        assert error.details["key"] == "value"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        error = ScraperError("Test", details={"url": "https://example.com"})
        result = error.to_dict()
        
        assert result["error"] == "Test"
        assert result["error_type"] == "scraper_error"
        assert result["likely_ban"] is False
        assert result["url"] == "https://example.com"


class TestTimeoutError:
    """Tests for TimeoutError."""
    
    def test_timeout_error(self):
        """Test timeout error creation."""
        error = TimeoutError(
            "Timed out after 30s",
            elapsed_time=30.5,
            stage="navigation"
        )
        assert error.error_type == "timeout"
        assert error.elapsed_time == 30.5
        assert error.stage == "navigation"
        assert error.likely_ban is False
    
    def test_timeout_with_screenshot(self):
        """Test timeout with screenshot path."""
        error = TimeoutError(
            "Timed out",
            elapsed_time=45.0,
            screenshot_path="/path/to/screenshot.png"
        )
        assert error.screenshot_path == "/path/to/screenshot.png"
        assert error.to_dict()["screenshot"] == "/path/to/screenshot.png"


class TestAccessDeniedError:
    """Tests for AccessDeniedError."""
    
    def test_access_denied(self):
        """Test access denied error."""
        error = AccessDeniedError("403 Forbidden", status_code=403)
        assert error.error_type == "access_denied"
        assert error.likely_ban is True
        assert error.details["status_code"] == 403


class TestCloudflareError:
    """Tests for CloudflareError."""
    
    def test_cloudflare_error(self):
        """Test Cloudflare error."""
        error = CloudflareError(
            "Cloudflare challenge detected",
            url="https://protected-site.com"
        )
        assert error.error_type == "cloudflare"
        assert error.likely_ban is True


class TestCaptchaError:
    """Tests for CaptchaError."""
    
    def test_captcha_error(self):
        """Test CAPTCHA error."""
        error = CaptchaError(
            "CAPTCHA detected",
            captcha_type="recaptcha_v2"
        )
        assert error.error_type == "captcha"
        assert error.likely_ban is False
        assert error.details["captcha_type"] == "recaptcha_v2"


class TestContentExtractionError:
    """Tests for ContentExtractionError."""
    
    def test_extraction_error(self):
        """Test extraction error."""
        error = ContentExtractionError(
            "No article found",
            html_size=50000
        )
        assert error.error_type == "extraction_failed"
        assert error.details["html_size"] == 50000


class TestNetworkError:
    """Tests for NetworkError."""
    
    def test_network_error(self):
        """Test network error."""
        error = NetworkError(
            "Connection refused",
            status_code=502
        )
        assert error.error_type == "network"
        assert error.likely_ban is False


class TestProxyError:
    """Tests for ProxyError."""
    
    def test_proxy_error(self):
        """Test proxy error."""
        error = ProxyError(
            "Proxy connection failed",
            proxy="http://proxy:8080"
        )
        assert error.error_type == "proxy"
        assert error.details["proxy"] == "http://proxy:8080"


class TestExpiredLinkError:
    """Tests for ExpiredLinkError."""
    
    def test_expired_link_error(self):
        """Test expired link error."""
        error = ExpiredLinkError(
            "Google News link expired",
            url="https://news.google.com/..."
        )
        assert error.error_type == "expired_link"
        assert error.likely_ban is False


class TestRateLimitError:
    """Tests for RateLimitError."""
    
    def test_rate_limit_error(self):
        """Test rate limit error."""
        error = RateLimitError(
            "Rate limit exceeded",
            retry_after=60
        )
        assert error.error_type == "rate_limit"
        assert error.likely_ban is True
        assert error.details["retry_after"] == 60


class TestClassifyException:
    """Tests for exception classification."""
    
    def test_classify_known_type(self):
        """Test classifying known error type."""
        assert classify_exception("timeout") == TimeoutError
        assert classify_exception("access_denied") == AccessDeniedError
        assert classify_exception("cloudflare") == CloudflareError
    
    def test_classify_unknown_type(self):
        """Test classifying unknown error type."""
        assert classify_exception("unknown") == ScraperError
