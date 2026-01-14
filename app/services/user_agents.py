"""
Comprehensive User Agent Manager for Anti-Detection
====================================================
Contains 50+ realistic, modern user agents organized by browser/OS type.
Smart selection logic to maintain consistency between user agent and other browser fingerprints.
"""

import random
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("user_agents")

# ============================================================================
# USER AGENT DATABASE - 50+ Modern User Agents (2024-2025)
# ============================================================================

# Chrome User Agents (Windows)
CHROME_WINDOWS_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# Chrome User Agents (macOS)
CHROME_MACOS_UA = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

# Chrome User Agents (Linux)
CHROME_LINUX_UA = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Firefox User Agents (Windows)
FIREFOX_WINDOWS_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Firefox User Agents (macOS)
FIREFOX_MACOS_UA = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.6; rv:120.0) Gecko/20100101 Firefox/120.0",
]

# Firefox User Agents (Linux)
FIREFOX_LINUX_UA = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Safari User Agents (macOS only)
SAFARI_MACOS_UA = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
]

# Edge User Agents (Windows)
EDGE_WINDOWS_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Edge User Agents (macOS)
EDGE_MACOS_UA = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
]

# Opera User Agents
OPERA_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
]

# ============================================================================
# BROWSER PROFILE DEFINITIONS
# ============================================================================

@dataclass
class BrowserProfile:
    """Represents a complete browser profile for anti-detection."""
    browser: str  # chrome, firefox, safari, edge, opera
    version: str  # browser version number
    os: str  # windows, macos, linux
    user_agent: str
    sec_ch_ua: str
    sec_ch_ua_platform: str
    sec_ch_ua_mobile: str = "?0"
    
    def __str__(self):
        return f"{self.browser.upper()}/{self.version} on {self.os.upper()}"


# Browser-specific Sec-CH-UA headers
SEC_CH_UA_TEMPLATES = {
    "chrome_120": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "chrome_121": '"Not_A Brand";v="8", "Chromium";v="121", "Google Chrome";v="121"',
    "chrome_122": '"Not_A Brand";v="8", "Chromium";v="122", "Google Chrome";v="122"',
    "chrome_123": '"Not_A Brand";v="8", "Chromium";v="123", "Google Chrome";v="123"',
    "chrome_124": '"Not_A Brand";v="8", "Chromium";v="124", "Google Chrome";v="124"',
    "chrome_125": '"Not_A Brand";v="8", "Chromium";v="125", "Google Chrome";v="125"',
    "chrome_126": '"Not_A Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "chrome_119": '"Not_A Brand";v="8", "Chromium";v="119", "Google Chrome";v="119"',
    "edge_120": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
    "edge_121": '"Not_A Brand";v="8", "Chromium";v="121", "Microsoft Edge";v="121"',
    "edge_122": '"Not_A Brand";v="8", "Chromium";v="122", "Microsoft Edge";v="122"',
    "edge_119": '"Not_A Brand";v="8", "Chromium";v="119", "Microsoft Edge";v="119"',
    "opera_106": '"Not_A Brand";v="8", "Chromium";v="120", "Opera";v="106"',
    "opera_105": '"Not_A Brand";v="8", "Chromium";v="119", "Opera";v="105"',
    "firefox": "",  # Firefox doesn't send Sec-CH-UA
    "safari": "",   # Safari doesn't send Sec-CH-UA
}

SEC_CH_UA_PLATFORM = {
    "windows": '"Windows"',
    "macos": '"macOS"',
    "linux": '"Linux"',
}

# ============================================================================
# VIEWPORT PROFILES BY OS (more realistic matching)
# ============================================================================

VIEWPORTS_BY_OS = {
    "windows": [
        {"width": 1920, "height": 1080},  # Most common Windows
        {"width": 1366, "height": 768},   # Laptops
        {"width": 1536, "height": 864},   # Scaled displays
        {"width": 1280, "height": 720},   # HD
        {"width": 2560, "height": 1440},  # QHD monitors
        {"width": 1680, "height": 1050},  # Older monitors
        {"width": 1600, "height": 900},   # Common laptop
    ],
    "macos": [
        {"width": 1440, "height": 900},   # MacBook Air 13"
        {"width": 1680, "height": 1050},  # MacBook Pro 15" scaled
        {"width": 1512, "height": 982},   # MacBook Pro 14" default
        {"width": 1728, "height": 1117},  # MacBook Pro 16" default
        {"width": 2560, "height": 1440},  # External display
        {"width": 1920, "height": 1080},  # External display
    ],
    "linux": [
        {"width": 1920, "height": 1080},  # Most common
        {"width": 1366, "height": 768},   # Laptops
        {"width": 2560, "height": 1440},  # Dev monitors
        {"width": 1280, "height": 800},   # Older laptops
        {"width": 3840, "height": 2160},  # 4K (common for devs)
    ],
}

