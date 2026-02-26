# AI Instructions: Adding New Bot Detections

## For AI Assistants (Claude, GPT, etc.)

When the user asks you to add a new bot detection system to WannaScrape, follow these instructions exactly.

---

## Quick Reference

**Location**: `app/detections/`
**Base class**: `app/detections/base.py`
**Tests**: `tests/test_detections.py`
**Time required**: ~5 minutes

---

## Step-by-Step Instructions

### Step 1: Create the Detection File

Create a new file at `app/detections/{detection_name}.py`

Example for Kasada:
```bash
touch app/detections/kasada.py
```

### Step 2: Use This Template

Copy and customize this template:

```python
"""
{DetectionName} Detection Plugin
================================
Brief description of what this bot detection system does.

Detection methods:
- List how it detects (selectors, cookies, headers, etc.)

Solving methods:
- How to bypass (wait, API, behavioral, etc.)
"""

import time
import logging
from typing import Optional

from playwright.sync_api import Page

from .base import (
    BaseDetection,
    DetectionResult,
    DetectionCategory,
    SolveMethod
)

logger = logging.getLogger("scraper.detections.{detection_name}")


class {DetectionName}Detection(BaseDetection):
    """
    {DetectionName} bot protection detection and bypass.

    Add more details about how this system works.
    """

    # =====================================================
    # REQUIRED: These must be set
    # =====================================================

    # Unique identifier (lowercase, no spaces)
    name = "{detection_name}"

    # Priority: lower number = runs first
    # Guidelines:
    #   10-20: Critical challenges (Cloudflare, PerimeterX)
    #   20-40: Standard challenges (DataDome, Akamai)
    #   30-50: CAPTCHAs (reCAPTCHA, hCaptcha)
    #   50-70: Fingerprint detection
    #   70-90: Behavioral analysis
    priority = 40

    # Category type
    # Options: CHALLENGE, CAPTCHA, FINGERPRINT, BEHAVIORAL, RATE_LIMIT
    category = DetectionCategory.CHALLENGE

    # =====================================================
    # OPTIONAL: Customize as needed
    # =====================================================

    description = "Human-readable description"
    requires_api = False  # True if needs 2captcha/capsolver
    solve_timeout = 30    # Max seconds to attempt solving
    enabled = True        # Can disable without removing

    # =====================================================
    # DETECTION PATTERNS: Add your patterns here
    # =====================================================

    # CSS selectors that indicate this detection
    selectors = [
        "#detection-element",
        ".challenge-container",
        "iframe[src*='detection-domain']",
    ]

    # Page title patterns (lowercase)
    title_indicators = [
        "blocked",
        "access denied",
        "verification required",
    ]

    # Page content patterns (for smaller pages)
    content_indicators = [
        "detection system name",
        "please verify",
        "checking your browser",
    ]

    # =====================================================
    # OPTIONAL: Custom setup (called after __init__)
    # =====================================================

    def _setup(self):
        """Custom initialization. Access self.config here."""
        # Example: Get API key from config
        # captcha_config = self.config.get("captcha", {})
        # self.api_key = captcha_config.get("api_key", "")
        pass

    # =====================================================
    # REQUIRED: Detection method
    # =====================================================

    def detect(self, page: Page, url: str) -> DetectionResult:
        """
        Check if this bot detection is present on the page.

        Args:
            page: Playwright Page object
            url: The URL being scraped

        Returns:
            DetectionResult with detected=True/False
        """
        # Method 1: Check CSS selectors (fastest)
        matched_selector = self._check_selectors(page)
        if matched_selector:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=1.0,
                details={"method": "selector", "selector": matched_selector},
                solve_method=SolveMethod.WAIT  # or API, BEHAVIORAL, BYPASS
            )

        # Method 2: Check page title
        matched_title = self._check_title(page)
        if matched_title:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=0.9,
                details={"method": "title", "indicator": matched_title},
                solve_method=SolveMethod.WAIT
            )

        # Method 3: Check page content (only for small pages)
        matched_content = self._check_content(page, max_length=50000)
        if matched_content:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=0.7,
                details={"method": "content", "indicator": matched_content},
                solve_method=SolveMethod.WAIT
            )

        # Not detected
        return DetectionResult(
            detected=False,
            detection_type=self.name
        )

    # =====================================================
    # REQUIRED: Solving method
    # =====================================================

    def solve(
        self,
        page: Page,
        url: str,
        detection_result: DetectionResult
    ) -> bool:
        """
        Attempt to solve/bypass this detection.

        Args:
            page: Playwright Page object
            url: The URL being scraped
            detection_result: Result from detect() with details

        Returns:
            True if solved successfully, False otherwise
        """
        logger.info(f"Attempting to solve {self.name}...")

        # ===== STRATEGY 1: Wait for auto-solve =====
        # Good for JS challenges that auto-complete
        for i in range(5):
            time.sleep(3)

            # Re-check if still detected
            new_result = self.detect(page, url)
            if not new_result.detected:
                self._log_solve(True, "Challenge auto-solved")
                return True

            # Check for redirect (challenge passed)
            if page.url != url:
                self._log_solve(True, "Redirected past challenge")
                return True

            logger.debug(f"Still waiting... attempt {i + 1}/5")

        # ===== STRATEGY 2: Try refresh =====
        # Sometimes clears JS challenges
        try:
            page.reload(wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)

            if not self.detect(page, url).detected:
                self._log_solve(True, "Solved after refresh")
                return True
        except Exception:
            pass

        # ===== STRATEGY 3: Behavioral (if needed) =====
        # Example: Click button, simulate mouse, etc.
        # selector = detection_result.details.get("selector")
        # if selector:
        #     try:
        #         page.locator(selector).click()
        #         time.sleep(2)
        #         if not self.detect(page, url).detected:
        #             return True
        #     except Exception:
        #         pass

        # ===== STRATEGY 4: API solving (if needed) =====
        # For CAPTCHAs that need external service
        # if self.requires_api and self.api_key:
        #     solution = self._call_solving_api(page, url)
        #     if solution:
        #         return self._inject_solution(page, solution)

        self._log_solve(False, "Could not solve")
        return False
```

