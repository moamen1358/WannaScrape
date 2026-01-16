"""
Tests for the Detection Plugin System.

These tests verify:
1. Base class functionality
2. Auto-discovery mechanism
3. Registry operations
4. Individual detection plugins
5. Handler integration
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Optional


# === BASE CLASS TESTS ===

class TestDetectionResult:
    """Tests for DetectionResult dataclass."""

    def test_result_creation(self):
        """Test basic result creation."""
        from app.detections.base import DetectionResult, SolveMethod

        result = DetectionResult(
            detected=True,
            detection_type="test",
            confidence=0.95,
            details={"key": "value"},
            solve_method=SolveMethod.WAIT
        )

        assert result.detected is True
        assert result.detection_type == "test"
        assert result.confidence == 0.95
        assert result.details == {"key": "value"}
        assert result.solve_method == SolveMethod.WAIT

    def test_result_bool_conversion(self):
        """Test that DetectionResult converts to bool correctly."""
        from app.detections.base import DetectionResult

        detected = DetectionResult(detected=True, detection_type="test")
        not_detected = DetectionResult(detected=False, detection_type="test")

        assert bool(detected) is True
        assert bool(not_detected) is False

    def test_result_defaults(self):
        """Test default values."""
        from app.detections.base import DetectionResult, SolveMethod

        result = DetectionResult(detected=False, detection_type="test")

        assert result.confidence == 1.0
        assert result.details == {}
        assert result.solve_method == SolveMethod.NONE


class TestBaseDetection:
    """Tests for BaseDetection abstract class."""

    def test_cannot_instantiate_base(self):
        """Test that BaseDetection cannot be instantiated directly."""
        from app.detections.base import BaseDetection

        # BaseDetection has abstract methods, so it can't be instantiated
        # But we can test the class attributes
        assert BaseDetection.name == "base"
        assert BaseDetection.priority == 100

    def test_subclass_implementation(self):
        """Test that subclasses can be created properly."""
        from app.detections.base import BaseDetection, DetectionResult, DetectionCategory

        class TestDetection(BaseDetection):
            name = "test_detection"
            priority = 50
            category = DetectionCategory.CHALLENGE

            def detect(self, page, url):
                return DetectionResult(detected=False, detection_type=self.name)

            def solve(self, page, url, detection_result):
                return True

        detection = TestDetection()
        assert detection.name == "test_detection"
        assert detection.priority == 50
        assert detection.enabled is True

    def test_config_passed_to_setup(self):
        """Test that config is available in _setup."""
        from app.detections.base import BaseDetection, DetectionResult, DetectionCategory

        setup_called = []

        class ConfigTestDetection(BaseDetection):
            name = "config_test"
            priority = 50
            category = DetectionCategory.CHALLENGE

            def _setup(self):
                setup_called.append(self.config)

            def detect(self, page, url):
                return DetectionResult(detected=False, detection_type=self.name)

            def solve(self, page, url, detection_result):
                return True

        config = {"key": "value"}
        detection = ConfigTestDetection(config=config)

        assert len(setup_called) == 1
        assert setup_called[0] == config


# === REGISTRY TESTS ===

class TestDetectionRegistry:
    """Tests for DetectionRegistry."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset the singleton before each test."""
        from app.detections.registry import DetectionRegistry
        DetectionRegistry.reset()
        yield
        DetectionRegistry.reset()

    def test_singleton_pattern(self):
        """Test that registry is a singleton."""
        from app.detections.registry import DetectionRegistry

        reg1 = DetectionRegistry(auto_discover=False)
        reg2 = DetectionRegistry(auto_discover=False)

        assert reg1 is reg2

    def test_auto_discovery(self):
        """Test that plugins are auto-discovered."""
        from app.detections.registry import DetectionRegistry

        registry = DetectionRegistry()

        # Should have discovered our plugins (those that don't require API keys)
        # Note: recaptcha and hcaptcha are disabled without API keys
        assert "cloudflare" in registry.list_all()
        assert "perimeterx" in registry.list_all()
        assert "datadome" in registry.list_all()

    def test_auto_discovery_with_api_config(self):
        """Test that API-requiring plugins load when configured."""
        from app.detections.registry import DetectionRegistry
        DetectionRegistry.reset()

        # Provide API config
        config = {"captcha": {"enabled": True, "api_key": "test-key", "service": "2captcha"}}
        registry = DetectionRegistry(config=config)

        # Now recaptcha and hcaptcha should be enabled
        assert "recaptcha" in registry.list_all()
        assert "hcaptcha" in registry.list_all()

    def test_priority_ordering(self):
        """Test that detections are ordered by priority."""
        from app.detections.registry import DetectionRegistry

        registry = DetectionRegistry()
        detections = registry.list_all()

        # Get priorities
        priorities = [registry.get(name).priority for name in detections]

        # Should be sorted ascending
        assert priorities == sorted(priorities)

    def test_manual_registration(self):
        """Test manual plugin registration."""
        from app.detections.registry import DetectionRegistry
        from app.detections.base import BaseDetection, DetectionResult, DetectionCategory

        class ManualDetection(BaseDetection):
            name = "manual_test"
            priority = 999
            category = DetectionCategory.CHALLENGE

            def detect(self, page, url):
                return DetectionResult(detected=False, detection_type=self.name)

            def solve(self, page, url, result):
                return True

        registry = DetectionRegistry(auto_discover=False)
        registry.register(ManualDetection)

        assert "manual_test" in registry.list_all()

    def test_unregister(self):
        """Test plugin unregistration."""
        from app.detections.registry import DetectionRegistry

        registry = DetectionRegistry()
        assert "cloudflare" in registry.list_all()

        registry.unregister("cloudflare")
        assert "cloudflare" not in registry.list_all()

    def test_get_by_name(self):
        """Test getting detection by name."""
        from app.detections.registry import DetectionRegistry

        registry = DetectionRegistry()
        cloudflare = registry.get("cloudflare")

        assert cloudflare is not None
        assert cloudflare.name == "cloudflare"

    def test_get_nonexistent(self):
        """Test getting non-existent detection."""
        from app.detections.registry import DetectionRegistry

        registry = DetectionRegistry()
        result = registry.get("nonexistent")

        assert result is None

    def test_list_by_category(self):
        """Test filtering by category."""
        from app.detections.registry import DetectionRegistry
        from app.detections.base import DetectionCategory

        registry = DetectionRegistry()

        challenges = registry.list_by_category(DetectionCategory.CHALLENGE)

        # Challenges don't require API keys
        assert "cloudflare" in challenges
        assert "perimeterx" in challenges
        assert "datadome" in challenges

    def test_list_by_category_with_captchas(self):
        """Test filtering CAPTCHAs when API is configured."""
        from app.detections.registry import DetectionRegistry
        from app.detections.base import DetectionCategory
        DetectionRegistry.reset()

        config = {"captcha": {"enabled": True, "api_key": "test-key", "service": "2captcha"}}
        registry = DetectionRegistry(config=config)

        captchas = registry.list_by_category(DetectionCategory.CAPTCHA)

        assert "recaptcha" in captchas
        assert "hcaptcha" in captchas

    def test_get_stats(self):
        """Test statistics retrieval."""
        from app.detections.registry import DetectionRegistry

        registry = DetectionRegistry()
        stats = registry.get_stats()

        assert "total_detections" in stats
        # At least 3 detections that don't require API keys
        assert stats["total_detections"] >= 3
        assert "by_category" in stats
        assert "detections" in stats