# ============================================================================
# LOCATION PROFILES DATABASE (30+ Locations)
# ============================================================================

LOCATION_PROFILES = [
    # United States
    {"name": "New York, USA", "timezone_id": "America/New_York", "locale": "en-US", "geo": {"latitude": 40.7128, "longitude": -74.0060}},
    {"name": "Los Angeles, USA", "timezone_id": "America/Los_Angeles", "locale": "en-US", "geo": {"latitude": 34.0522, "longitude": -118.2437}},
    {"name": "Chicago, USA", "timezone_id": "America/Chicago", "locale": "en-US", "geo": {"latitude": 41.8781, "longitude": -87.6298}},
    {"name": "Denver, USA", "timezone_id": "America/Denver", "locale": "en-US", "geo": {"latitude": 39.7392, "longitude": -104.9903}},
    {"name": "San Francisco, USA", "timezone_id": "America/Los_Angeles", "locale": "en-US", "geo": {"latitude": 37.7749, "longitude": -122.4194}},
    {"name": "Seattle, USA", "timezone_id": "America/Los_Angeles", "locale": "en-US", "geo": {"latitude": 47.6062, "longitude": -122.3321}},
    {"name": "Miami, USA", "timezone_id": "America/New_York", "locale": "en-US", "geo": {"latitude": 25.7617, "longitude": -80.1918}},
    {"name": "Boston, USA", "timezone_id": "America/New_York", "locale": "en-US", "geo": {"latitude": 42.3601, "longitude": -71.0589}},
    {"name": "Houston, USA", "timezone_id": "America/Chicago", "locale": "en-US", "geo": {"latitude": 29.7604, "longitude": -95.3698}},
    {"name": "Phoenix, USA", "timezone_id": "America/Phoenix", "locale": "en-US", "geo": {"latitude": 33.4484, "longitude": -112.0740}},
    
    # United Kingdom
    {"name": "London, UK", "timezone_id": "Europe/London", "locale": "en-GB", "geo": {"latitude": 51.5074, "longitude": -0.1278}},
    {"name": "Manchester, UK", "timezone_id": "Europe/London", "locale": "en-GB", "geo": {"latitude": 53.4808, "longitude": -2.2426}},
    {"name": "Birmingham, UK", "timezone_id": "Europe/London", "locale": "en-GB", "geo": {"latitude": 52.4862, "longitude": -1.8904}},
    
    # Canada
    {"name": "Toronto, Canada", "timezone_id": "America/Toronto", "locale": "en-CA", "geo": {"latitude": 43.6532, "longitude": -79.3832}},
    {"name": "Vancouver, Canada", "timezone_id": "America/Vancouver", "locale": "en-CA", "geo": {"latitude": 49.2827, "longitude": -123.1207}},
    {"name": "Montreal, Canada", "timezone_id": "America/Montreal", "locale": "fr-CA", "geo": {"latitude": 45.5017, "longitude": -73.5673}},
    
    # Australia
    {"name": "Sydney, Australia", "timezone_id": "Australia/Sydney", "locale": "en-AU", "geo": {"latitude": -33.8688, "longitude": 151.2093}},
    {"name": "Melbourne, Australia", "timezone_id": "Australia/Melbourne", "locale": "en-AU", "geo": {"latitude": -37.8136, "longitude": 144.9631}},
    {"name": "Brisbane, Australia", "timezone_id": "Australia/Brisbane", "locale": "en-AU", "geo": {"latitude": -27.4698, "longitude": 153.0251}},
    
    # Europe
    {"name": "Paris, France", "timezone_id": "Europe/Paris", "locale": "fr-FR", "geo": {"latitude": 48.8566, "longitude": 2.3522}},
    {"name": "Berlin, Germany", "timezone_id": "Europe/Berlin", "locale": "de-DE", "geo": {"latitude": 52.5200, "longitude": 13.4050}},
    {"name": "Amsterdam, Netherlands", "timezone_id": "Europe/Amsterdam", "locale": "nl-NL", "geo": {"latitude": 52.3676, "longitude": 4.9041}},
    {"name": "Madrid, Spain", "timezone_id": "Europe/Madrid", "locale": "es-ES", "geo": {"latitude": 40.4168, "longitude": -3.7038}},
    {"name": "Rome, Italy", "timezone_id": "Europe/Rome", "locale": "it-IT", "geo": {"latitude": 41.9028, "longitude": 12.4964}},
    {"name": "Stockholm, Sweden", "timezone_id": "Europe/Stockholm", "locale": "sv-SE", "geo": {"latitude": 59.3293, "longitude": 18.0686}},
    {"name": "Dublin, Ireland", "timezone_id": "Europe/Dublin", "locale": "en-IE", "geo": {"latitude": 53.3498, "longitude": -6.2603}},
    {"name": "Zurich, Switzerland", "timezone_id": "Europe/Zurich", "locale": "de-CH", "geo": {"latitude": 47.3769, "longitude": 8.5417}},
    {"name": "Vienna, Austria", "timezone_id": "Europe/Vienna", "locale": "de-AT", "geo": {"latitude": 48.2082, "longitude": 16.3738}},
    {"name": "Copenhagen, Denmark", "timezone_id": "Europe/Copenhagen", "locale": "da-DK", "geo": {"latitude": 55.6761, "longitude": 12.5683}},
    
    # Asia
    {"name": "Tokyo, Japan", "timezone_id": "Asia/Tokyo", "locale": "ja-JP", "geo": {"latitude": 35.6762, "longitude": 139.6503}},
    {"name": "Singapore", "timezone_id": "Asia/Singapore", "locale": "en-SG", "geo": {"latitude": 1.3521, "longitude": 103.8198}},
    {"name": "Hong Kong", "timezone_id": "Asia/Hong_Kong", "locale": "zh-HK", "geo": {"latitude": 22.3193, "longitude": 114.1694}},
    {"name": "Seoul, South Korea", "timezone_id": "Asia/Seoul", "locale": "ko-KR", "geo": {"latitude": 37.5665, "longitude": 126.9780}},
]

