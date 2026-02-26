# WannaScrape - AI Development Instructions

> **For AI assistants (GitHub Copilot, Claude, etc.):** Read this file to understand how to add features to this project.

---

## 🏗️ Project Architecture

```
app/
├── api/              # REST API endpoints (FastAPI)
├── cli/              # CLI commands (Typer) — --save, --save-dir flags
├── config/           # Configuration constants
├── core/             # Core business logic
│   ├── scraper.py    # Main WebScraper class (orchestrates everything)
│   ├── browser_manager.py     # Browser setup, fingerprint integration, tracker blocking
│   ├── content_extractor.py   # Trafilatura + fallback extraction
│   ├── fingerprint_manager.py # 🆕 10 fingerprint profiles, rotation, JS overrides
│   ├── cookie_dismisser.py    # 🆕 Cookie banner auto-dismissal (30+ selectors)
│   ├── captcha_solver.py
│   ├── rate_limiter.py
│   ├── session_manager.py
│   └── exceptions.py
├── detections/       # 🔌 BOT DETECTION PLUGIN SYSTEM
│   ├── base.py       # BaseDetection abstract class
│   ├── registry.py   # Auto-discovery engine
│   ├── handler.py    # Interface for scraper.py
│   └── *.py          # Individual detection plugins
├── logging/          # Logging system
├── monitoring/       # Prometheus metrics
├── services/         # External services (anti-detection scripts, user agents)
└── utils/            # Pure utility functions, human behavior (fast/normal/stealth)
```

---

## 🔌 Adding New Bot Detection (MOST COMMON TASK)

### Location: `app/detections/`
### Effort: Create 1 file only
### No changes needed to: scraper.py, handler.py, or any other file

### Template:

```python
# app/detections/yourdetection.py
"""
YourDetection Plugin
====================
Detects and handles YourDetection bot management.
"""

import logging
from playwright.sync_api import Page

from .base import (
    BaseDetection,
    DetectionResult,
    DetectionCategory,
    SolveMethod
)

logger = logging.getLogger("scraper.detections.yourdetection")


class YourDetection(BaseDetection):
    """YourDetection bot management."""

    # === REQUIRED ===
    name = "yourdetection"           # Unique identifier
    priority = 50                     # Lower = runs first (10-90)
    category = DetectionCategory.CHALLENGE  # or CAPTCHA, FINGERPRINT, BEHAVIORAL

    # === OPTIONAL ===
    description = "YourDetection Bot Manager"
    requires_api = False              # True if needs 2captcha/capsolver
    solve_timeout = 60

    # === DETECTION PATTERNS ===
    selectors = [
        "#your-detection-element",
        "iframe[src*='yourdetection']",
    ]
    
    title_indicators = [
        "checking your browser",
    ]
    
    content_indicators = [
        "please wait while we verify",
    ]

    def detect(self, page: Page, url: str) -> DetectionResult:
        """Check if detection is present."""
        matched = self._check_selectors(page)
        if matched:
            return DetectionResult(
                detected=True,
                detection_type=self.name,
                confidence=1.0,
                details={"selector": matched},
                solve_method=SolveMethod.WAIT
            )
        return DetectionResult(detected=False, detection_type=self.name)

    def solve(self, page: Page, url: str, detection_result: DetectionResult) -> bool:
        """Attempt to solve/bypass."""
        logger.info(f"Solving {self.name}")
        
        # Wait for auto-solve
        for _ in range(3):
            page.wait_for_timeout(5000)
            if not self._check_selectors(page):
                return True
        
        return False
```

### Available Helper Methods (inherited from BaseDetection):
- `self._check_selectors(page)` - Returns matched selector or None
- `self._check_title(page)` - Returns matched title indicator or None
- `self._check_content(page)` - Returns matched content indicator or None
- `self._wait_for_element_gone(page, selector, timeout)` - Wait for element to disappear
- `self._log_detection(detected, reason)` - Log detection result
- `self._log_solve(success, reason)` - Log solve result

### Detection Categories:
- `DetectionCategory.CHALLENGE` - Cloudflare, Akamai, PerimeterX
- `DetectionCategory.CAPTCHA` - reCAPTCHA, hCaptcha
- `DetectionCategory.FINGERPRINT` - Canvas, WebGL fingerprinting
- `DetectionCategory.BEHAVIORAL` - Mouse/keyboard analysis
- `DetectionCategory.RATE_LIMIT` - Request frequency limits

### Solve Methods:
- `SolveMethod.WAIT` - Just wait for auto-solve
- `SolveMethod.API` - Requires external API (2captcha)
- `SolveMethod.BEHAVIORAL` - Simulate human behavior
- `SolveMethod.BYPASS` - Technical bypass/spoof
- `SolveMethod.NONE` - Cannot be solved

---

## 📡 Adding New API Endpoint

### Location: `app/api/`
### Pattern: FastAPI router

```python
# app/api/your_endpoint.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.scraper_api import get_api_key  # For auth

router = APIRouter()


class YourRequest(BaseModel):
    field: str


class YourResponse(BaseModel):
    result: str


@router.post("/your-endpoint", response_model=YourResponse)
async def your_endpoint(
    request: YourRequest,
    api_key: str = Depends(get_api_key)  # Requires auth
):
    """Your endpoint description."""
    # Your logic here
    return YourResponse(result="success")
```