# === INDIVIDUAL DETECTION TESTS ===

class TestCloudflareDetection:
    """Tests for Cloudflare detection plugin."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page."""
        page = MagicMock()
        page.locator.return_value.count.return_value = 0
        page.title.return_value = "Test Page"
        page.content.return_value = "<html><body>Normal content</body></html>"
        page.url = "https://example.com"
        return page

    def test_no_detection_on_normal_page(self, mock_page):
        """Test that normal pages don't trigger detection."""
        from app.detections.cloudflare import CloudflareDetection

        detection = CloudflareDetection()
        result = detection.detect(mock_page, "https://example.com")

        assert result.detected is False

    def test_detection_by_selector(self, mock_page):
        """Test detection via CSS selector."""
        from app.detections.cloudflare import CloudflareDetection

        # Mock selector match
        def locator_side_effect(selector):
            mock = MagicMock()
            if "#challenge-running" in selector:
                mock.count.return_value = 1
            else:
                mock.count.return_value = 0
            return mock

        mock_page.locator.side_effect = locator_side_effect

        detection = CloudflareDetection()
        result = detection.detect(mock_page, "https://example.com")

        assert result.detected is True
        assert result.detection_type == "cloudflare"
        assert result.details["method"] == "selector"

    def test_detection_by_title(self, mock_page):
        """Test detection via page title."""
        from app.detections.cloudflare import CloudflareDetection

        mock_page.title.return_value = "Just a moment..."

        detection = CloudflareDetection()
        result = detection.detect(mock_page, "https://example.com")

        assert result.detected is True
        assert result.details["method"] == "title"


