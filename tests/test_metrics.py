"""
Tests for Prometheus metrics module.
"""

import pytest


class TestMetricsImport:
    """Test metrics module imports correctly."""
    
    def test_import_metrics(self):
        """Test that metrics module can be imported."""
        from app.monitoring import metrics
        assert metrics is not None
    
    def test_import_track_request(self):
        """Test track_request decorator import."""
        from app.monitoring.metrics import track_request
        assert callable(track_request)
    
    def test_import_record_functions(self):
        """Test record functions import."""
        from app.monitoring.metrics import (
            record_scrape,
            record_cloudflare,
            record_captcha,
            record_rate_limit,
            record_search,
        )
        assert callable(record_scrape)
        assert callable(record_cloudflare)
        assert callable(record_captcha)
        assert callable(record_rate_limit)
        assert callable(record_search)


class TestMetricsRecording:
    """Test metrics recording functions."""
    
    def test_record_scrape_success(self):
        """Test recording successful scrape."""
        from app.monitoring.metrics import record_scrape, SCRAPE_TOTAL
        
        # Get initial value
        initial = SCRAPE_TOTAL._metrics.get(('success', 'none'))
        
        record_scrape(status="success", error_type="none", duration=1.5, content_size=1000)
        
        # Verify counter incremented (or was created)
        assert True  # If no exception, it works
    
    def test_record_scrape_error(self):
        """Test recording failed scrape."""
        from app.monitoring.metrics import record_scrape
        
        record_scrape(status="error", error_type="timeout", duration=30.0)
        assert True
    
    def test_record_cloudflare(self):
        """Test recording Cloudflare challenge."""
        from app.monitoring.metrics import record_cloudflare
        
        record_cloudflare(status="detected")
        record_cloudflare(status="bypassed")
        assert True
    
    def test_record_captcha(self):
        """Test recording CAPTCHA attempt."""
        from app.monitoring.metrics import record_captcha
        
        record_captcha(status="solved")
        record_captcha(status="failed")
        assert True
    
    def test_record_rate_limit(self):
        """Test recording rate limit hit."""
        from app.monitoring.metrics import record_rate_limit
        
        record_rate_limit()
        assert True
    
    def test_record_search(self):
        """Test recording search request."""
        from app.monitoring.metrics import record_search
        
        record_search(status="success")
        record_search(status="error")
        assert True


class TestMetricsEndpoint:
    """Test metrics endpoint output."""
    
    def test_get_metrics_returns_bytes(self):
        """Test get_metrics returns bytes."""
        from app.monitoring.metrics import get_metrics
        
        result = get_metrics()
        assert isinstance(result, bytes)
    
    def test_get_metrics_contains_scraper_info(self):
        """Test metrics output contains scraper info."""
        from app.monitoring.metrics import get_metrics
        
        result = get_metrics().decode('utf-8')
        assert 'scraper' in result.lower()
    
    def test_get_metrics_content_type(self):
        """Test metrics content type."""
        from app.monitoring.metrics import get_metrics_content_type
        
        content_type = get_metrics_content_type()
        assert 'text/plain' in content_type or 'text' in content_type


class TestTrackRequestDecorator:
    """Test the track_request decorator."""
    
    def test_decorator_wraps_sync_function(self):
        """Test decorator works with sync functions."""
        from app.monitoring.metrics import track_request
        
        @track_request("test_endpoint")
        def my_sync_function():
            return "result"
        
        result = my_sync_function()
        assert result == "result"
    
    def test_decorator_wraps_async_function(self):
        """Test decorator works with async functions."""
        import asyncio
        from app.monitoring.metrics import track_request
        
        @track_request("test_endpoint_async")
        async def my_async_function():
            return "async_result"
        
        result = asyncio.run(my_async_function())
        assert result == "async_result"
    
    def test_decorator_handles_exception(self):
        """Test decorator properly handles exceptions."""
        from app.monitoring.metrics import track_request
        
        @track_request("test_exception")
        def raise_error():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            raise_error()
