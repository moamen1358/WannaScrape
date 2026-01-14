import trafilatura
import warnings
# Suppress the duckduckgo_search rename warning
warnings.filterwarnings("ignore", category=RuntimeWarning)
from duckduckgo_search import DDGS
import json
import time
import random
import logging
import math
from pathlib import Path
from typing import Optional, Dict, List
from urllib.parse import urlparse
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from tenacity import retry, stop_after_attempt, wait_exponential
from fake_useragent import UserAgent

# Import our enhanced UserAgentManager with 50+ user agents
from app.services.user_agents import UserAgentManager, LOCATION_PROFILES as EXTENDED_LOCATION_PROFILES

# Import advanced logging system
from app.services.advanced_logging import get_advanced_logger, AdvancedScrapeLogger

# Import advanced anti-detection suite
from app.services.advanced_anti_detection import (
    inject_advanced_anti_detection,
    DomainRateLimiter,
    SessionManager,
    type_like_human,
    move_mouse_naturally
)

# Configure logger with detailed format for debugging
logger = logging.getLogger("scraper")
if not logger.handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

# ============================================================================
# ANTI-DETECTION CONFIGURATIONS
# ============================================================================

# Common viewport sizes to randomize (realistic distribution)
COMMON_VIEWPORTS = [
    {"width": 1920, "height": 1080},  # Most common
    {"width": 1366, "height": 768},   # Laptops
    {"width": 1536, "height": 864},   # Scaled displays
    {"width": 1440, "height": 900},   # MacBooks
    {"width": 1280, "height": 720},   # HD
    {"width": 2560, "height": 1440},  # QHD monitors
    {"width": 1680, "height": 1050},  # Older monitors
]

# Location profiles - now using extended 30+ locations from user_agents module
# Keeping local reference for backward compatibility
LOCATION_PROFILES = EXTENDED_LOCATION_PROFILES

# Canvas fingerprint noise injection script
CANVAS_NOISE_SCRIPT = """
(function() {
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;

    // Add noise to toDataURL
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (type === 'image/png' && this.width > 0 && this.height > 0) {
            try {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = originalGetImageData.call(context, 0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        // Add tiny random noise (imperceptible but changes fingerprint)
                        imageData.data[i] = Math.max(0, Math.min(255, imageData.data[i] + (Math.random() * 2 - 1)));
                        imageData.data[i + 1] = Math.max(0, Math.min(255, imageData.data[i + 1] + (Math.random() * 2 - 1)));
                        imageData.data[i + 2] = Math.max(0, Math.min(255, imageData.data[i + 2] + (Math.random() * 2 - 1)));
                    }
                    context.putImageData(imageData, 0, 0);
                }
            } catch(e) {}
        }
        return originalToDataURL.apply(this, arguments);
    };
})();
"""

# WebGL fingerprint spoofing script
WEBGL_SPOOF_SCRIPT = """
(function() {
    const renderers = [
        'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)',
    ];
    const vendors = ['Google Inc. (NVIDIA)', 'Google Inc. (Intel)', 'Google Inc. (AMD)'];

    const selectedRenderer = renderers[Math.floor(Math.random() * renderers.length)];
    const selectedVendor = vendors[Math.floor(Math.random() * vendors.length)];

    const getParameterProxy = function(target, thisArg, args) {
        const param = args[0];
        // UNMASKED_VENDOR_WEBGL
        if (param === 37445) return selectedVendor;
        // UNMASKED_RENDERER_WEBGL
        if (param === 37446) return selectedRenderer;
        return target.apply(thisArg, args);
    };

    ['WebGLRenderingContext', 'WebGL2RenderingContext'].forEach(function(ctx) {
        if (window[ctx] && window[ctx].prototype.getParameter) {
            const original = window[ctx].prototype.getParameter;
            window[ctx].prototype.getParameter = function(param) {
                if (param === 37445) return selectedVendor;
                if (param === 37446) return selectedRenderer;
                return original.call(this, param);
            };
        }
    });
})();
"""

# Additional browser property patches
BROWSER_PATCHES_SCRIPT = """
(function() {
    // Randomize screen properties slightly
    const screenProps = {
        availWidth: window.screen.width,
        availHeight: window.screen.height - Math.floor(Math.random() * 40 + 30),
        colorDepth: 24,
        pixelDepth: 24
    };

    // Override navigator.hardwareConcurrency with realistic values
    const cores = [4, 6, 8, 12, 16][Math.floor(Math.random() * 5)];
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => cores });

    // Override navigator.deviceMemory with realistic values
    const memory = [4, 8, 16, 32][Math.floor(Math.random() * 4)];
    Object.defineProperty(navigator, 'deviceMemory', { get: () => memory });

    // Add realistic plugins (Chrome typically has these)
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            return {
                length: 5,
                item: (i) => null,
                namedItem: (name) => null,
                refresh: () => {}
            };
        }
    });

    // Disable WebRTC IP leak (important for proxy users)
    if (typeof RTCPeerConnection !== 'undefined') {
        const originalRTCPeerConnection = window.RTCPeerConnection;
        window.RTCPeerConnection = function(...args) {
            const config = args[0] || {};
            // Force TURN only mode to prevent IP leak
            config.iceServers = [];
            return new originalRTCPeerConnection(config);
        };
        window.RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;
    }

    // Spoof connection type (Network Information API)
    if (navigator.connection) {
        const connectionTypes = ['wifi', '4g', 'ethernet'];
        const effectiveTypes = ['4g', '3g'];
        Object.defineProperty(navigator.connection, 'type', {
            get: () => connectionTypes[Math.floor(Math.random() * connectionTypes.length)]
        });
        Object.defineProperty(navigator.connection, 'effectiveType', {
            get: () => effectiveTypes[Math.floor(Math.random() * effectiveTypes.length)]
        });
        Object.defineProperty(navigator.connection, 'downlink', {
            get: () => Math.floor(Math.random() * 10) + 1  // 1-10 Mbps
        });
        Object.defineProperty(navigator.connection, 'rtt', {
            get: () => Math.floor(Math.random() * 100) + 50  // 50-150ms
        });
    }

    // Spoof battery API (if available)
    if (navigator.getBattery) {
        navigator.getBattery = () => Promise.resolve({
            charging: Math.random() > 0.3,
            chargingTime: Math.floor(Math.random() * 3600),
            dischargingTime: Math.floor(Math.random() * 10800) + 3600,
            level: Math.random() * 0.5 + 0.5  // 50-100%
        });
    }
})();
"""

