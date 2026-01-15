"""
Pytest configuration and fixtures.
"""

import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_url():
    """Sample URL for testing."""
    return "https://example.com"


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Article</title></head>
    <body>
        <article>
            <h1>Test Headline</h1>
            <p>This is test article content with some text.</p>
            <p>Another paragraph with more content.</p>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "browser": {
            "headless": True,
            "slow_mo": 0,
            "timeout": 10000
        },
        "rate_limiting": {
            "min_delay_between_requests": 0,
            "max_delay_between_requests": 0
        },
        "proxies": {
            "enabled": False
        },
        "captcha": {
            "enabled": False
        }
    }