class TestRecaptchaDetection:
    """Tests for reCAPTCHA detection plugin."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page."""
        page = MagicMock()
        page.locator.return_value.count.return_value = 0
        page.evaluate.return_value = None
        return page

    def test_no_detection_on_normal_page(self, mock_page):
        """Test that normal pages don't trigger detection."""
        from app.detections.recaptcha import RecaptchaDetection

        detection = RecaptchaDetection()
        result = detection.detect(mock_page, "https://example.com")

        assert result.detected is False

    def test_detection_by_selector(self, mock_page):
        """Test detection via reCAPTCHA selector."""
        from app.detections.recaptcha import RecaptchaDetection

        def locator_side_effect(selector):
            mock = MagicMock()
            if ".g-recaptcha" in selector:
                mock.count.return_value = 1
            else:
                mock.count.return_value = 0
            return mock

        mock_page.locator.side_effect = locator_side_effect
        mock_page.evaluate.return_value = "test-sitekey-123"

        detection = RecaptchaDetection()
        result = detection.detect(mock_page, "https://example.com")

        assert result.detected is True
        assert result.detection_type == "recaptcha"
        assert result.details.get("sitekey") == "test-sitekey-123"


class TestPerimeterXDetection:
    """Tests for PerimeterX detection plugin."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page."""
        page = MagicMock()
        page.locator.return_value.count.return_value = 0
        page.content.return_value = "<html><body>Normal</body></html>"
        return page

    def test_detection_by_selector(self, mock_page):
        """Test detection via PerimeterX selector."""
        from app.detections.perimeterx import PerimeterXDetection

        def locator_side_effect(selector):
            mock = MagicMock()
            if "#px-captcha" in selector:
                mock.count.return_value = 1
            else:
                mock.count.return_value = 0
            return mock

        mock_page.locator.side_effect = locator_side_effect

        detection = PerimeterXDetection()
        result = detection.detect(mock_page, "https://example.com")

        assert result.detected is True
        assert result.detection_type == "perimeterx"


# === HANDLER TESTS ===