# ============================================================================
# USER AGENT MANAGER CLASS
# ============================================================================

class UserAgentManager:
    """
    Smart User Agent Manager for anti-detection.
    
    Features:
    - 50+ realistic modern user agents
    - Smart selection with browser/OS consistency
    - Weighted distribution (favoring common browsers)
    - Session-based or per-request rotation
    - Full logging of selected user agents
    """
    
    # Browser popularity weights (based on market share)
    BROWSER_WEIGHTS = {
        "chrome_windows": 0.35,  # Most common
        "chrome_macos": 0.15,
        "chrome_linux": 0.05,
        "firefox_windows": 0.08,
        "firefox_macos": 0.03,
        "firefox_linux": 0.02,
        "safari_macos": 0.12,
        "edge_windows": 0.12,
        "edge_macos": 0.02,
        "opera": 0.06,
    }
    
    ALL_USER_AGENTS: Dict[str, List[str]] = {
        "chrome_windows": CHROME_WINDOWS_UA,
        "chrome_macos": CHROME_MACOS_UA,
        "chrome_linux": CHROME_LINUX_UA,
        "firefox_windows": FIREFOX_WINDOWS_UA,
        "firefox_macos": FIREFOX_MACOS_UA,
        "firefox_linux": FIREFOX_LINUX_UA,
        "safari_macos": SAFARI_MACOS_UA,
        "edge_windows": EDGE_WINDOWS_UA,
        "edge_macos": EDGE_MACOS_UA,
        "opera": OPERA_UA,
    }
    
    def __init__(self, custom_user_agents: Optional[List[str]] = None):
        """
        Initialize UserAgentManager.
        
        Args:
            custom_user_agents: Optional list of custom user agents to use instead of defaults
        """
        self.custom_user_agents = custom_user_agents
        self._last_profile: Optional[BrowserProfile] = None
        self._usage_count: Dict[str, int] = {}
        
        # Build flat list of all user agents
        self._all_ua_list = []
        for ua_list in self.ALL_USER_AGENTS.values():
            self._all_ua_list.extend(ua_list)
        
        logger.info(f"🌐 UserAgentManager initialized with {len(self._all_ua_list)} user agents")
    
    def get_total_user_agents(self) -> int:
        """Get total number of available user agents."""
        if self.custom_user_agents:
            return len(self.custom_user_agents)
        return len(self._all_ua_list)
    
    def _parse_browser_info(self, user_agent: str) -> Tuple[str, str, str]:
        """
        Parse browser and OS info from user agent string.
        
        Returns:
            Tuple of (browser, os, version)
        """
        ua_lower = user_agent.lower()
        
        # Detect OS
        if "windows nt 11" in ua_lower:
            os_type = "windows"
        elif "windows nt 10" in ua_lower:
            os_type = "windows"
        elif "macintosh" in ua_lower or "mac os x" in ua_lower:
            os_type = "macos"
        elif "linux" in ua_lower:
            os_type = "linux"
        else:
            os_type = "windows"
        
        # Detect browser and version
        if "edg/" in ua_lower:
            browser = "edge"
            # Extract Edge version
            import re
            match = re.search(r'edg/(\d+)', ua_lower)
            version = match.group(1) if match else "120"
        elif "opr/" in ua_lower:
            browser = "opera"
            import re
            match = re.search(r'opr/(\d+)', ua_lower)
            version = match.group(1) if match else "106"
        elif "firefox/" in ua_lower:
            browser = "firefox"
            import re
            match = re.search(r'firefox/(\d+)', ua_lower)
            version = match.group(1) if match else "121"
        elif "safari/" in ua_lower and "chrome/" not in ua_lower:
            browser = "safari"
            import re
            match = re.search(r'version/(\d+)', ua_lower)
            version = match.group(1) if match else "17"
        else:
            browser = "chrome"
            import re
            match = re.search(r'chrome/(\d+)', ua_lower)
            version = match.group(1) if match else "120"
        
        return browser, os_type, version
    
    def _get_sec_ch_ua(self, browser: str, version: str) -> str:
        """Get appropriate Sec-CH-UA header for browser."""
        if browser == "firefox" or browser == "safari":
            return ""  # These browsers don't send Sec-CH-UA
        
        key = f"{browser}_{version}"
        if key in SEC_CH_UA_TEMPLATES:
            return SEC_CH_UA_TEMPLATES[key]
        
        # Fallback for unknown versions
        if browser == "chrome":
            return SEC_CH_UA_TEMPLATES.get("chrome_120", "")
        elif browser == "edge":
            return SEC_CH_UA_TEMPLATES.get("edge_120", "")
        elif browser == "opera":
            return SEC_CH_UA_TEMPLATES.get("opera_106", "")
        
        return ""
    
    def get_random_profile(self, prefer_browser: Optional[str] = None) -> BrowserProfile:
        """
        Get a random browser profile with consistent fingerprint data.
        
        Args:
            prefer_browser: Optional browser preference (chrome, firefox, safari, edge, opera)
        
        Returns:
            BrowserProfile with consistent user agent and headers
        """
        if self.custom_user_agents:
            user_agent = random.choice(self.custom_user_agents)
        else:
            # Select browser type based on weights
            if prefer_browser:
                # Filter to preferred browser
                matching_keys = [k for k in self.ALL_USER_AGENTS.keys() if k.startswith(prefer_browser)]
                if matching_keys:
                    category = random.choice(matching_keys)
                    user_agent = random.choice(self.ALL_USER_AGENTS[category])
                else:
                    user_agent = random.choice(self._all_ua_list)
            else:
                # Weighted random selection
                categories = list(self.BROWSER_WEIGHTS.keys())
                weights = list(self.BROWSER_WEIGHTS.values())
                category = random.choices(categories, weights=weights, k=1)[0]
                user_agent = random.choice(self.ALL_USER_AGENTS[category])
        
        # Parse browser info from user agent
        browser, os_type, version = self._parse_browser_info(user_agent)
        
        # Get consistent headers
        sec_ch_ua = self._get_sec_ch_ua(browser, version)
        sec_ch_ua_platform = SEC_CH_UA_PLATFORM.get(os_type, '"Windows"')
        
        profile = BrowserProfile(
            browser=browser,
            version=version,
            os=os_type,
            user_agent=user_agent,
            sec_ch_ua=sec_ch_ua,
            sec_ch_ua_platform=sec_ch_ua_platform,
        )
        
        # Track usage
        self._usage_count[user_agent] = self._usage_count.get(user_agent, 0) + 1
        self._last_profile = profile
        
        # Log the selection
        logger.info(f"🎭 Selected User-Agent: {browser.upper()}/{version} on {os_type.upper()}")
        logger.debug(f"   └─ Full UA: {user_agent[:80]}...")
        
        return profile
    
    def get_random_user_agent(self) -> str:
        """Get just a random user agent string (for simple use cases)."""
        profile = self.get_random_profile()
        return profile.user_agent
    
    def get_matching_headers(self, profile: BrowserProfile) -> Dict[str, str]:
        """
        Get HTTP headers that match the browser profile.
        
        Args:
            profile: The browser profile to match
        
        Returns:
            Dict of HTTP headers
        """
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Browser-specific Accept-Language
        if profile.os == "macos":
            headers["Accept-Language"] = "en-US,en;q=0.9"
        elif "linux" in profile.os:
            headers["Accept-Language"] = "en-US,en;q=0.9"
        else:
            headers["Accept-Language"] = random.choice([
                "en-US,en;q=0.9",
                "en-US,en;q=0.9,es;q=0.8",
                "en-GB,en;q=0.9,en-US;q=0.8",
            ])
        
        # Add Sec-CH-UA headers for Chromium-based browsers
        if profile.sec_ch_ua:
            headers["Sec-Ch-Ua"] = profile.sec_ch_ua
            headers["Sec-Ch-Ua-Mobile"] = profile.sec_ch_ua_mobile
            headers["Sec-Ch-Ua-Platform"] = profile.sec_ch_ua_platform
        
        return headers
    
    def get_random_location(self, prefer_english: bool = True) -> dict:
        """
        Get a random location profile.
        
        Args:
            prefer_english: If True, prefer English-speaking locations (higher weight)
        
        Returns:
            Location dict with timezone, locale, and geo coordinates
        """
        if prefer_english:
            # Filter to English locales
            english_locations = [loc for loc in LOCATION_PROFILES if loc["locale"].startswith("en")]
            if english_locations:
                location = random.choice(english_locations)
            else:
                location = random.choice(LOCATION_PROFILES)
        else:
            location = random.choice(LOCATION_PROFILES)
        
        logger.info(f"📍 Selected Location: {location['name']} ({location['timezone_id']})")
        
        return location
    
    def get_matching_viewport(self, profile: BrowserProfile) -> Dict[str, int]:
        """
        Get a viewport size that matches the browser profile's OS.
        
        Args:
            profile: The browser profile to match
        
        Returns:
            Dict with width and height
        """
        os_type = profile.os
        viewports = VIEWPORTS_BY_OS.get(os_type, VIEWPORTS_BY_OS["windows"])
        viewport = random.choice(viewports)
        
        logger.debug(f"📐 Selected viewport for {os_type}: {viewport['width']}x{viewport['height']}")
        
        return viewport
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get usage statistics for user agents."""
        return dict(self._usage_count)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global instance for simple access
_default_manager: Optional[UserAgentManager] = None


def get_user_agent_manager() -> UserAgentManager:
    """Get or create the default UserAgentManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = UserAgentManager()
    return _default_manager


