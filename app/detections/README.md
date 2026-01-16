# Detection Plugin System

A scalable, plugin-based architecture for handling bot detection systems.

## Quick Start (Adding a New Detection)

**Total time: < 10 minutes**

### Step 1: Create a new file

```bash
touch app/detections/mydetection.py
```

### Step 2: Copy this template

```python
"""
MyDetection Plugin
==================
Brief description of what this detects.
"""

import logging
from playwright.sync_api import Page

from .base import (
    BaseDetection,
    DetectionResult,
    DetectionCategory,
    SolveMethod
)

logger = logging.getLogger("scraper.detections.mydetection")


class MyDetection(BaseDetection):
    """Description of your detection."""

    # === REQUIRED: Unique identifier ===
    name = "mydetection"

    # === REQUIRED: Lower number = runs first ===
    priority = 50

    # === REQUIRED: Category type ===
    category = DetectionCategory.CHALLENGE  # or CAPTCHA, FINGERPRINT, BEHAVIORAL

    # === OPTIONAL: Human-readable description ===
    description = "My custom bot detection handler"

    # === OPTIONAL: Does it need an API key? ===
    requires_api = False

    # === OPTIONAL: Max time to solve (seconds) ===
    solve_timeout = 30

    # === DETECTION PATTERNS ===
    selectors = [
        "#my-challenge",
        ".my-captcha",
        "iframe[src*='myservice']",
    ]

    title_indicators = [
        "blocked",
        "verify",
    ]

    content_indicators = [
        "mydetection",
        "please verify",
    ]

    def detect(self, page: Page, url: str) -> DetectionResult:
        """
        Check if this detection is present.

        Returns DetectionResult with detected=True/False.
        """
        # Use helper methods from base class
        matched_selector = self._check_selectors(page)
        if matched_selector:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=1.0,
                details={"selector": matched_selector},
                solve_method=SolveMethod.WAIT  # or API, BEHAVIORAL, BYPASS
            )

        # Not detected
        return DetectionResult(
            detected=False,
            detection_type=self.name
        )

    def solve(
        self,
        page: Page,
        url: str,
        detection_result: DetectionResult
    ) -> bool:
        """
        Attempt to solve this detection.

        Returns True if solved, False otherwise.
        """
        logger.info(f"Attempting to solve {self.name}...")

        # Your solving logic here
        # ...

        return True  # or False if failed
```

### Step 3: That's it!

The plugin is automatically discovered and registered. No other files need to be modified.

```bash
# Run tests to verify
pytest tests/test_detections.py -v

# Use in your code
from app.detections import DetectionRegistry
registry = DetectionRegistry()
print(registry.list_all())  # Your detection should appear
```

---

## Architecture Overview

```
app/detections/
├── __init__.py       # Public API exports
├── base.py           # BaseDetection abstract class
├── registry.py       # Auto-discovery and registration
├── handler.py        # High-level interface for scraper
├── README.md         # This file
│
├── cloudflare.py     # Cloudflare detection plugin
├── recaptcha.py      # reCAPTCHA detection plugin
├── hcaptcha.py       # hCaptcha detection plugin
├── perimeterx.py     # PerimeterX detection plugin
├── datadome.py       # DataDome detection plugin
└── yourplugin.py     # Add your plugins here!
```

---

## Detection Categories

```python
from app.detections.base import DetectionCategory

DetectionCategory.CHALLENGE    # Cloudflare, PerimeterX, DataDome
DetectionCategory.CAPTCHA      # reCAPTCHA, hCaptcha, Turnstile
DetectionCategory.FINGERPRINT  # Canvas, WebGL fingerprinting
DetectionCategory.BEHAVIORAL   # Mouse/keyboard analysis
DetectionCategory.RATE_LIMIT   # Request frequency limits
```

---

## Solve Methods

```python
from app.detections.base import SolveMethod

SolveMethod.WAIT       # Just wait (JS challenges)
SolveMethod.API        # External API needed (2captcha)
SolveMethod.BEHAVIORAL # Simulate human behavior
SolveMethod.BYPASS     # Technical bypass/spoof
SolveMethod.NONE       # Cannot be solved
```

---

## Priority Guidelines

| Priority Range | Use For |
|---------------|---------|
| 10-20 | Critical challenges (Cloudflare, PerimeterX) |
| 20-40 | Standard challenges (DataDome, Akamai) |
| 30-50 | CAPTCHAs (reCAPTCHA, hCaptcha) |
| 50-70 | Fingerprint detection |
| 70-90 | Behavioral analysis |
| 90+ | Low priority / fallback |

---

## Helper Methods (Available in BaseDetection)

