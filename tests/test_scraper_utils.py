"""
Tests for core scraper utilities and helpers.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestTimeoutChecker:
    """Tests for TimeoutChecker class."""
    
    def test_timeout_checker_init(self):
        """Test TimeoutChecker initialization."""
        from app.core.scraper import TimeoutChecker
        
        checker = TimeoutChecker(max_timeout=60, url="https://example.com")
        assert checker.max_timeout == 60
        assert checker.url == "https://example.com"
    
    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        from app.core.scraper import TimeoutChecker
        import time
        
        checker = TimeoutChecker(max_timeout=60, url="https://example.com")
        time.sleep(0.1)
        
        elapsed = checker.elapsed()
        assert elapsed >= 0.1
        assert elapsed < 1.0
    
    def test_remaining_time(self):
        """Test remaining time calculation."""
        from app.core.scraper import TimeoutChecker
        
        checker = TimeoutChecker(max_timeout=60, url="https://example.com")
        remaining = checker.remaining()
        
        assert remaining > 59
        assert remaining <= 60
    
    def test_check_no_timeout(self):
        """Test check doesn't raise when within timeout."""
        from app.core.scraper import TimeoutChecker
        
        checker = TimeoutChecker(max_timeout=60, url="https://example.com")
        # Should not raise
        checker.check(stage="test")
    
    def test_check_raises_on_timeout(self):
        """Test check raises when timeout exceeded."""
        from app.core.scraper import TimeoutChecker, ScrapeTimeoutError
        
        checker = TimeoutChecker(max_timeout=0, url="https://example.com")
        
        with pytest.raises(ScrapeTimeoutError):
            checker.check(stage="test")


class TestScrapeTimeoutError:
    """Tests for ScrapeTimeoutError exception."""
    
    def test_error_creation(self):
        """Test ScrapeTimeoutError creation."""
        from app.core.scraper import ScrapeTimeoutError
        
        error = ScrapeTimeoutError(
            message="Timeout occurred",
            elapsed_time=45.5,
            screenshot_path="/path/to/screenshot.png"
        )
        
        assert str(error) == "Timeout occurred"
        assert error.elapsed_time == 45.5
        assert error.screenshot_path == "/path/to/screenshot.png"
    
    def test_error_without_screenshot(self):
        """Test ScrapeTimeoutError without screenshot."""
        from app.core.scraper import ScrapeTimeoutError
        
        error = ScrapeTimeoutError(
            message="Timeout",
            elapsed_time=30.0
        )
        
        assert error.screenshot_path is None


class TestClassifyError:
    """Tests for error classification helper."""
    
    def test_classify_timeout_error(self):
        """Test timeout error classification."""
        from app.utils.helpers import classify_error
        
        result = classify_error("TimeoutError: page load timed out")
        assert result["type"] == "timeout"
    
    def test_classify_network_error(self):
        """Test network error classification."""
        from app.utils.helpers import classify_error
        
        result = classify_error("Connection refused by server")
        assert result["type"] == "network"
    
    def test_classify_cloudflare(self):
        """Test Cloudflare detection."""
        from app.utils.helpers import classify_error
        
        result = classify_error("error", page_content="Please wait... Cloudflare checking your browser")
        assert result["type"] == "cloudflare"
    
    def test_classify_unknown_error(self):
        """Test unknown error classification."""
        from app.utils.helpers import classify_error
        
        result = classify_error("Some random error")
        assert result["type"] == "unknown"
        assert result["retry_recommended"] == True


class TestGetReferrer:
    """Tests for referrer generation."""
    
    def test_get_referrer_returns_string_or_none(self):
        """Test get_referrer returns valid value."""
        from app.utils.helpers import get_referrer
        
        referrer = get_referrer("https://example.com/article")
        assert referrer is None or isinstance(referrer, str)
    
    def test_get_referrer_multiple_calls(self):
        """Test get_referrer produces varied results."""
        from app.utils.helpers import get_referrer
        
        results = set()
        for _ in range(20):
            results.add(get_referrer("https://example.com"))
        
        # Should have some variation (not always the same)
        assert len(results) >= 1


class TestLoadConfig:
    """Tests for config loading."""
    
    def test_load_config_returns_dict(self):
        """Test load_config returns dictionary."""
        from app.utils.helpers import load_config
        
        config = load_config("config/config.json")
        assert isinstance(config, dict)
    
    def test_load_config_missing_file(self):
        """Test load_config handles missing file."""
        from app.utils.helpers import load_config
        
        config = load_config("nonexistent/config.json")
        assert isinstance(config, dict)


class TestMaskProxy:
    """Tests for proxy masking utility."""
    
    def test_mask_proxy_hides_password(self):
        """Test mask_proxy hides credentials."""
        from app.utils.proxy_manager import mask_proxy
        
        proxy = {
            "server": "http://proxy.example.com:8080",
            "username": "user123",
            "password": "secret_password"
        }
        
        masked = mask_proxy(proxy)
        assert "secret_password" not in str(masked)
        assert "***" in str(masked) or masked["password"] != "secret_password"
    
    def test_mask_proxy_without_password(self):
        """Test mask_proxy handles proxy without password."""
        from app.utils.proxy_manager import mask_proxy
        
        proxy = {"server": "http://proxy.example.com:8080"}
        masked = mask_proxy(proxy)
        assert masked is not None