class TestDetectionHandler:
    """Tests for DetectionHandler."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset the singleton before each test."""
        from app.detections.registry import DetectionRegistry
        DetectionRegistry.reset()
        yield
        DetectionRegistry.reset()

    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page."""
        page = MagicMock()
        page.locator.return_value.count.return_value = 0
        page.title.return_value = "Test Page"
        page.content.return_value = "<html><body>Normal</body></html>"
        page.url = "https://example.com"
        return page

    def test_no_detections(self, mock_page):
        """Test handler with no detections."""
        from app.detections.handler import DetectionHandler

        handler = DetectionHandler()
        result = handler.handle_detections(mock_page, "https://example.com")

        assert result.detected_any is False
        assert result.blocked is False
        assert result.all_solved is True

    def test_quick_check(self, mock_page):
        """Test quick detection check."""
        from app.detections.handler import DetectionHandler

        handler = DetectionHandler()

        # No detections
        assert handler.quick_check(mock_page, "https://example.com") is False

    def test_get_stats(self):
        """Test handler stats."""
        from app.detections.handler import DetectionHandler

        handler = DetectionHandler()
        stats = handler.get_stats()

        assert "total_detections" in stats
        # At least 3 detections that don't require API keys
        assert stats["total_detections"] >= 3


# === BACKWARD COMPATIBILITY TESTS ===

class TestBackwardCompatibility:
    """Tests for backward compatibility functions."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset the singleton before each test."""
        from app.detections.registry import DetectionRegistry
        DetectionRegistry.reset()
        yield
        DetectionRegistry.reset()

    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page."""
        page = MagicMock()
        page.locator.return_value.count.return_value = 0
        page.title.return_value = "Test Page"
        page.content.return_value = "<html><body>Normal</body></html>"
        page.url = "https://example.com"
        return page

    def test_is_cloudflare_challenge_compat(self, mock_page):
        """Test backward compatible Cloudflare detection."""
        from app.detections.handler import is_cloudflare_challenge

        result = is_cloudflare_challenge(mock_page)
        assert result is False

    def test_wait_for_cloudflare_compat(self, mock_page):
        """Test backward compatible Cloudflare wait."""
        from app.detections.handler import wait_for_cloudflare

        result = wait_for_cloudflare(mock_page, max_wait=1)
        assert result is True  # No Cloudflare = success


# === INTEGRATION TESTS ===

class TestPluginIntegration:
    """Integration tests for the plugin system."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset the singleton before each test."""
        from app.detections.registry import DetectionRegistry
        DetectionRegistry.reset()
        yield
        DetectionRegistry.reset()

    def test_all_plugins_load(self):
        """Test that all plugins load without errors."""
        from app.detections.registry import DetectionRegistry

        registry = DetectionRegistry()

        # Verify plugins that don't require API keys
        expected_without_api = ["cloudflare", "perimeterx", "datadome"]
        for name in expected_without_api:
            assert name in registry.list_all(), f"Plugin {name} not loaded"

    def test_all_plugins_load_with_api(self):
        """Test all plugins load when API is configured."""
        from app.detections.registry import DetectionRegistry
        DetectionRegistry.reset()

        config = {"captcha": {"enabled": True, "api_key": "test-key", "service": "2captcha"}}
        registry = DetectionRegistry(config=config)

        # All plugins should load
        expected = ["cloudflare", "recaptcha", "hcaptcha", "perimeterx", "datadome"]
        for name in expected:
            assert name in registry.list_all(), f"Plugin {name} not loaded"

    def test_plugins_have_required_attributes(self):
        """Test that all plugins have required attributes."""
        from app.detections.registry import DetectionRegistry

        registry = DetectionRegistry()

        for name in registry.list_all():
            detection = registry.get(name)
            assert hasattr(detection, 'name')
            assert hasattr(detection, 'priority')
            assert hasattr(detection, 'category')
            assert hasattr(detection, 'detect')
            assert hasattr(detection, 'solve')
            assert callable(detection.detect)
            assert callable(detection.solve)

    def test_detect_method_returns_correct_type(self):
        """Test that detect() returns DetectionResult."""
        from app.detections.registry import DetectionRegistry
        from app.detections.base import DetectionResult

        mock_page = MagicMock()
        mock_page.locator.return_value.count.return_value = 0
        mock_page.title.return_value = "Test"
        mock_page.content.return_value = "<html></html>"

        registry = DetectionRegistry()

        for name in registry.list_all():
            detection = registry.get(name)
            result = detection.detect(mock_page, "https://example.com")
            assert isinstance(result, DetectionResult), f"{name} detect() returned wrong type"