# ============================================================================
# HUMAN BEHAVIOR SIMULATION FUNCTIONS
# ============================================================================

def _human_delay(min_sec: float = 2.0, max_sec: float = 6.0) -> float:
    """Generate human-like delay using normal distribution (bell curve)."""
    mean = (min_sec + max_sec) / 2
    std_dev = (max_sec - min_sec) / 4
    delay = random.gauss(mean, std_dev)
    # Clamp to reasonable range
    return max(min_sec * 0.5, min(max_sec * 1.5, delay))


def _simulate_mouse_movement(page, num_movements: int = None):
    """Simulate natural mouse movements across the page."""
    try:
        viewport = page.viewport_size
        if not viewport:
            return

        width, height = viewport['width'], viewport['height']
        num_movements = num_movements or random.randint(3, 6)

        for _ in range(num_movements):
            # Random target position (avoid edges)
            x = random.randint(100, width - 100)
            y = random.randint(100, height - 100)

            # Random movement speed (steps)
            steps = random.randint(15, 40)
            page.mouse.move(x, y, steps=steps)

            # Micro-pause between movements
            time.sleep(random.uniform(0.05, 0.3))

        logger.debug(f"Simulated {num_movements} mouse movements")
    except Exception as e:
        logger.debug(f"Mouse simulation skipped: {e}")


def _simulate_scroll(page, scroll_down: bool = True):
    """Simulate natural scrolling behavior like reading a page."""
    try:
        # Get page dimensions
        page_height = page.evaluate("document.body.scrollHeight")
        viewport_height = page.viewport_size['height'] if page.viewport_size else 900

        if scroll_down:
            # Scroll down in chunks (like reading)
            current_position = 0
            max_scroll = min(page_height * 0.6, 3000)  # Don't scroll too far

            while current_position < max_scroll:
                # Random scroll amount (100-400 pixels, like mouse wheel)
                scroll_amount = random.randint(150, 400)
                current_position += scroll_amount

                # Smooth scroll
                page.evaluate(f"window.scrollTo({{top: {current_position}, behavior: 'smooth'}})")

                # Reading pause (varies by "content density")
                time.sleep(random.uniform(0.3, 1.2))

            # Sometimes scroll back up a bit (like re-reading)
            if random.random() > 0.6:
                scroll_back = random.randint(100, 300)
                page.evaluate(f"window.scrollBy({{top: -{scroll_back}, behavior: 'smooth'}})")
                time.sleep(random.uniform(0.2, 0.5))

        logger.debug(f"Simulated scroll behavior")
    except Exception as e:
        logger.debug(f"Scroll simulation skipped: {e}")


def _simulate_human_behavior(page):
    """Combined human behavior simulation."""
    # Random initial pause (like page is loading/rendering)
    time.sleep(_human_delay(0.5, 1.5))

    # Mouse movement
    _simulate_mouse_movement(page)

    # Short pause
    time.sleep(_human_delay(0.3, 0.8))

    # Scroll behavior
    _simulate_scroll(page)

    # Final pause before extraction
    time.sleep(_human_delay(0.5, 1.0))


# ============================================================================
# BROWSER PROFILE RANDOMIZATION
# ============================================================================

def _get_random_viewport() -> dict:
    """Get a random but realistic viewport size."""
    return random.choice(COMMON_VIEWPORTS)


def _get_random_location() -> dict:
    """
    DEPRECATED: Use UserAgentManager.get_random_location() instead.
    This provides the same functionality but with better logging.
    Kept for backward compatibility only.
    """
    location = random.choice(LOCATION_PROFILES)
    logger.debug(f"Selected location (legacy): {location.get('name', 'Unknown')}")
    return location


def _get_random_headers() -> dict:
    """
    DEPRECATED: Use UserAgentManager.get_matching_headers() instead.
    This function returns hardcoded Chrome headers which may not match the selected user agent.
    Kept for backward compatibility only.
    """
    logger.warning("⚠️ _get_random_headers() is deprecated - use ua_manager.get_matching_headers() for consistent fingerprint")
    accept_languages = [
        "en-US,en;q=0.9",
        "en-US,en;q=0.9,es;q=0.8",
        "en-GB,en;q=0.9,en-US;q=0.8",
        "en-US,en;q=0.9,fr;q=0.8",
    ]

    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": random.choice(accept_languages),
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }


def _get_referrer(target_url: str) -> Optional[str]:
    """Generate a realistic referrer based on target URL."""
    domain = urlparse(target_url).netloc

    # Weighted referrer options
    referrers = [
        (f"https://www.google.com/search?q={domain.replace('.', '+')}", 0.4),
        ("https://www.google.com/", 0.2),
        ("https://news.google.com/", 0.15),
        (None, 0.15),  # Direct visit
        ("https://t.co/", 0.05),  # Twitter
        ("https://www.facebook.com/", 0.05),
    ]

    r = random.random()
    cumulative = 0
    for ref, weight in referrers:
        cumulative += weight
        if r <= cumulative:
            return ref

    return None


