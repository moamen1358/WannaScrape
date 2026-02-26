"""
Advanced Human Behavior Simulation for Anti-Detection.

Simulates realistic human browsing patterns:
- Natural mouse movements with bezier curves and micro-movements
- Reading pauses and scanning behavior
- Variable scrolling (fast skim, slow read, back-scroll)
- Random hesitations and cursor idle patterns
- Different behavior patterns (reader, skimmer, searcher)
"""

import time
import math
import random
import logging
from typing import Optional, Dict, Tuple, List
from enum import Enum

logger = logging.getLogger("scraper.human")


class BehaviorType(Enum):
    """Different browsing behavior patterns."""
    READER = "reader"      # Slow, methodical reading
    SKIMMER = "skimmer"    # Fast scanning
    SEARCHER = "searcher"  # Looking for specific content


def human_delay(min_sec: float = 0.5, max_sec: float = 2.0) -> float:
    """Generate human-like delay using normal distribution."""
    mean = (min_sec + max_sec) / 2
    std_dev = (max_sec - min_sec) / 4
    delay = random.gauss(mean, std_dev)
    return max(min_sec * 0.5, min(max_sec * 1.5, delay))


def bezier_point(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Calculate point on cubic bezier curve."""
    u = 1 - t
    return u**3 * p0 + 3 * u**2 * t * p1 + 3 * u * t**2 * p2 + t**3 * p3


def ease_out_cubic(t: float) -> float:
    """Natural deceleration easing."""
    return 1 - pow(1 - t, 3)


def ease_in_out_sine(t: float) -> float:
    """Smooth acceleration and deceleration."""
    return -(math.cos(math.pi * t) - 1) / 2


def add_noise(value: float, intensity: float = 2.0) -> float:
    """Add small random noise to simulate hand tremor."""
    return value + random.gauss(0, intensity)


class AdvancedMouseSimulator:
    """
    Simulates realistic mouse movements like a real human.
    
    Features:
    - Bezier curve paths (not straight lines)
    - Variable speed (slow start, fast middle, slow end)
    - Micro-movements and hand tremor
    - Random pauses and hesitations
    - Visual cursor for debugging (in headful mode)
    """

    def __init__(self, page, viewport_width: int, viewport_height: int):
        self.page = page
        self.width = viewport_width
        self.height = viewport_height
        self.current_x = random.randint(100, viewport_width // 2)
        self.current_y = random.randint(100, viewport_height // 3)
        self.move_count = 0
        self.cursor_injected = False

    def _inject_visual_cursor(self):
        """Inject a visible cursor element for debugging."""
        if self.cursor_injected:
            return
        try:
            self.page.evaluate("""
                () => {
                    if (document.getElementById('debug-cursor')) return;
                    const cursor = document.createElement('div');
                    cursor.id = 'debug-cursor';
                    cursor.style.cssText = `
                        position: fixed;
                        width: 20px;
                        height: 20px;
                        background: rgba(255, 0, 0, 0.7);
                        border: 2px solid white;
                        border-radius: 50%;
                        pointer-events: none;
                        z-index: 999999;
                        transform: translate(-50%, -50%);
                        box-shadow: 0 0 10px rgba(255,0,0,0.5);
                        transition: left 0.05s, top 0.05s;
                    `;
                    document.body.appendChild(cursor);
                    
                    document.addEventListener('mousemove', (e) => {
                        cursor.style.left = e.clientX + 'px';
                        cursor.style.top = e.clientY + 'px';
                    });
                }
            """)
            self.cursor_injected = True
            logger.debug("Visual cursor injected for debugging")
        except Exception as e:
            logger.debug(f"Could not inject visual cursor: {e}")

    def _generate_control_points(self, start_x: float, start_y: float,
                                  end_x: float, end_y: float) -> List[Tuple[float, float]]:
        """Generate bezier control points for natural curved path."""
        distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)

        # Calculate perpendicular direction for curve offset
        dx = end_x - start_x
        dy = end_y - start_y

        # Perpendicular vector (rotated 90 degrees)
        perp_x = -dy
        perp_y = dx

        # Normalize perpendicular
        perp_len = math.sqrt(perp_x**2 + perp_y**2)
        if perp_len > 0:
            perp_x /= perp_len
            perp_y /= perp_len

        # Curve offset: 15-40% of distance, perpendicular to straight line
        curve_offset = distance * random.uniform(0.15, 0.40)
        curve_dir = random.choice([-1, 1])

        # Control point 1: ~30% along path, offset perpendicular
        cp1_x = start_x + dx * 0.3 + perp_x * curve_offset * curve_dir
        cp1_y = start_y + dy * 0.3 + perp_y * curve_offset * curve_dir

        # Control point 2: ~70% along path, offset perpendicular (same direction)
        cp2_x = start_x + dx * 0.7 + perp_x * curve_offset * curve_dir * 0.6
        cp2_y = start_y + dy * 0.7 + perp_y * curve_offset * curve_dir * 0.6

        return [(cp1_x, cp1_y), (cp2_x, cp2_y)]

    def _calculate_speed(self, t: float, total_distance: float) -> float:
        """Calculate movement speed - slow at ends, fast in middle."""
        base_speed = 0.003 + (total_distance / 10000)

        if t < 0.15:
            speed_mult = 0.3 + (t / 0.15) * 0.7
        elif t > 0.85:
            speed_mult = 0.3 + ((1 - t) / 0.15) * 0.7
        else:
            speed_mult = 1.0 + random.uniform(-0.1, 0.1)

        return base_speed * speed_mult

    def move_to(self, target_x: float, target_y: float, smooth: bool = True):
        """Move mouse to target with natural bezier curve motion."""
        try:
            # Inject visual cursor for debugging
            self._inject_visual_cursor()

            target_x = max(10, min(self.width - 10, target_x))
            target_y = max(10, min(self.height - 10, target_y))

            distance = math.sqrt((target_x - self.current_x)**2 + (target_y - self.current_y)**2)

            if distance < 5:
                return

            # Log the movement
            logger.debug(f"🖱️ Moving: ({int(self.current_x)}, {int(self.current_y)}) → ({int(target_x)}, {int(target_y)}) [{int(distance)}px]")

            # Fast but smooth: 10-25 steps based on distance
            steps = max(10, min(25, int(distance / 20)))

            if smooth:
                control_points = self._generate_control_points(
                    self.current_x, self.current_y, target_x, target_y
                )
                cp1_x, cp1_y = control_points[0]
                cp2_x, cp2_y = control_points[1]

                for i in range(steps + 1):
                    t = i / steps
                    eased_t = ease_in_out_sine(t)

                    x = bezier_point(eased_t, self.current_x, cp1_x, cp2_x, target_x)
                    y = bezier_point(eased_t, self.current_y, cp1_y, cp2_y, target_y)

                    tremor = 1.0 if (t < 0.2 or t > 0.8) else 0.3
                    x = add_noise(x, tremor)
                    y = add_noise(y, tremor)

                    x = max(5, min(self.width - 5, x))
                    y = max(5, min(self.height - 5, y))

                    self.page.mouse.move(x, y)

                    # Fast: 2-5ms per step (total move = 20-125ms)
                    time.sleep(random.uniform(0.002, 0.005))
            else:
                self.page.mouse.move(target_x, target_y)

            self.current_x = target_x
            self.current_y = target_y
            self.move_count += 1

        except Exception as e:
            logger.debug(f"Mouse move error: {e}")
            try:
                self.page.mouse.move(target_x, target_y)
            except Exception:
                pass

    def random_movement(self) -> Tuple[float, float]:
        """Make a random natural movement to a new position."""
        zones = [
            (0.3, 0.7, 0.2, 0.5, 0.4),   # Main content area
            (0.1, 0.3, 0.1, 0.3, 0.2),   # Top-left
            (0.5, 0.9, 0.3, 0.7, 0.2),   # Right side
            (0.2, 0.8, 0.6, 0.9, 0.2),   # Bottom
        ]

        r = random.random()
        cumulative = 0
        chosen_zone = zones[0]
        for zone in zones:
            cumulative += zone[4]
            if r < cumulative:
                chosen_zone = zone
                break

        target_x = random.uniform(self.width * chosen_zone[0], self.width * chosen_zone[1])
        target_y = random.uniform(self.height * chosen_zone[2], self.height * chosen_zone[3])

        self.move_to(target_x, target_y)
        return (target_x, target_y)

    def hover_and_read(self, duration: float = None):
        """Simulate hovering while reading - small micro-movements."""
        if duration is None:
            duration = random.uniform(0.05, 0.15)  # Very short

        start_time = time.time()
        start_x, start_y = self.current_x, self.current_y

        # Just 2-3 micro movements
        for _ in range(random.randint(2, 3)):
            if time.time() - start_time >= duration:
                break
            drift_x = random.gauss(0, 2)
            drift_y = random.gauss(1, 0.5)

            new_x = max(10, min(self.width - 10, start_x + drift_x))
            new_y = max(10, min(self.height - 10, start_y + drift_y))

            self.page.mouse.move(new_x, new_y)
            time.sleep(random.uniform(0.01, 0.03))

            start_x, start_y = new_x, new_y

        self.current_x, self.current_y = start_x, start_y

    def idle_micro_movements(self, duration: float = 0.1):
        """Small idle movements when thinking or pausing."""
        # Just 2-4 quick micro movements
        for _ in range(random.randint(2, 4)):
            offset_x = random.gauss(0, 1.5)
            offset_y = random.gauss(0, 1.5)

            new_x = self.current_x + offset_x
            new_y = self.current_y + offset_y

            self.page.mouse.move(new_x, new_y)
            time.sleep(random.uniform(0.01, 0.02))


class AdvancedScrollSimulator:
    """
    Simulates realistic scrolling behavior.
    
    Features:
    - Variable scroll speeds
    - Back-scrolling
    - Pause to read sections
    """

    def __init__(self, page):
        self.page = page
        self.current_position = 0
        self.scroll_count = 0
        self.page_height = 2000
        self.viewport_height = 800

    def _get_page_info(self):
        """Get current page dimensions."""
        try:
            self.page_height = self.page.evaluate("document.body.scrollHeight") or 2000
            self.viewport_height = self.page.evaluate("window.innerHeight") or 800
            self.current_position = self.page.evaluate("window.pageYOffset") or 0
        except Exception:
            pass

    def smooth_scroll(self, amount: int, duration: float = None):
        """Scroll smoothly by amount pixels."""
        if duration is None:
            duration = random.uniform(0.1, 0.2)  # Fast scroll

        target = max(0, min(self.page_height - self.viewport_height,
                           self.current_position + amount))

        steps = max(3, int(abs(amount) / 80))  # Fewer steps
        step_delay = duration / steps

        for i in range(steps):
            t = (i + 1) / steps
            eased_t = ease_out_cubic(t)

            current = self.current_position + (target - self.current_position) * eased_t

            try:
                self.page.evaluate(f"window.scrollTo(0, {int(current)})")
            except Exception:
                pass

            time.sleep(step_delay)

        self.current_position = target
        self.scroll_count += 1

    def quick_scroll(self, amount: int):
        """Quick scroll like using scroll wheel."""
        target = max(0, min(self.page_height - self.viewport_height,
                           self.current_position + amount))

        try:
            self.page.evaluate(f"window.scrollTo({{top: {target}, behavior: 'smooth'}})")
        except Exception:
            pass

        self.current_position = target
        self.scroll_count += 1
        time.sleep(random.uniform(0.2, 0.4))

    def read_scroll(self):
        """Scroll while reading."""
        self._get_page_info()
        amount = random.randint(150, 350)
        self.smooth_scroll(amount, duration=random.uniform(0.1, 0.2))
        time.sleep(random.uniform(0.05, 0.1))  # Brief pause

    def skim_scroll(self):
        """Fast scroll to skim content."""
        self._get_page_info()
        amount = random.randint(400, 700)
        self.quick_scroll(amount)

    def back_scroll(self):
        """Scroll back up."""
        self._get_page_info()
        if self.current_position > 100:
            amount = random.randint(100, 250)
            self.smooth_scroll(-amount, duration=random.uniform(0.1, 0.15))

    def scroll_to_content(self):
        """Scroll to main content area."""
        self._get_page_info()
        target = random.randint(150, 300)
        if self.current_position < target:
            self.smooth_scroll(target - self.current_position, duration=0.1)


def simulate_human_behavior(page, config: dict = None, speed: str = None) -> dict:
    """
    Advanced human behavior simulation.
    
    Simulates realistic browsing:
    1. Initial page load pause
    2. Random mouse movements (1-5)
    3. Scroll to content
    4. Reading behavior with pauses
    5. Occasional back-scroll
    
    Args:
        page: Playwright page object
        config: Scraper config dict
        speed: Override speed — "fast", "normal", or "stealth". 
               "fast" = minimal simulation (~1s), 
               "normal" = standard (~3-5s), 
               "stealth" = thorough (~5-8s)
    """
    stats = {"mouse_moves": 0, "scrolls": 0, "behavior_type": "mixed"}

    # Determine speed mode
    if speed is None:
        speed = (config or {}).get("human_behavior", {}).get("speed", "fast")

    try:
        start_time = time.time()

        try:
            viewport = page.viewport_size
            if viewport:
                width, height = viewport['width'], viewport['height']
            else:
                width = page.evaluate("window.innerWidth") or 1920
                height = page.evaluate("window.innerHeight") or 1080
        except Exception:
            width, height = 1920, 1080

        mouse = AdvancedMouseSimulator(page, width, height)
        scroll = AdvancedScrollSimulator(page)

        # ── FAST MODE: minimal simulation for speed ──
        if speed == "fast":
            behavior = random.choice(list(BehaviorType))
            stats["behavior_type"] = behavior.value
            logger.info("🎭 Behavior: FAST mode (minimal)")
            # Just 1 mouse move + 1 scroll — enough to look human
            mouse.random_movement()
            stats["mouse_moves"] = 1
            time.sleep(random.uniform(0.05, 0.15))
            scroll.scroll_to_content()
            stats["scrolls"] = 1
            elapsed = time.time() - start_time
            logger.info(f"✅ Human behavior (fast): {elapsed:.2f}s")
            return stats

        behavior = random.choice(list(BehaviorType))
        stats["behavior_type"] = behavior.value

        logger.info(f"🎭 Behavior type: {behavior.value.upper()}")

        # Phase 1: Brief initial pause
        initial_pause = random.uniform(0.1, 0.2)
        time.sleep(initial_pause)

        # Phase 2: Mouse movements (1-3 random)
        num_movements = random.randint(1, 3)
        logger.info(f"🖱️ Performing {num_movements} mouse movements")

        for i in range(num_movements):
            pattern = random.random()

            if pattern < 0.5:
                mouse.random_movement()
            elif pattern < 0.8:
                mouse.random_movement()
                mouse.hover_and_read()  # Very brief
            else:
                target_x = random.randint(100, width - 100)
                target_y = random.randint(100, height - 100)
                mouse.move_to(target_x, target_y)

            # Brief pause between movements (20-80ms)
            if i < num_movements - 1:
                time.sleep(random.uniform(0.02, 0.08))

        stats["mouse_moves"] = num_movements

        # Phase 3: Scrolling (1-3 random)
        scroll.scroll_to_content()
        num_scrolls = random.randint(1, 3)
        logger.info(f"📜 Performing {num_scrolls} scroll actions")

        for i in range(num_scrolls):
            scroll_type = random.random()

            if behavior == BehaviorType.READER:
                if scroll_type < 0.7:
                    scroll.read_scroll()
                elif scroll_type < 0.9:
                    scroll.smooth_scroll(random.randint(200, 400))
                else:
                    scroll.back_scroll()

            elif behavior == BehaviorType.SKIMMER:
                if scroll_type < 0.6:
                    scroll.skim_scroll()
                elif scroll_type < 0.8:
                    scroll.quick_scroll(random.randint(300, 600))
                else:
                    scroll.read_scroll()

            else:  # SEARCHER
                if scroll_type < 0.5:
                    scroll.skim_scroll()
                elif scroll_type < 0.8:
                    scroll.read_scroll()
                else:
                    scroll.back_scroll()

            # Occasional mouse move during scroll
            if random.random() < 0.15:
                mouse.random_movement()
                stats["mouse_moves"] += 1

            # Brief pause between scrolls
            if i < num_scrolls - 1:
                time.sleep(random.uniform(0.03, 0.08))

        stats["scrolls"] = num_scrolls

        # Phase 4: Final (optional quick move)
        if random.random() < 0.3:
            target_x = random.randint(int(width * 0.2), int(width * 0.7))
            target_y = random.randint(int(height * 0.3), int(height * 0.6))
            mouse.move_to(target_x, target_y)
            stats["mouse_moves"] += 1

        elapsed = time.time() - start_time
        logger.info(f"✅ Human behavior: {stats['mouse_moves']} moves, {stats['scrolls']} scrolls in {elapsed:.2f}s")

        return stats

    except Exception as e:
        logger.warning(f"Human behavior error: {e}")
        return stats


def simulate_mouse_movement(page, num_movements: int = None, config: dict = None):
    """Legacy function for compatibility."""
    try:
        viewport = page.viewport_size or {"width": 1920, "height": 1080}
        mouse = AdvancedMouseSimulator(page, viewport['width'], viewport['height'])

        if num_movements is None:
            num_movements = random.randint(2, 4)

        for _ in range(num_movements):
            mouse.random_movement()
            time.sleep(random.uniform(0.1, 0.3))

    except Exception as e:
        logger.warning(f"Mouse simulation error: {e}")


def simulate_scroll(page, scroll_down: bool = True, config: dict = None):
    """Legacy function for compatibility."""
    try:
        scroll = AdvancedScrollSimulator(page)

        if scroll_down:
            for _ in range(random.randint(2, 4)):
                scroll.read_scroll()
        else:
            scroll.back_scroll()

    except Exception as e:
        logger.warning(f"Scroll simulation error: {e}")


def human_mouse_move(page, target_x: float, target_y: float, steps: int = 25):
    """Move mouse to specific target with natural motion."""
    try:
        viewport = page.viewport_size or {"width": 1920, "height": 1080}
        mouse = AdvancedMouseSimulator(page, viewport['width'], viewport['height'])
        mouse.move_to(target_x, target_y, smooth=True)
    except Exception:
        try:
            page.mouse.move(target_x, target_y)
        except Exception:
            pass


def type_like_human(page, selector: str, text: str,
                    min_delay: int = 50, max_delay: int = 150):
    """
    Type text with human-like delays between keystrokes.

    Includes occasional typos and corrections for realism.

    Args:
        page: Playwright page object
        selector: CSS selector for input element
        text: Text to type
        min_delay: Minimum delay between keystrokes in ms
        max_delay: Maximum delay between keystrokes in ms
    """
    element = page.locator(selector)
    element.focus()

    for char in text:
        # Occasional typo (3% chance)
        if random.random() < 0.03 and char.isalpha():
            # Type wrong character
            wrong_char = chr(ord(char) + random.choice([-1, 1]))
            page.keyboard.type(wrong_char)
            time.sleep(random.uniform(0.1, 0.3))
            # Backspace and correct
            page.keyboard.press("Backspace")
            time.sleep(random.uniform(0.05, 0.15))

        # Type the character
        page.keyboard.type(char)

        # Variable delay
        delay = random.randint(min_delay, max_delay)

        # Longer pause after punctuation
        if char in ".,!?;:":
            delay *= 2

        # Occasional longer pause (thinking)
        if random.random() < 0.05:
            delay *= 3

        time.sleep(delay / 1000)


def move_mouse_naturally(page, target_x: int, target_y: int, duration: float = 0.5):
    """
    Move mouse using bezier curves for natural-looking movement.

    Args:
        page: Playwright page object
        target_x: Target X coordinate
        target_y: Target Y coordinate
        duration: Duration of movement in seconds
    """
    try:
        # Get current position (approximate from viewport)
        viewport = page.viewport_size
        if not viewport:
            return

        # Start from random edge position
        start_x = random.randint(0, viewport['width'])
        start_y = random.randint(0, viewport['height'])

        # Generate bezier control points
        ctrl1_x = start_x + (target_x - start_x) * 0.3 + random.randint(-50, 50)
        ctrl1_y = start_y + (target_y - start_y) * 0.3 + random.randint(-50, 50)
        ctrl2_x = start_x + (target_x - start_x) * 0.7 + random.randint(-50, 50)
        ctrl2_y = start_y + (target_y - start_y) * 0.7 + random.randint(-50, 50)

        # Number of steps
        steps = int(duration * 60)  # 60 fps

        for i in range(steps + 1):
            t = i / steps

            # Bezier curve calculation
            u = 1 - t
            x = u**3 * start_x + 3 * u**2 * t * ctrl1_x + 3 * u * t**2 * ctrl2_x + t**3 * target_x
            y = u**3 * start_y + 3 * u**2 * t * ctrl1_y + 3 * u * t**2 * ctrl2_y + t**3 * target_y

            page.mouse.move(x, y)
            time.sleep(duration / steps)

    except Exception as e:
        logger.debug(f"Natural mouse movement skipped: {e}")