def get_random_user_agent() -> str:
    """Convenience function to get a random user agent."""
    return get_user_agent_manager().get_random_user_agent()


def get_random_browser_profile() -> BrowserProfile:
    """Convenience function to get a random browser profile."""
    return get_user_agent_manager().get_random_profile()


def get_random_location(prefer_english: bool = True) -> dict:
    """Convenience function to get a random location."""
    return get_user_agent_manager().get_random_location(prefer_english)


def get_all_user_agents() -> List[str]:
    """Get list of all available user agents."""
    manager = get_user_agent_manager()
    return manager._all_ua_list.copy()


# ============================================================================
# TEST / DEBUG
# ============================================================================

if __name__ == "__main__":
    # Test the module
    logging.basicConfig(level=logging.DEBUG)
    
    manager = UserAgentManager()
    
    print(f"\n📊 Total User Agents Available: {manager.get_total_user_agents()}")
    print("\n🧪 Testing Random Profile Selection (5 samples):\n")
    
    for i in range(5):
        profile = manager.get_random_profile()
        location = manager.get_random_location()
        headers = manager.get_matching_headers(profile)
        
        print(f"Sample {i+1}:")
        print(f"  Browser: {profile.browser}")
        print(f"  OS: {profile.os}")
        print(f"  UA: {profile.user_agent[:70]}...")
        print(f"  Location: {location['name']}")
        print(f"  Sec-CH-UA: {profile.sec_ch_ua[:50]}..." if profile.sec_ch_ua else "  Sec-CH-UA: (not applicable)")
        print()