def _inject_anti_detection_scripts(context_or_page, is_context: bool = False):
    """
    Inject all anti-detection JavaScript.
    
    Args:
        context_or_page: Either a BrowserContext or Page object
        is_context: If True, inject at context level (applies to all pages)
    """
    try:
        target = context_or_page
        target_type = "context" if is_context else "page"
        
        target.add_init_script(CANVAS_NOISE_SCRIPT)
        target.add_init_script(WEBGL_SPOOF_SCRIPT)
        target.add_init_script(BROWSER_PATCHES_SCRIPT)
        
        logger.info(f"🛡️ Injected anti-detection scripts at {target_type} level")
        logger.debug(f"   └─ Canvas noise, WebGL spoof, Browser patches")
    except Exception as e:
        logger.warning(f"⚠️ Failed to inject anti-detection scripts: {e}")


# ============================================================================
# PROXY MANAGER CLASS
# ============================================================================

class ProxyManager:
    """Manages proxy rotation with health tracking."""

    def __init__(self, proxies: List[dict]):
        self.proxies = proxies
        self.failed_counts: Dict[str, int] = {}  # {server: failure_count}
        self.last_used: Dict[str, float] = {}  # {server: timestamp}
        self.cooldown_until: Dict[str, float] = {}  # {server: timestamp}

    def get_proxy(self) -> Optional[dict]:
        """Get a healthy proxy that hasn't been used recently."""
        if not self.proxies:
            return None

        now = time.time()
        min_interval = 30  # Minimum seconds between using same proxy

        available = [
            p for p in self.proxies
            if self.failed_counts.get(p['server'], 0) < 3
            and now - self.last_used.get(p['server'], 0) > min_interval
            and now > self.cooldown_until.get(p['server'], 0)
        ]

        if not available:
            # Reset failed proxies if all are marked or on cooldown
            logger.warning("All proxies exhausted, resetting...")
            self.failed_counts = {}
            self.cooldown_until = {}
            available = self.proxies

        proxy = random.choice(available)
        self.last_used[proxy['server']] = now
        return proxy

    def mark_failed(self, proxy: dict, cooldown_seconds: int = 120):
        """Mark a proxy as failed and put it on cooldown."""
        if not proxy:
            return

        server = proxy['server']
        self.failed_counts[server] = self.failed_counts.get(server, 0) + 1
        self.cooldown_until[server] = time.time() + cooldown_seconds

        logger.warning(f"Proxy {server} marked failed (count: {self.failed_counts[server]})")

    def mark_success(self, proxy: dict):
        """Mark a proxy as successful, reset its failure count."""
        if not proxy:
            return

        server = proxy['server']
        self.failed_counts[server] = 0
        if server in self.cooldown_until:
            del self.cooldown_until[server]


# ============================================================================
# ENHANCED CLOUDFLARE HANDLING
# ============================================================================

def _is_cloudflare_challenge(page) -> bool:
    """
    Smart Cloudflare challenge detection.
    Only triggers on REAL Cloudflare challenge pages, not articles that mention Cloudflare.
    """
    try:
        # First check: Element-based detection (most reliable)
        cf_selectors = [
            "#challenge-running",
            "#challenge-stage", 
            ".cf-browser-verification",
            "#cf-challenge-running",
            "#cf-wrapper",
            "#cf-hcaptcha-container",
            ".cf-turnstile",
        ]

        for selector in cf_selectors:
            if page.locator(selector).count() > 0:
                logger.debug(f"Cloudflare detected via selector: {selector}")
                return True

        # Second check: Page title indicates challenge
        page_title = (page.title() or "").lower()
        cf_title_indicators = ["just a moment", "attention required", "checking your browser"]
        if any(indicator in page_title for indicator in cf_title_indicators):
            logger.debug(f"Cloudflare detected via title: {page_title}")
            return True

        # Third check: Very short page with CF indicators (real challenge pages are short)
        page_content = page.content() or ""
        content_length = len(page_content)
        
        # Real Cloudflare challenge pages are typically < 50KB
        if content_length < 50000:
            page_text = (page.text_content("body") or "").lower()
            
            # Only trigger on SPECIFIC Cloudflare challenge phrases
            # NOT generic words like "cloudflare" which could be in article content
            challenge_phrases = [
                "checking your browser before",
                "this process is automatic",
                "you will be redirected",
                "ray id:",
                "enable javascript and cookies",
                "ddos protection by",
                "please stand by",
                "verify you are human",
            ]
            
            for phrase in challenge_phrases:
                if phrase in page_text:
                    logger.debug(f"Cloudflare detected via phrase: {phrase}")
                    return True

        return False
    except Exception as e:
        logger.debug(f"Cloudflare detection error: {e}")
        return False


def _wait_for_cloudflare(page, max_wait: int = 45) -> bool:
    """Wait for Cloudflare challenge with extended timeout."""
    if not _is_cloudflare_challenge(page):
        return True

    logger.info("Cloudflare challenge detected, waiting...")
    start = time.time()

    while time.time() - start < max_wait:
        time.sleep(3)

        if not _is_cloudflare_challenge(page):
            logger.info(f"Cloudflare challenge passed after {time.time() - start:.1f}s")
            return True

        logger.debug(f"Still waiting for Cloudflare... ({time.time() - start:.1f}s)")

    logger.warning(f"Cloudflare challenge timeout after {max_wait}s")
    return False


# ============================================================================
# ORIGINAL HELPER FUNCTIONS
# ============================================================================

def _mask_proxy(proxy: dict) -> str:
    """Mask proxy credentials for safe logging."""
    if not proxy:
        return "None"
    server = proxy.get("server", "unknown")
    username = proxy.get("username", "")
    if username:
        return f"{server} (user: {username[:3]}***)"
    return server


