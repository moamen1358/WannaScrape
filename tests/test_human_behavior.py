"""
Tests for human behavior simulation.
"""

import pytest
from unittest.mock import MagicMock, patch
import random

from app.utils.human_behavior import (
    human_delay,
    bezier_point,
    ease_out_cubic,
    ease_in_out_sine,
    add_noise,
    BehaviorType,
    AdvancedMouseSimulator,
    AdvancedScrollSimulator,
    simulate_human_behavior,
)


class TestHumanDelay:
    """Tests for human_delay function."""
    
    def test_delay_within_range(self):
        """Test delay is roughly within expected range."""
        for _ in range(100):
            delay = human_delay(0.5, 2.0)
            # Allow some variance due to gaussian distribution
            assert 0.1 <= delay <= 4.0
    
    def test_delay_respects_min_max(self):
        """Test delay respects min/max bounds."""
        delay = human_delay(1.0, 1.0)
        assert 0.5 <= delay <= 1.5  # With variance


class TestBezierPoint:
    """Tests for bezier curve calculation."""
    
    def test_bezier_start_point(self):
        """Test bezier at t=0 returns start point."""
        result = bezier_point(0, 0, 100, 200, 300)
        assert result == 0
    
    def test_bezier_end_point(self):
        """Test bezier at t=1 returns end point."""
        result = bezier_point(1, 0, 100, 200, 300)
        assert result == 300
    
    def test_bezier_midpoint(self):
        """Test bezier at t=0.5 returns intermediate value."""
        result = bezier_point(0.5, 0, 0, 100, 100)
        assert 0 < result < 100


class TestEasingFunctions:
    """Tests for easing functions."""
    
    def test_ease_out_cubic_bounds(self):
        """Test ease_out_cubic at boundaries."""
        assert ease_out_cubic(0) == 0
        assert ease_out_cubic(1) == 1
    
    def test_ease_out_cubic_acceleration(self):
        """Test ease_out_cubic accelerates then decelerates."""
        # Early values should be higher than linear
        assert ease_out_cubic(0.5) > 0.5
    
    def test_ease_in_out_sine_bounds(self):
        """Test ease_in_out_sine at boundaries."""
        assert abs(ease_in_out_sine(0)) < 0.001
        assert abs(ease_in_out_sine(1) - 1) < 0.001
    
    def test_ease_in_out_sine_symmetry(self):
        """Test ease_in_out_sine is symmetric."""
        assert abs(ease_in_out_sine(0.5) - 0.5) < 0.001


class TestAddNoise:
    """Tests for noise function."""
    
    def test_noise_adds_variation(self):
        """Test noise adds variation to value."""
        values = [add_noise(100, 5) for _ in range(100)]
        # Should have some variance
        assert max(values) != min(values)
    
    def test_noise_centered_on_value(self):
        """Test noise is centered on original value."""
        values = [add_noise(100, 2) for _ in range(1000)]
        avg = sum(values) / len(values)
        assert 95 < avg < 105  # Should average close to 100


class TestBehaviorType:
    """Tests for BehaviorType enum."""
    
    def test_behavior_types(self):
        """Test all behavior types exist."""
        assert BehaviorType.READER.value == "reader"
        assert BehaviorType.SKIMMER.value == "skimmer"
        assert BehaviorType.SEARCHER.value == "searcher"


class TestAdvancedMouseSimulator:
    """Tests for AdvancedMouseSimulator."""
    
    @pytest.fixture
    def mock_page(self):
        """Create mock page object."""
        page = MagicMock()
        page.mouse = MagicMock()
        page.evaluate = MagicMock(return_value=None)
        return page
    
    def test_initialization(self, mock_page):
        """Test mouse simulator initialization."""
        mouse = AdvancedMouseSimulator(mock_page, 1920, 1080)
        assert mouse.width == 1920
        assert mouse.height == 1080
        assert mouse.move_count == 0
    
    def test_random_movement_calls_move(self, mock_page):
        """Test random_movement generates movement."""
        mouse = AdvancedMouseSimulator(mock_page, 1920, 1080)
        target = mouse.random_movement()
        
        assert isinstance(target, tuple)
        assert len(target) == 2
        assert mock_page.mouse.move.called
    
    def test_move_to_updates_position(self, mock_page):
        """Test move_to updates current position."""
        mouse = AdvancedMouseSimulator(mock_page, 1920, 1080)
        mouse.move_to(500, 500)
        
        assert mouse.current_x == 500
        assert mouse.current_y == 500
        assert mouse.move_count == 1


class TestAdvancedScrollSimulator:
    """Tests for AdvancedScrollSimulator."""
    
    @pytest.fixture
    def mock_page(self):
        """Create mock page object."""
        page = MagicMock()
        page.evaluate = MagicMock(return_value=3000)  # Page height
        return page
    
    def test_initialization(self, mock_page):
        """Test scroll simulator initialization."""
        scroll = AdvancedScrollSimulator(mock_page)
        assert scroll.current_position == 0
        assert scroll.scroll_count == 0
    
    def test_smooth_scroll(self, mock_page):
        """Test smooth scroll updates position."""
        scroll = AdvancedScrollSimulator(mock_page)
        scroll.smooth_scroll(500)
        
        assert scroll.current_position > 0
        assert scroll.scroll_count == 1
        assert mock_page.evaluate.called
    
    def test_quick_scroll(self, mock_page):
        """Test quick scroll."""
        scroll = AdvancedScrollSimulator(mock_page)
        scroll.quick_scroll(300)
        
        assert scroll.scroll_count == 1


class TestSimulateHumanBehavior:
    """Tests for simulate_human_behavior function."""
    
    @pytest.fixture
    def mock_page(self):
        """Create mock page object."""
        page = MagicMock()
        page.viewport_size = {"width": 1920, "height": 1080}
        page.mouse = MagicMock()
        page.evaluate = MagicMock(return_value=3000)
        return page
    
    def test_returns_stats(self, mock_page):
        """Test function returns stats dictionary."""
        stats = simulate_human_behavior(mock_page)
        
        assert "mouse_moves" in stats
        assert "scrolls" in stats
        assert "behavior_type" in stats
    
    def test_mouse_moves_in_range(self, mock_page):
        """Test mouse moves are within 1-3 range."""
        random.seed(42)  # For reproducibility
        stats = simulate_human_behavior(mock_page)
        
        # Base moves should be 1-3, might have extra from scroll phase
        assert 1 <= stats["mouse_moves"] <= 6
    
    def test_scrolls_in_range(self, mock_page):
        """Test scrolls are within 1-3 range."""
        random.seed(42)
        stats = simulate_human_behavior(mock_page)
        
        assert 1 <= stats["scrolls"] <= 3
    
    def test_behavior_type_valid(self, mock_page):
        """Test behavior type is one of valid types."""
        stats = simulate_human_behavior(mock_page)
        
        assert stats["behavior_type"] in ["reader", "skimmer", "searcher"]
