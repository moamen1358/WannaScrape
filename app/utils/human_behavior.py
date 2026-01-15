"""
Human behavior simulation for anti-detection.
Simulates realistic mouse movements, scrolling, and timing.
"""

import time
import math
import random
import logging
from typing import Optional

logger = logging.getLogger("scraper.human")


def human_delay(min_sec: float = 2.0, max_sec: float = 6.0) -> float:
    """Generate human-like delay using normal distribution (bell curve)."""
    mean = (min_sec + max_sec) / 2
    std_dev = (max_sec - min_sec) / 4
    delay = random.gauss(mean, std_dev)
    return max(min_sec * 0.5, min(max_sec * 1.5, delay))


def bezier_curve(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Calculate point on cubic bezier curve at parameter t (0-1)."""
    u = 1 - t
    return u**3 * p0 + 3 * u**2 * t * p1 + 3 * u * t**2 * p2 + t**3 * p3


def ease_out_quad(t: float) -> float:
    """Easing function for natural deceleration."""
    return 1 - (1 - t) ** 2


def simulate_mouse_movement(page, num_movements: int = None, config: dict = None):
    """
    Simulate realistic human mouse movements.

    Args:
        page: Playwright page object
        num_movements: Number of movements (uses config if None)
        config: Configuration dict with human_behavior settings
    """
    try:
        hb_config = config.get("human_behavior", {}) if config else {}
        movement_speed = hb_config.get("movement_speed", 0.008)
        pause_config = hb_config.get("pause_between_actions", {"min": 0.1, "max": 0.3})

        viewport = page.viewport_size
        if not viewport:
            try:
                width = page.evaluate("window.innerWidth") or 1920
                height = page.evaluate("window.innerHeight") or 1080
            except:
                width, height = 1920, 1080
        else:
            width, height = viewport['width'], viewport['height']

        if num_movements is None:
            mv_config = hb_config.get("mouse_movements", {"min": 2, "max": 3})
            num_movements = random.randint(mv_config.get("min", 2), mv_config.get("max", 3))

        logger.debug(f"Mouse: {num_movements} moves in {width}x{height}")

        current_x = random.randint(100, min(width // 3, width - 100))
        current_y = random.randint(100, min(height // 3, height - 100))
        page.mouse.move(current_x, current_y)

        for _ in range(num_movements):
            target_x = random.randint(100, max(200, width - 100))
            target_y = random.randint(150, max(200, height - 150))
            steps = random.randint(10, 15)

            for i in range(steps + 1):
                t = i / steps
                curve = math.sin(t * math.pi) * 10
                x = max(10, min(width - 10, current_x + (target_x - current_x) * t + curve))
                y = max(10, min(height - 10, current_y + (target_y - current_y) * t))
                page.mouse.move(x, y)
                time.sleep(movement_speed)

            current_x, current_y = target_x, target_y
            time.sleep(random.uniform(pause_config.get("min", 0.1), pause_config.get("max", 0.3)))

        logger.debug(f"Mouse completed: {num_movements} moves")
    except Exception as e:
        logger.warning(f"Mouse simulation error: {e}")


def simulate_scroll(page, scroll_down: bool = True, config: dict = None):
    """
    Simulate realistic human scrolling behavior.

    Args:
        page: Playwright page object
        scroll_down: Direction of scroll
        config: Configuration dict with human_behavior settings
    """
    try:
        hb_config = config.get("human_behavior", {}) if config else {}
        scroll_config = hb_config.get("scroll_actions", {"min": 2, "max": 3})
        pause_config = hb_config.get("pause_between_actions", {"min": 0.1, "max": 0.3})

        page_height = page.evaluate("document.body.scrollHeight") or 2000
        viewport_height = page.evaluate("window.innerHeight") or 800

        logger.debug(f"Scroll: page={page_height}px, viewport={viewport_height}px")

        if scroll_down:
            scroll_count = random.randint(scroll_config.get("min", 2), scroll_config.get("max", 3))
            max_scroll = min(page_height - viewport_height, page_height * 0.5)
            max_scroll = max(max_scroll, 300)
            current_pos = 0

            for _ in range(scroll_count):
                scroll_amount = random.randint(250, 450)
                target_pos = min(current_pos + scroll_amount, max_scroll)
                page.evaluate(f"window.scrollTo({{top: {target_pos}, behavior: 'smooth'}})")
                current_pos = target_pos
                time.sleep(random.uniform(pause_config.get("min", 0.1), pause_config.get("max", 0.3)))

            if random.random() < 0.2:
                back_amount = random.randint(100, 200)
                page.evaluate(f"window.scrollTo({{top: {max(0, current_pos - back_amount)}, behavior: 'smooth'}})")
                time.sleep(random.uniform(0.1, 0.2))

            logger.debug(f"Scroll completed: {scroll_count} scrolls, reached {current_pos}px")
    except Exception as e:
        logger.warning(f"Scroll simulation error: {e}")


def simulate_human_behavior(page, config: dict = None):
    """
    Combined human behavior simulation.
    Runs mouse movements and scrolling in ~2-4 seconds.

    Args:
        page: Playwright page object
        config: Configuration dict
    """
    try:
        logger.info("Starting human behavior simulation...")
        start_time = time.time()

        time.sleep(random.uniform(0.1, 0.2))
        simulate_mouse_movement(page, config=config)
        time.sleep(random.uniform(0.1, 0.2))
        simulate_scroll(page, config=config)

        elapsed = time.time() - start_time
        logger.info(f"Human behavior completed in {elapsed:.1f}s")

    except Exception as e:
        logger.warning(f"Human behavior error: {e}")


def human_mouse_move(page, target_x: float, target_y: float, steps: int = 25):
    """
    Move mouse to target with human-like bezier curve motion.
    Used for precise movements (e.g., clicking buttons).
    """
    try:
        current = page.evaluate("() => ({x: window.innerWidth/2, y: window.innerHeight/2})")
        start_x = current.get('x', 500)
        start_y = current.get('y', 500)

        cp1_x = start_x + (target_x - start_x) * random.uniform(0.2, 0.4) + random.uniform(-50, 50)
        cp1_y = start_y + (target_y - start_y) * random.uniform(0.2, 0.4) + random.uniform(-50, 50)
        cp2_x = start_x + (target_x - start_x) * random.uniform(0.6, 0.8) + random.uniform(-50, 50)
        cp2_y = start_y + (target_y - start_y) * random.uniform(0.6, 0.8) + random.uniform(-50, 50)

        for i in range(steps):
            t = i / steps
            x = (1-t)**3 * start_x + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * target_x
            y = (1-t)**3 * start_y + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * target_y

            x += random.uniform(-1, 1)
            y += random.uniform(-1, 1)

            page.mouse.move(x, y)

            if t < 0.2 or t > 0.8:
                time.sleep(random.uniform(0.01, 0.03))
            else:
                time.sleep(random.uniform(0.005, 0.015))

        page.mouse.move(target_x, target_y)
    except Exception as e:
        page.mouse.move(target_x, target_y, steps=steps)