### Step 3: Customize the Template

Replace these placeholders:
- `{DetectionName}` → `Kasada`, `Incapsula`, etc. (PascalCase)
- `{detection_name}` → `kasada`, `incapsula`, etc. (lowercase)

Fill in:
1. **Selectors**: CSS selectors that identify this detection
2. **Title indicators**: Page title patterns
3. **Content indicators**: Text patterns in page source
4. **Priority**: Lower = runs first
5. **Solve method**: Customize the solving strategy

### Step 4: Add Tests (Optional but Recommended)

Add tests to `tests/test_detections.py`:

```python
class Test{DetectionName}Detection:
    """Tests for {DetectionName} detection plugin."""

    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.locator.return_value.count.return_value = 0
        page.title.return_value = "Test Page"
        page.content.return_value = "<html><body>Normal</body></html>"
        return page

    def test_no_detection_on_normal_page(self, mock_page):
        from app.detections.{detection_name} import {DetectionName}Detection

        detection = {DetectionName}Detection()
        result = detection.detect(mock_page, "https://example.com")

        assert result.detected is False

    def test_detection_by_selector(self, mock_page):
        from app.detections.{detection_name} import {DetectionName}Detection

        def locator_side_effect(selector):
            mock = MagicMock()
            if "#detection-element" in selector:
                mock.count.return_value = 1
            else:
                mock.count.return_value = 0
            return mock

        mock_page.locator.side_effect = locator_side_effect

        detection = {DetectionName}Detection()
        result = detection.detect(mock_page, "https://example.com")

        assert result.detected is True
        assert result.detection_type == "{detection_name}"
```

### Step 5: Verify

```bash
# Run detection tests
pytest tests/test_detections.py -v

# Verify your detection is registered
python -c "from app.detections import DetectionRegistry; print(DetectionRegistry().list_all())"
```

---

## Available Helper Methods

These are available in your detection class (inherited from `BaseDetection`):

```python
# Check CSS selectors - returns matched selector or None
matched = self._check_selectors(page)

# Check page title - returns matched indicator or None
matched = self._check_title(page)

# Check page content - returns matched indicator or None
matched = self._check_content(page, max_length=50000)

# Wait for element to disappear
passed = self._wait_for_element_gone(page, "#challenge", timeout=30)

# Log detection result
self._log_detection(detected=True, reason="Found challenge element")

# Log solve result
self._log_solve(success=True, reason="Challenge passed")
```

---

## Solve Methods

Choose the appropriate `SolveMethod`:

| Method | Use When |
|--------|----------|
| `SolveMethod.WAIT` | JS challenges that auto-complete |
| `SolveMethod.API` | CAPTCHAs needing 2captcha/capsolver |
| `SolveMethod.BEHAVIORAL` | Requires mouse/keyboard simulation |
| `SolveMethod.BYPASS` | Technical bypass (cookie, header) |
| `SolveMethod.NONE` | Cannot be solved automatically |

---

## Priority Guidelines

| Priority | Detection Type | Examples |
|----------|---------------|----------|
| 10-20 | Critical challenges | Cloudflare, PerimeterX |
| 20-40 | Standard challenges | DataDome, Akamai, Incapsula |
| 30-50 | CAPTCHAs | reCAPTCHA, hCaptcha, Turnstile |
| 50-70 | Fingerprint checks | Canvas, WebGL |
| 70-90 | Behavioral analysis | Mouse tracking |

---

## Common Detection Patterns

### Akamai Bot Manager ✅ (Already implemented: `app/detections/akamai.py`)
```python
selectors = [
    "#ak-challenge",
    "#akamai-challenge-js",
    "script[src*='akamai']",
]
content_indicators = [
    "akamai",
    "ak_bmsc",
    "errors.edgesuite.net",
    "/_sec/",
]
```

### Incapsula/Imperva
```python
selectors = [
    "#incapsula-challenge",
    "iframe[src*='incapsula']",
]
content_indicators = [
    "incapsula",
    "imperva",
    "_incap_",
    "visid_incap",
]
```

### Kasada
```python
selectors = [
    "#kasada-challenge",
]
content_indicators = [
    "kasada",
    "x-kpsdk",
]
```

### Shape Security
```python
content_indicators = [
    "shape security",
    "shapesecurity",
]
```

---

## Example: Complete Kasada Detection

```python
"""
Kasada Detection Plugin
=======================
Detects Kasada bot protection.
"""

import time
import logging
from playwright.sync_api import Page

from .base import (
    BaseDetection,
    DetectionResult,
    DetectionCategory,
    SolveMethod
)

logger = logging.getLogger("scraper.detections.kasada")


class KasadaDetection(BaseDetection):
    name = "kasada"
    priority = 30
    category = DetectionCategory.CHALLENGE
    description = "Kasada Bot Protection"
    requires_api = False
    solve_timeout = 30

    selectors = [
        "#kasada-challenge",
    ]

    content_indicators = [
        "kasada",
        "x-kpsdk",
    ]

    def detect(self, page: Page, url: str) -> DetectionResult:
        matched = self._check_selectors(page)
        if matched:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=1.0,
                details={"selector": matched},
                solve_method=SolveMethod.WAIT
            )

        matched = self._check_content(page, max_length=30000)
        if matched:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=0.8,
                details={"content": matched},
                solve_method=SolveMethod.WAIT
            )

        return DetectionResult(detected=False, detection_type=self.name)

    def solve(self, page: Page, url: str, detection_result: DetectionResult) -> bool:
        logger.info("Kasada challenge detected, waiting...")

        for i in range(10):
            time.sleep(3)
            if not self.detect(page, url).detected:
                self._log_solve(True, f"Passed after {(i+1)*3}s")
                return True

        self._log_solve(False, "Timeout")
        return False
```

---

## Checklist

Before finishing, verify:

- [ ] File created at `app/detections/{name}.py`
- [ ] Class name is `{Name}Detection` (PascalCase)
- [ ] `name` attribute is lowercase
- [ ] `priority` is set appropriately
- [ ] `category` is correct
- [ ] `selectors` list has CSS selectors
- [ ] `detect()` method returns `DetectionResult`
- [ ] `solve()` method returns `bool`
- [ ] Tests pass: `pytest tests/test_detections.py -v`
- [ ] Detection appears in registry: `DetectionRegistry().list_all()`

---

## Troubleshooting

### Detection not appearing in registry
- Check file is in `app/detections/` directory
- Check class inherits from `BaseDetection`
- Check `name` attribute is unique
- Check `enabled = True`
- For CAPTCHA types, ensure API key is configured

### Tests failing
- Reset registry between tests: `DetectionRegistry.reset()`
- Mock the page object properly
- Check selector matching logic

### Detection not working
- Add debug logging: `logger.debug(f"Checking {selector}")`
- Verify selectors on real pages
- Check if page content is too large for content check