def _classify_error(error_msg: str, page_content: str = "", page_title: str = "") -> dict:
    """Classify error type for better debugging and ban detection.
    
    IMPORTANT: Only check for ban indicators in specific contexts to avoid false positives
    when scraping articles about security, firewalls, etc.
    """
    error_lower = error_msg.lower()
    title_lower = page_title.lower() if page_title else ""
    
    # Only check first 2000 chars of content - error pages are typically short
    # This prevents false positives from articles about security, WAF, etc.
    content_lower = page_content[:2000].lower() if page_content else ""

    classification = {
        "type": "unknown",
        "likely_ban": False,
        "retry_recommended": True,
        "details": ""
    }

    # Cloudflare challenge - check first (common case)
    # Only trigger if the page is SHORT (real error page) or has specific Cloudflare structure
    cloudflare_indicators = ["just a moment", "checking your browser", "ray id", "cf-browser-verification"]
    is_cloudflare = any(x in content_lower for x in cloudflare_indicators)
    
    if is_cloudflare and len(page_content) < 50000:  # Real Cloudflare pages are short
        classification["type"] = "cloudflare_challenge"
        classification["likely_ban"] = False
        classification["retry_recommended"] = True
        classification["details"] = "Cloudflare challenge - may need longer wait time"
        return classification

    # CAPTCHA / Bot detection - these are very specific phrases
    captcha_indicators = ["verify you are human", "press & hold", "prove you're not a robot", 
                         "complete the captcha", "security check", "one more step"]
    if any(x in content_lower for x in captcha_indicators):
        classification["type"] = "bot_detection"
        classification["likely_ban"] = True
        classification["retry_recommended"] = True
        classification["details"] = "Bot detection triggered - consider slower scraping or different proxy"
        return classification

    # Rate limiting - only in error message or TITLE (not body content)
    rate_limit_in_title = any(x in title_lower for x in ["rate limit", "too many requests", "429", "throttle"])
    rate_limit_in_error = any(x in error_lower for x in ["rate limit", "too many requests", "429", "throttle"])
    if rate_limit_in_title or rate_limit_in_error:
        classification["type"] = "rate_limit"
        classification["likely_ban"] = True
        classification["retry_recommended"] = False
        classification["details"] = "Rate limit detected - consider increasing delays or rotating proxies"
        return classification

    # Access denied - ONLY check title, not body (to avoid false positives on security articles)
    access_denied_title_indicators = ["access denied", "403 forbidden", "blocked", "you have been blocked"]
    is_access_denied_title = any(x in title_lower for x in access_denied_title_indicators)
    
    # Also check if the page is very short (typical error page)
    is_short_error_page = len(page_content) < 5000 and any(x in content_lower for x in 
                          ["access denied", "you have been blocked", "your ip has been blocked"])
    
    if is_access_denied_title or is_short_error_page:
        classification["type"] = "access_denied"
        classification["likely_ban"] = True
        classification["retry_recommended"] = False
        classification["details"] = "Access denied - IP or proxy may be blocked"
        return classification

    # Timeout
    if any(x in error_lower for x in ["timeout", "timed out"]):
        classification["type"] = "timeout"
        classification["likely_ban"] = False
        classification["retry_recommended"] = True
        classification["details"] = "Request timed out - may be network issue or slow target"
        return classification

    # Connection errors
    if any(x in error_lower for x in ["connection", "network", "refused", "unreachable"]):
        classification["type"] = "connection_error"
        classification["likely_ban"] = False
        classification["retry_recommended"] = True
        classification["details"] = "Connection error - check proxy or network"
        return classification

    # Paywall - only if it appears prominently (in first 3000 chars, not in article body)
    paywall_indicators = ["subscribe to continue", "sign in to read", "premium content", "paywall"]
    if any(x in content_lower[:3000] for x in paywall_indicators):
        classification["type"] = "paywall"
        classification["likely_ban"] = False
        classification["retry_recommended"] = False
        classification["details"] = "Content behind paywall"
        return classification

    return classification


def _save_failure_screenshot(page, url: str, error_type: str, error_msg: str) -> Optional[str]:
    """Save screenshot and metadata when scraping fails."""
    import os
    from datetime import datetime

    try:
        # Create directory structure
        date_str = datetime.now().strftime("%Y-%m-%d")
        screenshot_dir = f"screenshots/{date_str}"
        os.makedirs(screenshot_dir, exist_ok=True)

        # Generate unique filename from URL and timestamp
        timestamp = datetime.now().strftime("%H%M%S")
        # Clean URL for filename
        safe_url = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_").replace("&", "_")[:50]
        filename = f"{timestamp}_{error_type}_{safe_url}"

        # Save screenshot
        screenshot_path = f"{screenshot_dir}/{filename}.png"
        try:
            page.screenshot(path=screenshot_path, full_page=True)
        except Exception:
            # Fallback to viewport only if full page fails
            page.screenshot(path=screenshot_path)

        # Save metadata JSON
        metadata = {
            "url": url,
            "final_url": page.url,
            "page_title": page.title(),
            "error_type": error_type,
            "error_message": error_msg,
            "timestamp": datetime.now().isoformat(),
            "screenshot_file": f"{filename}.png"
        }
        metadata_path = f"{screenshot_dir}/{filename}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Screenshot saved: {screenshot_path}")
        return screenshot_path

    except Exception as e:
        logger.warning(f"Failed to save screenshot: {e}")
        return None


