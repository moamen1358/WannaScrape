"""
Tests for the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Set test environment
os.environ["SCRAPER_API_KEY"] = "test-api-key"

from app.api.scraper_api import app, get_scraper


# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_check(self):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert "features" in data
    
    def test_health_check_no_auth_required(self):
        """Test health check doesn't require authentication."""
        response = client.get("/health")
        assert response.status_code == 200


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        # Check for some expected metric names
        content = response.text
        assert "scraper_requests_total" in content or "scraper" in content
    
    def test_metrics_no_auth_required(self):
        """Test metrics endpoint doesn't require authentication."""
        response = client.get("/metrics")
        assert response.status_code == 200


class TestAuthentication:
    """Tests for API key authentication."""
    
    def test_scrape_without_api_key(self):
        """Test scrape endpoint requires API key."""
        response = client.post(
            "/scrape",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]
    
    def test_scrape_with_invalid_api_key(self):
        """Test scrape endpoint rejects invalid API key."""
        response = client.post(
            "/scrape",
            json={"url": "https://example.com"},
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]
    
    def test_scrape_with_valid_api_key(self):
        """Test scrape endpoint accepts valid API key."""
        # Mock the scraper
        mock_scraper = MagicMock()
        mock_scraper.extract_article.return_value = {
            "title": "Test Article",
            "text": "Test content",
            "date": "2026-01-15"
        }
        
        def mock_get_scraper():
            return mock_scraper
        
        app.dependency_overrides[get_scraper] = mock_get_scraper
        
        try:
            response = client.post(
                "/scrape",
                json={"url": "https://example.com"},
                headers={"X-API-Key": "test-api-key"}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Test Article"
        finally:
            app.dependency_overrides.clear()


class TestScrapeEndpoint:
    """Tests for /scrape endpoint."""
    
    def test_scrape_success(self):
        """Test successful scrape."""
        mock_scraper = MagicMock()
        mock_scraper.extract_article.return_value = {
            "title": "Test Article",
            "text": "This is test content.",
            "date": "2026-01-15",
            "source": "https://example.com",
            "user_agent_used": "Mozilla/5.0",
            "location_used": "New York, USA"
        }
        
        app.dependency_overrides[get_scraper] = lambda: mock_scraper
        
        try:
            response = client.post(
                "/scrape",
                json={"url": "https://example.com", "company_name": "Test Corp"},
                headers={"X-API-Key": "test-api-key"}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Test Article"
            assert data[0]["company_name"] == "Test Corp"
        finally:
            app.dependency_overrides.clear()
    
    def test_scrape_error_response(self):
        """Test scrape error is properly returned."""
        mock_scraper = MagicMock()
        mock_scraper.extract_article.return_value = {
            "error": "Access denied",
            "error_type": "access_denied"
        }
        
        app.dependency_overrides[get_scraper] = lambda: mock_scraper
        
        try:
            response = client.post(
                "/scrape",
                json={"url": "https://blocked-site.com"},
                headers={"X-API-Key": "test-api-key"}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data[0]["error"] == "Access denied"
            assert data[0]["error_type"] == "access_denied"
        finally:
            app.dependency_overrides.clear()
    
    def test_scrape_invalid_url(self):
        """Test scrape with invalid URL."""
        response = client.post(
            "/scrape",
            json={"url": "not-a-valid-url"},
            headers={"X-API-Key": "test-api-key"}
        )
        assert response.status_code == 422  # Validation error


class TestSearchEndpoint:
    """Tests for /search endpoint."""
    
    def test_search_success(self):
        """Test successful search."""
        mock_scraper = MagicMock()
        mock_scraper.find_source_from_text.return_value = [
            {"title": "Result 1", "url": "https://example.com/1"},
            {"title": "Result 2", "url": "https://example.com/2"}
        ]
        
        app.dependency_overrides[get_scraper] = lambda: mock_scraper
        
        try:
            response = client.post(
                "/search",
                json={"text": "sample search text", "num_results": 2},
                headers={"X-API-Key": "test-api-key"}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) == 2
            assert data[0]["title"] == "Result 1"
        finally:
            app.dependency_overrides.clear()


class TestCorrelationId:
    """Tests for correlation ID middleware."""
    
    def test_correlation_id_generated(self):
        """Test correlation ID is generated if not provided."""
        response = client.get("/health")
        assert "X-Correlation-ID" in response.headers
    
    def test_correlation_id_preserved(self):
        """Test correlation ID is preserved if provided."""
        response = client.get(
            "/health",
            headers={"X-Correlation-ID": "my-custom-id"}
        )
        assert response.headers["X-Correlation-ID"] == "my-custom-id"