```python
# Check CSS selectors (returns matched selector or None)
matched = self._check_selectors(page)

# Check page title (returns matched indicator or None)
matched = self._check_title(page)

# Check page content (returns matched indicator or None)
matched = self._check_content(page, max_length=50000)

# Wait for element to disappear
passed = self._wait_for_element_gone(page, "#challenge", timeout=30)

# Logging helpers
self._log_detection(detected=True, reason="Found challenge element")
self._log_solve(success=True, reason="Challenge passed")
```

---

## Using the Detection System

### In scraper.py (High-Level)

```python
from app.detections.handler import DetectionHandler

class WebScraper:
    def __init__(self):
        self.detection_handler = DetectionHandler(self.config)

    def scrape(self, page, url):
        # After page load, handle any detections
        result = self.detection_handler.handle_detections(page, url)

        if result.blocked:
            logger.warning(f"Blocked by: {result.detections}")
            return None

        if result.detected_any:
            logger.info(f"Solved challenges: {result.solve_results}")

        # Continue with scraping...
```

### Low-Level Usage

```python
from app.detections import DetectionRegistry

registry = DetectionRegistry()

# Run all detections
results = registry.detect_all(page, url)

# Run specific category
captchas = registry.detect_by_category(page, url, DetectionCategory.CAPTCHA)

# Solve specific detection
solved = registry.solve("cloudflare", page, url)

# Get stats
print(registry.get_stats())
```

### Backward Compatibility

Old Cloudflare functions still work:

```python
from app.detections.handler import is_cloudflare_challenge, wait_for_cloudflare

if is_cloudflare_challenge(page):
    wait_for_cloudflare(page, max_wait=45)
```

---

## Configuration

Detections receive config from `config.json`:

```json
{
  "detections": {
    "recaptcha": {
      "enabled": true
    },
    "datadome": {
      "enabled": true,
      "custom_option": "value"
    }
  },
  "captcha": {
    "enabled": true,
    "service": "2captcha",
    "api_key": "your-api-key"
  }
}
```

Access in your detection:

```python
def _setup(self):
    my_option = self.config.get("custom_option", "default")
    captcha_config = self.config.get("captcha", {})
    self.api_key = captcha_config.get("api_key", "")
```

---

## Testing Your Detection

```python
# tests/test_detections.py

class TestMyDetection:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.locator.return_value.count.return_value = 0
        page.title.return_value = "Test Page"
        page.content.return_value = "<html><body>Normal</body></html>"
        return page

    def test_no_detection(self, mock_page):
        from app.detections.mydetection import MyDetection

        detection = MyDetection()
        result = detection.detect(mock_page, "https://example.com")

        assert result.detected is False

    def test_detection_by_selector(self, mock_page):
        from app.detections.mydetection import MyDetection

        # Mock selector match
        def locator_side_effect(selector):
            mock = MagicMock()
            if "#my-challenge" in selector:
                mock.count.return_value = 1
            else:
                mock.count.return_value = 0
            return mock

        mock_page.locator.side_effect = locator_side_effect

        detection = MyDetection()
        result = detection.detect(mock_page, "https://example.com")

        assert result.detected is True
```

Run tests:

```bash
pytest tests/test_detections.py::TestMyDetection -v
```

---

## Checklist for New Detections

- [ ] Created `app/detections/mydetection.py`
- [ ] Set unique `name` attribute
- [ ] Set appropriate `priority` (lower = runs first)
- [ ] Set correct `category`
- [ ] Implemented `detect()` method returning `DetectionResult`
- [ ] Implemented `solve()` method returning `bool`
- [ ] Added CSS selectors for detection
- [ ] Added title/content indicators (optional)
- [ ] Wrote tests in `tests/test_detections.py`
- [ ] All tests pass: `pytest tests/test_detections.py -v`

---

## Examples

### Simple Wait-Based Detection (like Cloudflare)

```python
def solve(self, page, url, detection_result):
    for _ in range(10):
        time.sleep(3)
        if not self.detect(page, url).detected:
            return True
    return False
```

### API-Based Detection (like reCAPTCHA)

```python
def solve(self, page, url, detection_result):
    sitekey = detection_result.details.get("sitekey")
    solution = self._call_2captcha_api(sitekey, url)
    return self._inject_solution(page, solution)
```

### Behavioral Detection (like PerimeterX)

```python
def solve(self, page, url, detection_result):
    button = page.locator("#press-hold").first
    box = button.bounding_box()

    # Move to button
    page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)

    # Press and hold
    page.mouse.down()
    time.sleep(5)
    page.mouse.up()

    return not self.detect(page, url).detected
```

---

## Support

For questions or issues, check:
1. Existing plugins in `app/detections/` for examples
2. Test file `tests/test_detections.py` for patterns
3. Base class `app/detections/base.py` for helper methods