class WebScraper:
    def __init__(self, config_path="config/config.json", proxies=None):
        self.ddgs = DDGS()
        self.ua = UserAgent()

        # Load configuration
        self.config = self._load_config(config_path)

        # Load proxies from file if not provided
        if proxies is None and self.config["proxies"]["enabled"]:
            proxies = self._load_proxies()
        self.proxies = proxies or []

        # Initialize ProxyManager for smart proxy rotation
        self.proxy_manager = ProxyManager(self.proxies) if self.proxies else None

        # Initialize enhanced UserAgentManager with 50+ user agents
        self.ua_manager = UserAgentManager()
        logger.info(f"🌐 Initialized UserAgentManager with {self.ua_manager.get_total_user_agents()} user agents")
        
        # Initialize advanced logging system
        self.adv_logger = get_advanced_logger()
        logger.info(f"📊 Advanced logging system initialized")
        
        # Initialize domain-level rate limiter (NEW)
        rate_limit_config = self.config.get("rate_limiting", {})
        self.domain_rate_limiter = DomainRateLimiter(
            max_requests_per_domain_per_hour=rate_limit_config.get("max_requests_per_domain_per_hour", 30),
            min_delay_between_requests=rate_limit_config.get("min_delay_between_requests", 5),
            max_delay_between_requests=rate_limit_config.get("max_delay_between_requests", 15)
        )
        logger.info(f"🚦 Domain rate limiter initialized (max {rate_limit_config.get('max_requests_per_domain_per_hour', 30)}/hr/domain)")
        
        # Initialize session manager for cookie persistence (NEW)
        self.session_manager = SessionManager(sessions_dir="sessions")
        logger.info(f"🍪 Session manager initialized for cookie persistence")
        
        # Keep legacy user_agents list for backward compatibility
        self.user_agents = self.config["user_agents"]

        # Rate limiting state
        self.last_request_time = 0
        self.min_request_interval = self.config.get("anti_detection", {}).get("min_request_interval", 5)

    def _apply_rate_limiting(self):
        """Ensure minimum time between requests."""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed + random.uniform(0, 3)
                logger.debug(f"Rate limiting: waiting {wait_time:.1f}s before next request")
                time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path) as f:
                config = json.load(f)
                logger.info(f"✅ Loaded configuration from {config_path}")
                return config
        except Exception as e:
            logger.warning(f"⚠️  Failed to load config: {e}. Using defaults.")
            # Return default config
            return {
                "proxies": {"enabled": False, "proxy_file": "Webshare 10 proxies.txt"},
                "browser": {"headless": True, "slow_mo": 200, "timeout": 60000},
                "user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ],
                "retry": {"max_attempts": 3, "min_wait": 2, "max_wait": 10},
                "strategies": [
                    {"wait": "domcontentloaded", "timeout": 40000, "sleep": 4},
                    {"wait": "load", "timeout": 60000, "sleep": 3},
                    {"wait": "networkidle", "timeout": 80000, "sleep": 2}
                ]
            }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def extract_article(
        self,
        url: str,
        allow_manual: bool = False,
        headless: Optional[bool] = None,
        storage_state_path: Optional[str] = None,
    ) -> dict:
        """
        Extracts the main article content from a given URL using Playwright with stealth mode.
        Includes retry logic, user-agent rotation, and bot detection handling.
        Now with full anti-detection suite: fingerprint randomization, human behavior simulation,
        proxy health tracking, and rate limiting.
        """
        if headless is None:
            headless = self.config["browser"]["headless"]

        # Apply domain-level rate limiting (NEW - tracks per-domain request history)
        can_request, wait_time, reason = self.domain_rate_limiter.can_request(url)
        if not can_request:
            logger.warning(f"🚦 Domain rate limit: {reason}")
            if wait_time > 300:  # More than 5 minutes
                logger.error(f"❌ Aborting: would need to wait {wait_time:.0f}s")
                return {
                    "error": f"Domain rate limit exceeded: {reason}",
                    "url": url,
                    "retry_after": wait_time
                }
            logger.info(f"⏳ Waiting {wait_time:.1f}s before request...")
            time.sleep(wait_time)
        
        # Apply legacy rate limiting between requests
        self._apply_rate_limiting()
        
        # Record this request in domain tracker
        self.domain_rate_limiter.record_request(url)

        max_retries = 3
        last_error = "Unknown error"
        content = None
        simple_text = None
        final_url = url
        proxy = None
        session = None  # Advanced logging session
        
        # Track profile for API response
        used_browser_profile = None
        used_location = None
        
        # Check for saved session (cookie persistence)
        if storage_state_path is None and self.session_manager.should_use_session(url):
            storage_state_path = self.session_manager.get_session(url)

        for attempt in range(max_retries):
            if attempt > 0:
                logger.info(f"  🔄 Retry attempt {attempt + 1}/{max_retries}...")
                # Use human-like delay between retries
                time.sleep(_human_delay(3, 8))
                
                # On retry, switch proxy if available (NEW)
                if self.proxy_manager and proxy:
                    logger.info("  🔄 Switching proxy for retry...")
                    self.proxy_manager.mark_failed(proxy, cooldown_seconds=60)

            # Start advanced logging session
            session = self.adv_logger.start_session(url, attempt + 1, max_retries)

            try:
                with sync_playwright() as p:
                    slow_mo = random.randint(150, 300)
                    
                    browser = p.chromium.launch(
                        headless=headless,
                        slow_mo=slow_mo,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--disable-dev-shm-usage',
                            '--no-sandbox',
                            '--disable-web-security',
                            '--disable-features=IsolateOrigins,site-per-process',
                        ]
                    )
                    
                    # Log browser launch
                    self.adv_logger.log_browser_launched(session, headless, slow_mo)

                    # Get a complete browser profile with consistent fingerprint
                    browser_profile = self.ua_manager.get_random_profile()
                    user_agent = browser_profile.user_agent
                    
                    # Store browser profile for API response
                    used_browser_profile = browser_profile

                    # Get OS-matching viewport (more realistic fingerprint)
                    viewport = self.ua_manager.get_matching_viewport(browser_profile)
                    location = self.ua_manager.get_random_location(prefer_english=True)
                    
                    # Store location for API response
                    used_location = location

                    storage_state_arg = None
                    if storage_state_path and Path(storage_state_path).exists():
                        storage_state_arg = storage_state_path

                    # Get matching HTTP headers for the browser profile
                    http_headers = self.ua_manager.get_matching_headers(browser_profile)
                    
                    # Build context options with randomized fingerprint
                    context_options = {
                        "user_agent": user_agent,
                        "viewport": viewport,
                        "locale": location["locale"],
                        "timezone_id": location["timezone_id"],
                        "geolocation": location["geo"],
                        "permissions": ['geolocation'],
                        "extra_http_headers": http_headers,
                    }

                    # Add referrer
                    referrer = _get_referrer(url)
                    if referrer:
                        context_options["extra_http_headers"]["Referer"] = referrer

                    if storage_state_arg:
                        context_options["storage_state"] = storage_state_arg

                    # Use ProxyManager for smart proxy rotation
                    if self.proxy_manager:
                        proxy = self.proxy_manager.get_proxy()
                        if proxy:
                            context_options["proxy"] = {
                                "server": proxy["server"],
                                "username": proxy.get("username"),
                                "password": proxy.get("password"),
                            }
                    elif self.proxies:
                        proxy = random.choice(self.proxies)
                        context_options["proxy"] = {
                            "server": proxy["server"],
                            "username": proxy.get("username"),
                            "password": proxy.get("password"),
                        }
                        logger.info(f"Using proxy: {_mask_proxy(proxy)}")

                    logger.debug(f"Browser profile: viewport={viewport}, locale={location['locale']}, tz={location['timezone_id']}")

                    # Log anti-detection configuration with advanced logger
                    self.adv_logger.log_anti_detection_config(
                        session, browser_profile, viewport, location, proxy, referrer
                    )

                    context = browser.new_context(**context_options)
                    
                    # Inject anti-detection scripts at CONTEXT level (applies to all pages/navigations)
                    _inject_anti_detection_scripts(context, is_context=True)
                    # Inject ADVANCED anti-detection scripts (audio, fonts, performance, etc.)
                    inject_advanced_anti_detection(context, is_context=True)
                    self.adv_logger.log_anti_detection_scripts(session, "context")
                    
                    page = context.new_page()

                    # Apply stealth mode (patches navigator, webdriver, etc.)
                    stealth = Stealth()
                    stealth.apply_stealth_sync(page)
                    self.adv_logger.log_stealth_applied(session)

                    # Also inject at page level for redundancy (will apply on next navigation)
                    _inject_anti_detection_scripts(page)
                    inject_advanced_anti_detection(page)
                    self.adv_logger.log_anti_detection_scripts(session, "page")

                    # Block images, media, and fonts to save bandwidth
                    def block_resources(route):
                        resource_type = route.request.resource_type
                        if resource_type in ['image', 'media', 'font']:
                            route.abort()
                        else:
                            route.continue_()

                    page.route("**/*", block_resources)
                    logger.debug("Enabled resource blocking (images, media, fonts)")
                    
                    strategies = self.config.get("strategies", [
                        {"wait": "domcontentloaded", "timeout": 40000, "sleep": 4},
                        {"wait": "load", "timeout": 60000, "sleep": 3},
                        {"wait": "networkidle", "timeout": 80000, "sleep": 2}
                    ])
                    
                    for i, strategy in enumerate(strategies):
                        try:
                            # Log navigation start
                            self.adv_logger.log_navigation_start(session, strategy)
                            
                            page.goto(url, wait_until=strategy["wait"], timeout=strategy["timeout"])
                            final_url = page.url
                            
                            # Log page loaded
                            self.adv_logger.log_page_loaded(session, final_url, page.title())
                            
                            # Popup dismissal
                            try:
                                popup_selectors = [
                                    "button:has-text('Accept all cookies')",
                                    "button:has-text('Accept All Cookies')",
                                    "#credential_picker_container",
                                    "iframe[src*='accounts.google.com']", 
                                    "#gsi_permission_iframe",
                                    "button:has-text('Sign in with Google')",
                                    "button:has-text('Stay signed out')",
                                    "button:has-text('Open in app')",
                                    "a:has-text('Open in app')",
                                    "button:has-text('Continue in browser')",
                                    "button:has-text('Maybe later')",
                                    "button:has-text('Not now')",
                                    "button:has-text('Close')",
                                    "a:has-text('Back Home')",
                                    "button:has-text('Back Home')",
                                    "a:has-text('Already a subscriber?')",
                                    "button:has-text('Already a subscriber?')",
                                    "button:has-text('Unlock Digital Access')",
                                    "button:has-text('Accept')",
                                    "button:has-text('Agree')",
                                    "button:has-text('OK')",
                                    "button:has-text('Accept All')",
                                    "button:has-text('Accept Cookies')",
                                    "button:has-text('Got it')",
                                    "button[aria-label='Close']",
                                    "button[title='Close']",
                                    "button.close",
                                    ".close-button",
                                    "button#onetrust-accept-btn-handler",
                                    "button:has-text('Accept All Cookies')",
                                    "button:has-text('Accept all cookies')",
                                    "button:has-text('Decline all cookies')",
                                    "button:has-text('ACT NOW')",
                                    "a:has-text('ACT NOW')",
                                ]
                                
                                for selector in popup_selectors:
                                    try:
                                        button = page.locator(selector).first
                                        if button.is_visible(timeout=1000):
                                            self.adv_logger.log_popup_dismissed(session, selector)
                                            button.click(timeout=2000)
                                            page.wait_for_timeout(2000)
                                            break
                                    except Exception:
                                        continue
                                        
                                # Restore iframe handling for cookie banners
                                try:
                                    for frame in page.frames:
                                        try:
                                            # Common cookie banner selectors inside iframes
                                            iframe_selectors = [
                                                "button:has-text('Accept')",
                                                "button:has-text('Accept All')",
                                                "button:has-text('Agree')",
                                                "button.cm__btn[data-role='all']",
                                            ]
                                            for sel in iframe_selectors:
                                                el = frame.locator(sel).first
                                                if el.is_visible(timeout=1000):
                                                    self.adv_logger.log_popup_dismissed(session, f"iframe:{sel}")
                                                    el.click(timeout=2000)
                                                    break
                                        except Exception:
                                            pass
                                except Exception:
                                    pass

                                # Enhanced Cloudflare handling with longer timeout
                                cf_start = time.time()
                                cf_passed = _wait_for_cloudflare(page, max_wait=45)
                                cf_time = time.time() - cf_start
                                if cf_time > 1:  # Only log if we actually waited
                                    self.adv_logger.log_cloudflare_detected(session, cf_time)

                                page.evaluate("""
                                    () => {
                                        if (document.body && window.getComputedStyle(document.body).overflow === 'hidden') {
                                            document.body.style.overflow = 'auto';
                                        }
                                    }
                                """)
                            except Exception:
                                pass

                            if self._handle_press_and_hold(page):
                                try:
                                    page.wait_for_load_state('networkidle', timeout=30000)
                                except Exception:
                                    pass

                            # Human-like delay (normal distribution instead of fixed)
                            time.sleep(_human_delay(strategy["sleep"] - 1, strategy["sleep"] + 2))

                            # Simulate human behavior (mouse movement, scrolling)
                            _simulate_human_behavior(page)
                            self.adv_logger.log_human_behavior(session, mouse_moves=random.randint(3, 6), scrolls=random.randint(2, 5))
                            
                            # Access Denied / Ban check with SMART detection
                            # Only trigger on real error pages, not articles about security
                            page_content_raw = page.content()
                            page_content = page_content_raw.lower()
                            page_title = page.title()
                            page_title_lower = page_title.lower()
                            content_length = len(page_content_raw)

                            error_classification = _classify_error("", page_content_raw, page_title_lower)
                            
                            # Smart ban detection: only trigger if:
                            # 1. Error classification says it's a ban AND
                            # 2. Page is short (real error pages are <10KB) OR title clearly indicates error
                            is_short_page = content_length < 10000
                            title_indicates_error = any(x in page_title_lower for x in 
                                ["access denied", "blocked", "forbidden", "error", "captcha", "verify"])
                            
                            is_real_ban = error_classification["likely_ban"] and (is_short_page or title_indicates_error)

                            if is_real_ban:
                                # Capture screenshot for analysis
                                screenshot_path = _save_failure_screenshot(page, url, error_classification['type'], f"Ban/block detected: {page_title}")

                                # Mark proxy as failed for smart rotation
                                if self.proxy_manager and proxy:
                                    self.proxy_manager.mark_failed(proxy, cooldown_seconds=180)

                                # Log failure with advanced logger
                                self.adv_logger.log_session_failed(
                                    session,
                                    error_type=error_classification['type'],
                                    error_message=f"Ban/block detected: {page_title}",
                                    likely_ban=True,
                                    screenshot_path=screenshot_path or ""
                                )
                                raise Exception(f"Access Denied by target site - Type: {error_classification['type']}")

                            content = page.content()
                            
                            # Fallback: Try to extract text from specific content containers
                            simple_text = ""
                            extraction_method = "trafilatura"
                            try:
                                # Priority list of selectors to avoid navigation/footer/cookie text
                                content_selectors = [
                                    "article", 
                                    "[role='main']", 
                                    "main", 
                                    ".post-content", 
                                    ".article-body", 
                                    ".entry-content", 
                                    "#main-content",
                                    "body" # Last resort
                                ]
                                
                                for selector in content_selectors:
                                    loc = page.locator(selector)
                                    if loc.count() > 0 and loc.first.is_visible():
                                        text = loc.first.inner_text()
                                        if len(text) > 500: 
                                            simple_text = text
                                            extraction_method = f"fallback:{selector}"
                                            logger.info(f"  📄 Fallback extraction using selector: '{selector}'")
                                            break
                            except Exception:
                                simple_text = ""
                                
                            final_url = page.url
                            # Log content extraction
                            self.adv_logger.log_content_extracted(
                                session, 
                                html_length=len(content) if content else 0,
                                text_length=len(simple_text),
                                extraction_method=extraction_method,
                                success=content and len(content) > 1000
                            )
                            
                            if content and len(content) > 1000:
                                break
                        except Exception as e:
                            last_error = str(e)
                            if "Access Denied" in last_error:
                                raise
                            continue

                    # Capture screenshot if content extraction failed (before browser closes)
                    if not content or len(content) < 1000:
                        screenshot_path = _save_failure_screenshot(page, url, "extraction_failed", f"Content too short or empty (len={len(content) if content else 0})")
                        self.adv_logger.log_session_failed(
                            session,
                            error_type="extraction_failed",
                            error_message=f"Content too short or empty (len={len(content) if content else 0})",
                            likely_ban=False,
                            screenshot_path=screenshot_path or ""
                        )
                    else:
                        # Mark proxy as successful for smart rotation
                        if self.proxy_manager and proxy:
                            self.proxy_manager.mark_success(proxy)
                        
                        # Save session (cookies) for future requests (NEW)
                        try:
                            self.session_manager.save_session(context, url)
                        except Exception as session_err:
                            logger.debug(f"Could not save session: {session_err}")
                        
                        # Log successful session
                        self.adv_logger.log_session_success(session)

                    browser.close()
                    if content and len(content) > 1000:
                        break
            except Exception as e:
                last_error = str(e)
                error_classification = _classify_error(last_error)
                
                # Log failure with advanced logger
                if session:
                    self.adv_logger.log_session_failed(
                        session,
                        error_type=error_classification['type'],
                        error_message=str(e)[:200],
                        likely_ban=error_classification['likely_ban']
                    )
                
                if attempt == max_retries - 1:
                    break
                continue
        
        if not content:
            error_classification = _classify_error(last_error)
            
            # Log overall stats after complete failure
            self.adv_logger.log_overall_stats()
            
            return {
                "error": f"Failed after {max_retries} attempts. Last error: {last_error}",
                "error_type": error_classification["type"],
                "likely_ban": error_classification["likely_ban"],
                "recommendation": error_classification["details"],
                "final_url": url,
                "user_agent_used": f"{used_browser_profile.browser}/{used_browser_profile.version}" if used_browser_profile else "unknown",
                "location_used": used_location.get("name", "unknown") if used_location else "unknown"
            }
            
        content_lower = content.lower()
        if "this feed is not available" in content_lower or "news:unfepa" in content:
            return {
                "error": "Google News article link expired or unavailable.",
                "final_url": final_url,
                "user_agent_used": f"{used_browser_profile.browser}/{used_browser_profile.version}" if used_browser_profile else "unknown",
                "location_used": used_location.get("name", "unknown") if used_location else "unknown"
            }
        
        result = trafilatura.extract(
            content, 
            output_format="json", 
            with_metadata=True,
            include_comments=False,
            favor_recall=True,
            include_tables=True,
            deduplicate=True
        )
        
        if result:
            parsed_result = json.loads(result)
            text = parsed_result.get('text', '')
            
            if len(text) < 100:
                return {
                    "error": "Insufficient content extracted. The page may be an error page, paywall, or require login.",
                    "final_url": final_url,
                    "extracted_text": text,
                    "user_agent_used": f"{used_browser_profile.browser}/{used_browser_profile.version}" if used_browser_profile else "unknown",
                    "location_used": used_location.get("name", "unknown") if used_location else "unknown"
                }
            
            # Add metadata for API response
            parsed_result['final_url'] = final_url
            parsed_result['user_agent_used'] = f"{used_browser_profile.browser}/{used_browser_profile.version}" if used_browser_profile else "unknown"
            parsed_result['location_used'] = used_location.get("name", "unknown") if used_location else "unknown"
            return parsed_result
        elif simple_text and len(simple_text) > 500:
            logger.warning("⚠️ Trafilatura failed to extract content. Falling back to raw text.")
            return {
                "title": "Extracted Content (Fallback)",
                "date": None,
                "source": final_url,
                "text": simple_text,
                "final_url": final_url,
                "user_agent_used": f"{used_browser_profile.browser}/{used_browser_profile.version}" if used_browser_profile else "unknown",
                "location_used": used_location.get("name", "unknown") if used_location else "unknown"
            }
        else:
            return {
                "error": "Could not extract content from the page.",
                "final_url": final_url,
                "user_agent_used": f"{used_browser_profile.browser}/{used_browser_profile.version}" if used_browser_profile else "unknown",
                "location_used": used_location.get("name", "unknown") if used_location else "unknown"
            }

    def find_source_from_text(self, text: str, num_results: int = 3) -> list:
        """Searches for the text snippet on DuckDuckGo and returns potential source URLs."""
        results = []
        try:
            query = f'"{text}"' if len(text) < 200 else text
            search_results = self.ddgs.text(query, region='us-en', max_results=num_results)
            if search_results:
                for res in search_results:
                    results.append({
                        "title": res.get("title"),
                        "url": res.get("href"),
                        "description": res.get("body")
                    })
            return results
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]
    
    def _load_proxies(self):
        """Load proxies from Webshare file"""
        proxy_filename = self.config["proxies"]["proxy_file"]
        config_dir = Path("config")
        proxy_file = config_dir / proxy_filename
        if not proxy_file.exists():
            proxy_file = Path(proxy_filename)
        if not proxy_file.exists():
            logger.warning(f"⚠️  Proxy file not found: {proxy_file}")
            return []
        
        proxies = []
        try:
            with open(proxy_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split(":")
                    if len(parts) == 4:
                        proxies.append({
                            "server": f"http://{parts[0]}:{parts[1]}",
                            "username": parts[2],
                            "password": parts[3]
                        })
            logger.info(f"✅ Loaded {len(proxies)} proxies from {proxy_file}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load proxies: {e}")
        return proxies

    def _handle_press_and_hold(self, page):
        """Detects and attempts to bypass 'Press & Hold' bot detection challenges."""
        try:
            selectors = [
                "button:has-text('Press & Hold')",
                "#px-captcha",
                "div[aria-label='Press & Hold']",
                ".press-and-hold",
                "button:has-text('Confirm you are a human')"
            ]
            for selector in selectors:
                button = page.locator(selector).first
                if button.is_visible(timeout=2000):
                    logger.info(f"  🤖 'Press & Hold' detected: {selector}")
                    box = button.bounding_box()
                    if not box:
                        continue
                    x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
                    y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
                    page.mouse.move(x, y, steps=10)
                    time.sleep(random.uniform(0.5, 1.0))
                    logger.info("  🖱️ Holding button...")
                    page.mouse.down()
                    hold_duration = random.uniform(3.5, 5.5)
                    time.sleep(hold_duration)
                    page.mouse.up()
                    logger.info("  🖱️ Released button.")
                    page.wait_for_timeout(3000)
                    return True
            return False
        except Exception as e:
            logger.warning(f"  ⚠️ Error during Press & Hold bypass: {e}")
            return False

if __name__ == "__main__":
    scraper = WebScraper()
    logger.info("Testing Scraper...")