### Register in `app/api/__init__.py`:
```python
from app.api.your_endpoint import router as your_router
# Add to routers list
```

---

## 💻 Adding New CLI Command

### Location: `app/cli/commands.py`
### Pattern: Typer command

```python
@app.command()
def your_command(
    arg: str = typer.Argument(..., help="Description"),
    option: bool = typer.Option(False, "--option", "-o", help="Description")
):
    """Command description shown in --help."""
    # Your logic here
    console.print("[green]Success![/green]")
```

---

## 🛡️ Adding Anti-Detection Script

### Location: `app/services/anti_detection/scripts.py`
### Pattern: JavaScript injection script

```python
YOUR_SCRIPT = """
(() => {
    // Your anti-detection JavaScript
    Object.defineProperty(navigator, 'yourProperty', {
        get: () => 'spoofed_value'
    });
})();
"""
```

### Inject in `app/core/browser_manager.py`:
```python
target.add_init_script(YOUR_SCRIPT)
```

---

## 🧪 Adding Tests

### Location: `tests/`
### Pattern: pytest with fixtures

```python
# tests/test_your_feature.py
import pytest
from unittest.mock import Mock, patch


class TestYourFeature:
    def test_basic_case(self):
        """Test description."""
        result = your_function()
        assert result == expected

    def test_with_mock(self):
        """Test with mocked dependencies."""
        with patch('app.module.dependency') as mock:
            mock.return_value = "mocked"
            result = your_function()
            assert result == "mocked"
```

### Run tests:
```bash
pytest tests/test_your_feature.py -v
```

---

## 📊 Adding Prometheus Metrics

### Location: `app/monitoring/metrics.py`
### Pattern: prometheus_client

```python
from prometheus_client import Counter, Histogram

YOUR_COUNTER = Counter(
    'scraper_your_metric_total',
    'Description',
    ['label1', 'label2']
)

YOUR_HISTOGRAM = Histogram(
    'scraper_your_duration_seconds',
    'Description',
    ['label']
)

def record_your_metric(label1: str, label2: str):
    YOUR_COUNTER.labels(label1=label1, label2=label2).inc()
```

---

## 📝 Adding Configuration Option

### Location: `config/config.json`

```json
{
  "your_feature": {
    "enabled": true,
    "option1": "value",
    "option2": 123
  }
}
```

### Access in code:
```python
config = load_config("config/config.json")
your_config = config.get("your_feature", {})
enabled = your_config.get("enabled", False)
```

---

## 🔧 Key Files Reference

| File | Purpose | When to Modify |
|------|---------|----------------|
| `app/core/scraper.py` | Main orchestrator | Rarely - only for core flow changes |
| `app/core/browser_manager.py` | Browser setup, fingerprints, tracker blocking | Adding anti-detection scripts |
| `app/core/fingerprint_manager.py` | Fingerprint rotation (10 profiles) | Adding new fingerprint profiles |
| `app/core/cookie_dismisser.py` | Cookie banner auto-dismissal | Adding new consent framework selectors |
| `app/core/content_extractor.py` | Article extraction (Trafilatura + fallback) | Adding new CSS selectors for content |
| `app/detections/*.py` | Bot detection | Adding new detection (create new file) |
| `app/api/scraper_api.py` | /scrape endpoint | Changing scrape API behavior |
| `app/cli/commands.py` | CLI commands (--save, --save-dir) | Adding new commands |
| `app/config/constants.py` | Constants | Adding popup selectors, etc. |
| `app/utils/human_behavior.py` | Human simulation (fast/normal/stealth) | Changing behavior modes |
| `config/config.json` | Runtime configuration | Adding new config options |
| `requirements.txt` | Dependencies | Adding new packages |

---

## ✅ Before Committing

1. **Run tests**: `pytest tests/ -v`
2. **Check imports**: `python -c "from app.core.scraper import WebScraper"`
3. **Run linter**: `ruff check app/`
4. **Format code**: `ruff format app/`

---

## 📋 Common Patterns

### Error Handling
```python
from app.core.exceptions import ScraperError, AccessDeniedError

try:
    result = do_something()
except AccessDeniedError as e:
    logger.warning(f"Access denied: {e}")
    raise
except Exception as e:
    raise ScraperError(f"Failed: {e}") from e
```

### Logging
```python
import logging
logger = logging.getLogger("scraper.your_module")

logger.debug("Detailed info")
logger.info("General info")
logger.warning("Something unexpected")
logger.error("Something failed")
```

### Type Hints
```python
from typing import Optional, Dict, Any, List

def your_function(
    required: str,
    optional: Optional[int] = None
) -> Dict[str, Any]:
    ...
```

---

## 🚀 Quick Examples

### "Add Kasada detection"
→ Create `app/detections/kasada.py` using template above (Akamai already exists)

### "Add /analyze endpoint"
→ Create `app/api/analyze_api.py` with FastAPI router

### "Add --verbose flag to CLI"
→ Modify `app/cli/commands.py`

### "Block WebRTC"
→ Add script to `app/services/anti_detection/scripts.py`

### "Add proxy authentication support"
→ Modify `app/utils/proxy_manager.py`
