# Anti-Ban Enhancement Plan for Web Scraper

## Current State Summary
Your scraper already has:
- Playwright stealth mode
- User-agent rotation
- Proxy support
- Basic timing delays
- Popup/Cloudflare handling

## What's Missing (Priority Order)

---

## Phase 1: Human Behavior Simulation (HIGH IMPACT)

### 1.1 Random Mouse Movement
```python
def _simulate_human_mouse(page):
    """Simulate natural mouse movements across the page."""
    import random

    viewport = page.viewport_size
    width, height = viewport['width'], viewport['height']

    # Generate 3-7 random points to move through
    num_points = random.randint(3, 7)

    for _ in range(num_points):
        x = random.randint(100, width - 100)
        y = random.randint(100, height - 100)

        # Move with random steps (simulates acceleration/deceleration)
        steps = random.randint(10, 30)
        page.mouse.move(x, y, steps=steps)

        # Random micro-pause
        time.sleep(random.uniform(0.1, 0.5))
```

### 1.2 Random Scrolling
```python
def _simulate_human_scroll(page):
    """Simulate natural scrolling behavior."""
    import random

    # Get page height
    page_height = page.evaluate("document.body.scrollHeight")
    viewport_height = page.viewport_size['height']

    # Scroll down in chunks (like reading)
    current_position = 0
    while current_position < page_height * 0.7:  # Don't always scroll to bottom
        # Random scroll amount (100-500 pixels)
        scroll_amount = random.randint(100, 500)
        current_position += scroll_amount

        page.evaluate(f"window.scrollTo(0, {current_position})")

        # Reading pause (longer pauses = more human-like)
        time.sleep(random.uniform(0.5, 2.0))

    # Sometimes scroll back up a bit
    if random.random() > 0.7:
        scroll_back = random.randint(200, 500)
        page.evaluate(f"window.scrollBy(0, -{scroll_back})")
        time.sleep(random.uniform(0.3, 1.0))
```

### 1.3 Random "Thinking Time"
```python
def _human_delay():
    """Generate human-like delay using normal distribution."""
    import numpy as np

    # Normal distribution centered at 3 seconds, std dev 1.5
    delay = np.random.normal(3, 1.5)
    # Clamp between 1 and 8 seconds
    return max(1, min(8, delay))
```

---

## Phase 2: Browser Fingerprint Randomization (CRITICAL)

### 2.1 Viewport Randomization
```python
COMMON_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
    {"width": 2560, "height": 1440},
]

def _get_random_viewport():
    return random.choice(COMMON_VIEWPORTS)
```

### 2.2 Timezone/Locale Matching
```python
LOCATION_PROFILES = [
    {"timezone_id": "America/New_York", "locale": "en-US"},
    {"timezone_id": "America/Los_Angeles", "locale": "en-US"},
    {"timezone_id": "America/Chicago", "locale": "en-US"},
    {"timezone_id": "Europe/London", "locale": "en-GB"},
    {"timezone_id": "Europe/Paris", "locale": "fr-FR"},
]

def _get_random_location():
    return random.choice(LOCATION_PROFILES)
```

### 2.3 Canvas Fingerprint Noise (JavaScript Injection)
```python
CANVAS_NOISE_SCRIPT = """
(function() {
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (type === 'image/png') {
            const context = this.getContext('2d');
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                // Add tiny random noise to RGB values
                imageData.data[i] += Math.floor(Math.random() * 2) - 1;
                imageData.data[i + 1] += Math.floor(Math.random() * 2) - 1;
                imageData.data[i + 2] += Math.floor(Math.random() * 2) - 1;
            }
            context.putImageData(imageData, 0, 0);
        }
        return originalToDataURL.apply(this, arguments);
    };
})();
"""
```

### 2.4 WebGL Fingerprint Spoofing
```python
WEBGL_SPOOF_SCRIPT = """
(function() {
    const getParameterProxyHandler = {
        apply: function(target, thisArg, args) {
            const param = args[0];
            const gl = thisArg;
            // Randomize unmasked vendor/renderer
            if (param === 37445) { // UNMASKED_VENDOR_WEBGL
                return 'Google Inc. (NVIDIA)';
            }
            if (param === 37446) { // UNMASKED_RENDERER_WEBGL
                const renderers = [
                    'ANGLE (NVIDIA GeForce GTX 1080 Direct3D11)',
                    'ANGLE (NVIDIA GeForce RTX 3070 Direct3D11)',
                    'ANGLE (Intel UHD Graphics 630 Direct3D11)',
                    'ANGLE (AMD Radeon RX 580 Direct3D11)',
                ];
                return renderers[Math.floor(Math.random() * renderers.length)];
            }
            return target.apply(thisArg, args);
        }
    };

    // Proxy both WebGL contexts
    ['WebGLRenderingContext', 'WebGL2RenderingContext'].forEach(ctx => {
        if (window[ctx]) {
            const original = window[ctx].prototype.getParameter;
            window[ctx].prototype.getParameter = new Proxy(original, getParameterProxyHandler);
        }
    });
})();
"""
```

---

## Phase 3: Request Pattern Improvements (HIGH IMPACT)

### 3.1 Rate Limiting Configuration
Add to `config.json`:
```json
{
    "rate_limiting": {
        "min_delay_between_requests": 5,
        "max_delay_between_requests": 15,
        "requests_per_domain_per_hour": 20,
        "cooling_period_after_error": 60
    }
}
```

