"""
Browser Fingerprint Manager for Anti-Detection.

Rotates complete, consistent browser fingerprints per scrape session.
Each fingerprint matches: user_agent <-> viewport <-> platform <-> WebGL <-> hardware.
This prevents sites from correlating requests by fingerprint.
"""

import random
import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger("scraper.fingerprint")


@dataclass
class BrowserFingerprint:
    """A complete, consistent browser fingerprint."""
    user_agent: str
    viewport: dict
    platform: str
    language: str
    languages: list
    timezone: str
    webgl_vendor: str
    webgl_renderer: str
    hardware_concurrency: int
    device_memory: int
    max_touch_points: int
    color_depth: int = 24
    pixel_ratio: float = 1.0


# Real-world browser fingerprints — each one is internally consistent
FINGERPRINT_DATABASE: List[dict] = [
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "platform": "Win32",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "timezone": "America/New_York",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "hardware_concurrency": 12,
        "device_memory": 16,
        "max_touch_points": 0,
        "pixel_ratio": 1.0,
    },
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "viewport": {"width": 1366, "height": 768},
        "platform": "Win32",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "timezone": "America/Chicago",
        "webgl_vendor": "Google Inc. (Intel)",
        "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "max_touch_points": 0,
        "pixel_ratio": 1.0,
    },
    {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1440, "height": 900},
        "platform": "MacIntel",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "timezone": "America/Los_Angeles",
        "webgl_vendor": "Google Inc. (Apple)",
        "webgl_renderer": "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)",
        "hardware_concurrency": 10,
        "device_memory": 16,
        "max_touch_points": 0,
        "pixel_ratio": 2.0,
    },
    {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 2560, "height": 1440},
        "platform": "MacIntel",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "timezone": "America/New_York",
        "webgl_vendor": "Google Inc. (Apple)",
        "webgl_renderer": "ANGLE (Apple, Apple M2 Max, OpenGL 4.1)",
        "hardware_concurrency": 12,
        "device_memory": 32,
        "max_touch_points": 0,
        "pixel_ratio": 2.0,
    },
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "platform": "Win32",
        "language": "en-GB",
        "languages": ["en-GB", "en"],
        "timezone": "Europe/London",
        "webgl_vendor": "Google Inc. (AMD)",
        "webgl_renderer": "ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "hardware_concurrency": 8,
        "device_memory": 16,
        "max_touch_points": 0,
        "pixel_ratio": 1.0,
    },
    {
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "platform": "Linux x86_64",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "timezone": "America/Denver",
        "webgl_vendor": "Google Inc. (AMD)",
        "webgl_renderer": "ANGLE (AMD, AMD Radeon RX 6700 XT, OpenGL 4.6)",
        "hardware_concurrency": 12,
        "device_memory": 16,
        "max_touch_points": 0,
        "pixel_ratio": 1.0,
    },
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "viewport": {"width": 1536, "height": 864},
        "platform": "Win32",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "timezone": "America/Los_Angeles",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "max_touch_points": 0,
        "pixel_ratio": 1.25,
    },
    {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1680, "height": 1050},
        "platform": "MacIntel",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "timezone": "America/Chicago",
        "webgl_vendor": "Google Inc. (Apple)",
        "webgl_renderer": "ANGLE (Apple, Apple M1, OpenGL 4.1)",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "max_touch_points": 0,
        "pixel_ratio": 2.0,
    },
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "viewport": {"width": 2560, "height": 1440},
        "platform": "Win32",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "timezone": "America/New_York",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "hardware_concurrency": 16,
        "device_memory": 32,
        "max_touch_points": 0,
        "pixel_ratio": 1.0,
    },
    {
        "user_agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "platform": "Linux x86_64",
        "language": "en-US",
        "languages": ["en-US", "en"],
        "timezone": "America/New_York",
        "webgl_vendor": "Google Inc. (Intel)",
        "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics 770, OpenGL 4.6)",
        "hardware_concurrency": 16,
        "device_memory": 16,
        "max_touch_points": 0,
        "pixel_ratio": 1.0,
    },
]


class FingerprintManager:
    """
    Manages browser fingerprint rotation for anti-detection.

    Each scrape session gets a different, internally-consistent fingerprint
    so sites can't correlate requests by fingerprint signature.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._recent_indices: List[int] = []

    def get_fingerprint(self) -> BrowserFingerprint:
        """Get a random fingerprint, avoiding recently used ones."""
        if not self.enabled:
            return BrowserFingerprint(**FINGERPRINT_DATABASE[0])

        available = [
            i for i in range(len(FINGERPRINT_DATABASE))
            if i not in self._recent_indices[-3:]
        ]
        if not available:
            available = list(range(len(FINGERPRINT_DATABASE)))
            self._recent_indices.clear()

        idx = random.choice(available)
        self._recent_indices.append(idx)

        fp = BrowserFingerprint(**FINGERPRINT_DATABASE[idx])
        logger.info(
            f"🎭 Fingerprint: {fp.platform} | "
            f"{fp.viewport['width']}x{fp.viewport['height']} | "
            f"{fp.language} | {fp.timezone}"
        )
        return fp

    def get_context_options(self, fp: BrowserFingerprint) -> dict:
        """Get Playwright browser context options for this fingerprint."""
        return {
            "user_agent": fp.user_agent,
            "viewport": fp.viewport,
            "locale": fp.language,
            "timezone_id": fp.timezone,
            "device_scale_factor": fp.pixel_ratio,
            "color_scheme": "light",
        }

    def get_override_script(self, fp: BrowserFingerprint) -> str:
        """Generate JavaScript to override browser fingerprint properties."""
        return f"""
(function() {{
    Object.defineProperty(navigator, 'platform', {{get: () => '{fp.platform}'}});
    Object.defineProperty(navigator, 'language', {{get: () => '{fp.language}'}});
    Object.defineProperty(navigator, 'languages', {{get: () => {fp.languages}}});
    Object.defineProperty(navigator, 'hardwareConcurrency', {{get: () => {fp.hardware_concurrency}}});
    Object.defineProperty(navigator, 'deviceMemory', {{get: () => {fp.device_memory}}});
    Object.defineProperty(navigator, 'maxTouchPoints', {{get: () => {fp.max_touch_points}}});

    ['WebGLRenderingContext', 'WebGL2RenderingContext'].forEach(function(ctxName) {{
        if (window[ctxName] && window[ctxName].prototype.getParameter) {{
            const original = window[ctxName].prototype.getParameter;
            window[ctxName].prototype.getParameter = function(param) {{
                if (param === 37445) return '{fp.webgl_vendor}';
                if (param === 37446) return '{fp.webgl_renderer}';
                return original.call(this, param);
            }};
        }}
    }});

    Object.defineProperty(screen, 'width', {{get: () => {fp.viewport['width']}}});
    Object.defineProperty(screen, 'height', {{get: () => {fp.viewport['height']}}});
    Object.defineProperty(screen, 'availWidth', {{get: () => {fp.viewport['width']}}});
    Object.defineProperty(screen, 'availHeight', {{get: () => {fp.viewport['height'] - 40}}});
    Object.defineProperty(screen, 'colorDepth', {{get: () => {fp.color_depth}}});
    Object.defineProperty(screen, 'pixelDepth', {{get: () => {fp.color_depth}}});
    Object.defineProperty(window, 'devicePixelRatio', {{get: () => {fp.pixel_ratio}}});
}})();
"""