### 3.2 HTTP Headers Randomization
```python
def _get_random_headers():
    accept_languages = [
        "en-US,en;q=0.9",
        "en-US,en;q=0.9,es;q=0.8",
        "en-GB,en;q=0.9,en-US;q=0.8",
    ]

    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": random.choice(accept_languages),
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
```

### 3.3 Referrer Spoofing
```python
def _get_realistic_referrer(target_url):
    """Generate a realistic referrer based on target."""
    from urllib.parse import urlparse

    domain = urlparse(target_url).netloc

    referrers = [
        f"https://www.google.com/search?q={domain}",
        f"https://www.google.com/",
        f"https://news.google.com/",
        f"https://t.co/redirect",  # Twitter
        None,  # Sometimes no referrer is fine
    ]

    return random.choice(referrers)
```

---

## Phase 4: Proxy Management Improvements

### 4.1 Proxy Health Tracking
```python
class ProxyManager:
    def __init__(self, proxies):
        self.proxies = proxies
        self.failed_proxies = {}  # {proxy_server: failure_count}
        self.last_used = {}  # {proxy_server: timestamp}

    def get_proxy(self):
        """Get a healthy proxy that hasn't been used recently."""
        available = [
            p for p in self.proxies
            if self.failed_proxies.get(p['server'], 0) < 3
            and time.time() - self.last_used.get(p['server'], 0) > 60
        ]

        if not available:
            # Reset failed proxies if all are marked
            self.failed_proxies = {}
            available = self.proxies

        proxy = random.choice(available)
        self.last_used[proxy['server']] = time.time()
        return proxy

    def mark_failed(self, proxy_server):
        self.failed_proxies[proxy_server] = self.failed_proxies.get(proxy_server, 0) + 1

    def mark_success(self, proxy_server):
        self.failed_proxies[proxy_server] = 0
```

---

## Phase 5: Enhanced Cloudflare Handling

### 5.1 Better Challenge Detection
```python
def _is_cloudflare_challenge(page):
    """Comprehensive Cloudflare detection."""
    indicators = [
        # Text-based
        "just a moment",
        "checking your browser",
        "ray id",
        "cloudflare",
        "ddos protection",

        # Element-based
        "#challenge-running",
        "#challenge-stage",
        ".cf-browser-verification",
    ]

    page_text = page.text_content("body").lower()

    # Check text indicators
    for indicator in indicators[:5]:
        if indicator in page_text:
            return True

    # Check element indicators
    for selector in indicators[5:]:
        if page.locator(selector).count() > 0:
            return True

    return False

def _wait_for_cloudflare(page, max_wait=60):
    """Wait for Cloudflare challenge with longer timeout."""
    start = time.time()

    while time.time() - start < max_wait:
        if not _is_cloudflare_challenge(page):
            return True

        logger.info("Waiting for Cloudflare challenge...")
        time.sleep(3)

    return False
```

---

## Implementation Priority

| Phase | Feature | Impact | Effort | Priority |
|-------|---------|--------|--------|----------|
| 1.1 | Mouse Movement | HIGH | LOW | 1 |
| 1.2 | Random Scrolling | HIGH | LOW | 2 |
| 2.1 | Viewport Randomization | HIGH | LOW | 3 |
| 3.1 | Rate Limiting | HIGH | MEDIUM | 4 |
| 2.3 | Canvas Noise | CRITICAL | MEDIUM | 5 |
| 2.4 | WebGL Spoofing | CRITICAL | MEDIUM | 6 |
| 3.2 | Header Randomization | MEDIUM | LOW | 7 |
| 4.1 | Proxy Health | MEDIUM | MEDIUM | 8 |
| 5.1 | Cloudflare Enhanced | MEDIUM | LOW | 9 |

---

## Quick Wins (Implement Today)

1. **Add mouse movement before extraction**
2. **Add random scrolling after page load**
3. **Randomize viewport per request**
4. **Add longer random delays (use normal distribution)**
5. **Add referrer header**

---

## Config File Enhancement

```json
{
    "anti_detection": {
        "simulate_mouse": true,
        "simulate_scroll": true,
        "randomize_viewport": true,
        "randomize_timezone": true,
        "inject_canvas_noise": true,
        "inject_webgl_spoof": true
    },
    "delays": {
        "min_page_delay": 3,
        "max_page_delay": 10,
        "min_between_requests": 5,
        "max_between_requests": 20,
        "use_normal_distribution": true
    },
    "rate_limiting": {
        "max_requests_per_hour": 30,
        "cooling_period_on_error": 120
    }
}
```

---

## Testing Your Changes

After implementing, test with:
1. https://bot.sannysoft.com/ - Checks automation detection
2. https://browserleaks.com/canvas - Canvas fingerprint
3. https://browserleaks.com/webgl - WebGL fingerprint
4. https://www.browserscan.net/ - Comprehensive bot check
5. https://pixelscan.net/ - Fingerprint analysis

---

## Summary

The most impactful changes are:
1. **Human behavior simulation** (mouse + scroll) - Makes 80% difference
2. **Fingerprint randomization** (viewport, canvas, WebGL) - Defeats JS detection
3. **Request timing variance** (normal distribution delays) - Defeats pattern analysis
4. **Proxy health management** - Avoids using blocked IPs

Implement Phase 1 first - it's quick and has the highest impact on avoiding bans.
