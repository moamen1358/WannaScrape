"""
Advanced Logging System for Web Scraper
========================================
Provides detailed, structured logging for every scrape operation
with comprehensive session tracking, timing, and analytics.
"""

import logging
import time
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
import threading

# ============================================================================
# SCRAPE SESSION DATA CLASSES
# ============================================================================

@dataclass
class AntiDetectionConfig:
    """Stores anti-detection configuration used for a scrape."""
    user_agent: str = ""
    browser: str = ""
    os: str = ""
    browser_version: str = ""
    viewport_width: int = 0
    viewport_height: int = 0
    location_name: str = ""
    timezone: str = ""
    locale: str = ""
    geolocation: Dict[str, float] = field(default_factory=dict)
    proxy_server: str = ""
    proxy_masked: str = ""
    referrer: Optional[str] = None
    sec_ch_ua: str = ""
    
    def to_log_string(self) -> str:
        return f"""
    ┌─ BROWSER FINGERPRINT ────────────────────────────────────────┐
    │ Browser:     {self.browser.upper()} v{self.browser_version} on {self.os.upper()}
    │ User-Agent:  {self.user_agent[:70]}...
    │ Viewport:    {self.viewport_width}x{self.viewport_height}
    │ Sec-CH-UA:   {self.sec_ch_ua[:50] if self.sec_ch_ua else '(not applicable)'}...
    ├─ LOCATION PROFILE ───────────────────────────────────────────┤
    │ Location:    {self.location_name}
    │ Timezone:    {self.timezone}
    │ Locale:      {self.locale}
    │ Geo:         {self.geolocation.get('latitude', 0):.4f}, {self.geolocation.get('longitude', 0):.4f}
    ├─ NETWORK ────────────────────────────────────────────────────┤
    │ Proxy:       {self.proxy_masked or 'Direct (no proxy)'}
    │ Referrer:    {self.referrer or 'Direct visit'}
    └──────────────────────────────────────────────────────────────┘"""


@dataclass
class TimingMetrics:
    """Tracks timing for various phases of the scrape."""
    start_time: float = 0
    browser_launch_time: float = 0
    page_load_time: float = 0
    cloudflare_wait_time: float = 0
    human_behavior_time: float = 0
    content_extraction_time: float = 0
    total_time: float = 0
    
    def to_log_string(self) -> str:
        return f"""
    ┌─ TIMING BREAKDOWN ───────────────────────────────────────────┐
    │ Browser Launch:      {self.browser_launch_time:.2f}s
    │ Page Load:           {self.page_load_time:.2f}s
    │ Cloudflare Wait:     {self.cloudflare_wait_time:.2f}s
    │ Human Simulation:    {self.human_behavior_time:.2f}s
    │ Content Extraction:  {self.content_extraction_time:.2f}s
    │ ─────────────────────────────────────────────────────────────
    │ TOTAL TIME:          {self.total_time:.2f}s
    └──────────────────────────────────────────────────────────────┘"""


@dataclass 
class ContentMetrics:
    """Tracks content extraction results."""
    html_length: int = 0
    text_length: int = 0
    title: str = ""
    final_url: str = ""
    extraction_method: str = ""
    has_article: bool = False
    word_count: int = 0
    
    def to_log_string(self) -> str:
        return f"""
    ┌─ CONTENT METRICS ────────────────────────────────────────────┐
    │ Title:            {self.title[:50]}{'...' if len(self.title) > 50 else ''}
    │ Final URL:        {self.final_url[:60]}{'...' if len(self.final_url) > 60 else ''}
    │ HTML Size:        {self.html_length:,} bytes
    │ Text Size:        {self.text_length:,} chars
    │ Word Count:       ~{self.word_count:,} words
    │ Extraction:       {self.extraction_method}
    │ Has Article:      {'✅ Yes' if self.has_article else '❌ No'}
    └──────────────────────────────────────────────────────────────┘"""


@dataclass
class ScrapeSession:
    """Complete session data for a single scrape operation."""
    session_id: str = ""
    url: str = ""
    timestamp: str = ""
    attempt: int = 1
    max_attempts: int = 3
    status: str = "pending"  # pending, success, failed, banned
    
    anti_detection: AntiDetectionConfig = field(default_factory=AntiDetectionConfig)
    timing: TimingMetrics = field(default_factory=TimingMetrics)
    content: ContentMetrics = field(default_factory=ContentMetrics)
    
    error_type: str = ""
    error_message: str = ""
    error_details: str = ""
    likely_ban: bool = False
    
    strategies_tried: List[str] = field(default_factory=list)
    popups_dismissed: List[str] = field(default_factory=list)
    cloudflare_detected: bool = False
    screenshot_path: str = ""
    
    def to_dict(self) -> dict:
        """Convert session to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "url": self.url,
            "timestamp": self.timestamp,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "status": self.status,
            "anti_detection": asdict(self.anti_detection),
            "timing": asdict(self.timing),
            "content": asdict(self.content),
            "error_type": self.error_type,
            "error_message": self.error_message,
            "likely_ban": self.likely_ban,
            "strategies_tried": self.strategies_tried,
            "cloudflare_detected": self.cloudflare_detected,
        }


# ============================================================================
# ADVANCED LOGGER CLASS
# ============================================================================

class AdvancedScrapeLogger:
    """
    Advanced logging system for web scraping operations.
    
    Features:
    - Structured session logging
    - Detailed timing metrics
    - Anti-detection config logging
    - JSON log export for analysis
    - Real-time progress indicators
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.logger = logging.getLogger("scraper.advanced")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Session counter for unique IDs
        self._session_counter = 0
        self._lock = threading.Lock()
        
        # Current session
        self.current_session: Optional[ScrapeSession] = None
        
        # Statistics
        self.stats = {
            "total_scrapes": 0,
            "successful": 0,
            "failed": 0,
            "banned": 0,
            "total_time": 0,
            "avg_time": 0,
        }
    
    def get_stats(self) -> dict:
        """Return current statistics."""
        return {
            **self.stats,
            "success_rate": f"{(self.stats['successful'] / self.stats['total_scrapes'] * 100):.1f}%" if self.stats['total_scrapes'] > 0 else "0%",
            "ban_rate": f"{(self.stats['banned'] / self.stats['total_scrapes'] * 100):.1f}%" if self.stats['total_scrapes'] > 0 else "0%"
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        with self._lock:
            self._session_counter += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"SCRAPE_{timestamp}_{self._session_counter:04d}"
    
    def start_session(self, url: str, attempt: int = 1, max_attempts: int = 3) -> ScrapeSession:
        """Start a new scrape session."""
        session = ScrapeSession(
            session_id=self._generate_session_id(),
            url=url,
            timestamp=datetime.now().isoformat(),
            attempt=attempt,
            max_attempts=max_attempts,
            status="pending"
        )
        session.timing.start_time = time.time()
        self.current_session = session
        
        self.stats["total_scrapes"] += 1
        
        return session
    
    def log_anti_detection_config(
        self,
        session: ScrapeSession,
        browser_profile,  # BrowserProfile from user_agents.py
        viewport: dict,
        location: dict,
        proxy: Optional[dict] = None,
        referrer: Optional[str] = None
    ):
        """Log the anti-detection configuration used."""
        # Extract browser version from user agent
        import re
        ua = browser_profile.user_agent
        version_match = re.search(r'(?:Chrome|Firefox|Safari|Edge|OPR)/(\d+)', ua)
        version = version_match.group(1) if version_match else "unknown"
        
        session.anti_detection = AntiDetectionConfig(
            user_agent=browser_profile.user_agent,
            browser=browser_profile.browser,
            os=browser_profile.os,
            browser_version=version,
            viewport_width=viewport.get("width", 0),
            viewport_height=viewport.get("height", 0),
            location_name=location.get("name", "Unknown"),
            timezone=location.get("timezone_id", ""),
            locale=location.get("locale", ""),
            geolocation=location.get("geo", {}),
            proxy_server=proxy.get("server", "") if proxy else "",
            proxy_masked=self._mask_proxy(proxy) if proxy else "",
            referrer=referrer,
            sec_ch_ua=browser_profile.sec_ch_ua
        )
        
        url = session.url
        self.logger.info(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  📋 SESSION: {session.session_id}
║  🌐 URL: {url[:65]}{'...' if len(url) > 65 else ''}
║  🔄 ATTEMPT: {session.attempt}/{session.max_attempts}
║  ⏰ STARTED: {session.timestamp}
╠══════════════════════════════════════════════════════════════════════════╣
{session.anti_detection.to_log_string()}
╚══════════════════════════════════════════════════════════════════════════╝""")
    
    def log_browser_launched(self, session: ScrapeSession, headless: bool, slow_mo: int):
        """Log browser launch details."""
        session.timing.browser_launch_time = time.time() - session.timing.start_time
        
        self.logger.info(f"""
    🚀 BROWSER LAUNCHED
    ├─ Mode:       {'Headless' if headless else 'Visible'}
    ├─ Slow Mo:    {slow_mo}ms
    ├─ Launch Time: {session.timing.browser_launch_time:.2f}s
    └─ Args:       Anti-automation flags enabled""")
    
    def log_stealth_applied(self, session: ScrapeSession):
        """Log stealth mode application."""
        self.logger.info("""
    🥷 STEALTH MODE APPLIED
    ├─ Navigator patches (webdriver, plugins, languages)
    ├─ Chrome runtime patches
    ├─ Console patches  
    └─ Permission patches""")
    
    def log_anti_detection_scripts(self, session: ScrapeSession, level: str = "context"):
        """Log anti-detection script injection."""
        self.logger.info(f"""
    🛡️ ANTI-DETECTION SCRIPTS INJECTED ({level.upper()} level)
    ├─ Canvas fingerprint noise
    ├─ WebGL renderer/vendor spoof
    ├─ Hardware concurrency randomization
    ├─ Device memory randomization
    ├─ Plugin masking
    ├─ WebRTC IP leak protection
    ├─ Network connection spoof
    └─ Battery API spoof""")
    
    def log_navigation_start(self, session: ScrapeSession, strategy: dict):
        """Log navigation start."""
        session.strategies_tried.append(strategy.get("wait", "unknown"))
        
        self.logger.info(f"""
    🔗 NAVIGATING TO URL
    ├─ Strategy:   {strategy.get('wait', 'unknown')}
    ├─ Timeout:    {strategy.get('timeout', 0)/1000:.1f}s
    └─ Sleep:      {strategy.get('sleep', 0)}s after load""")
    
    def log_page_loaded(self, session: ScrapeSession, final_url: str, page_title: str):
        """Log successful page load."""
        session.timing.page_load_time = time.time() - session.timing.start_time - session.timing.browser_launch_time
        session.content.final_url = final_url
        session.content.title = page_title
        
        self.logger.info(f"""
    ✅ PAGE LOADED
    ├─ Final URL:  {final_url[:60]}{'...' if len(final_url) > 60 else ''}
    ├─ Title:      {page_title[:50]}{'...' if len(page_title) > 50 else ''}
    └─ Load Time:  {session.timing.page_load_time:.2f}s""")
    
    def log_popup_dismissed(self, session: ScrapeSession, selector: str):
        """Log popup dismissal."""
        session.popups_dismissed.append(selector)
        self.logger.info(f"    👆 Popup dismissed: {selector[:50]}")
    
    def log_cloudflare_detected(self, session: ScrapeSession, wait_time: float):
        """Log Cloudflare challenge detection."""
        session.cloudflare_detected = True
        session.timing.cloudflare_wait_time = wait_time
        
        self.logger.warning(f"""
    ⚠️ CLOUDFLARE CHALLENGE DETECTED
    ├─ Wait Time:  {wait_time:.1f}s
    └─ Status:     {'Passed' if wait_time < 45 else 'Timeout'}""")
    
    def log_human_behavior(self, session: ScrapeSession, mouse_moves: int = 0, scrolls: int = 0):
        """Log human behavior simulation."""
        session.timing.human_behavior_time = time.time() - session.timing.start_time - session.timing.page_load_time
        
        self.logger.info(f"""
    🧑 HUMAN BEHAVIOR SIMULATED
    ├─ Mouse Movements: {mouse_moves}
    ├─ Scroll Actions:  {scrolls}
    └─ Time Spent:      {session.timing.human_behavior_time:.2f}s""")
    
    def log_content_extracted(
        self, 
        session: ScrapeSession, 
        html_length: int,
        text_length: int,
        extraction_method: str,
        success: bool
    ):
        """Log content extraction results."""
        session.timing.content_extraction_time = time.time() - session.timing.start_time - session.timing.human_behavior_time
        session.timing.total_time = time.time() - session.timing.start_time
        
        session.content.html_length = html_length
        session.content.text_length = text_length
        session.content.extraction_method = extraction_method
        session.content.has_article = success
        session.content.word_count = len(session.content.title.split()) if text_length > 0 else 0
        
        self.logger.info(session.content.to_log_string())
    
    def log_session_success(self, session: ScrapeSession):
        """Log successful session completion."""
        session.status = "success"
        session.timing.total_time = time.time() - session.timing.start_time
        
        self.stats["successful"] += 1
        self.stats["total_time"] += session.timing.total_time
        self.stats["avg_time"] = self.stats["total_time"] / self.stats["successful"]
        
        self.logger.info(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ✅ SCRAPE SUCCESSFUL - {session.session_id}
╠══════════════════════════════════════════════════════════════════════════╣
{session.timing.to_log_string()}
{session.content.to_log_string()}
╠══════════════════════════════════════════════════════════════════════════╣
║  📊 SESSION STATS
║  ├─ Strategies Tried:   {', '.join(session.strategies_tried)}
║  ├─ Popups Dismissed:   {len(session.popups_dismissed)}
║  ├─ Cloudflare:         {'Yes - Passed' if session.cloudflare_detected else 'Not detected'}
║  └─ Proxy Used:         {session.anti_detection.proxy_masked or 'Direct'}
╚══════════════════════════════════════════════════════════════════════════╝""")
        
        # Save to JSON log
        self._save_session_log(session)
    
    def log_session_failed(
        self, 
        session: ScrapeSession, 
        error_type: str,
        error_message: str,
        likely_ban: bool = False,
        screenshot_path: str = ""
    ):
        """Log failed session."""
        session.status = "banned" if likely_ban else "failed"
        session.error_type = error_type
        session.error_message = error_message
        session.likely_ban = likely_ban
        session.screenshot_path = screenshot_path
        session.timing.total_time = time.time() - session.timing.start_time
        
        if likely_ban:
            self.stats["banned"] += 1
        else:
            self.stats["failed"] += 1
        
        self.logger.error(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ❌ SCRAPE FAILED - {session.session_id}
╠══════════════════════════════════════════════════════════════════════════╣
║  🚫 ERROR DETAILS
║  ├─ Type:        {error_type}
║  ├─ Message:     {error_message[:60]}{'...' if len(error_message) > 60 else ''}
║  ├─ Likely Ban:  {'🔴 YES' if likely_ban else '🟢 NO'}
║  └─ Screenshot:  {screenshot_path or 'Not saved'}
╠──────────────────────────────────────────────────────────────────────────╣
{session.anti_detection.to_log_string()}
{session.timing.to_log_string()}
╠──────────────────────────────────────────────────────────────────────────╣
║  📊 SESSION STATS
║  ├─ Attempt:            {session.attempt}/{session.max_attempts}
║  ├─ Strategies Tried:   {', '.join(session.strategies_tried) or 'None'}
║  └─ Proxy Used:         {session.anti_detection.proxy_masked or 'Direct'}
╚══════════════════════════════════════════════════════════════════════════╝""")
        
        # Save to JSON log
        self._save_session_log(session)
    
    def log_overall_stats(self):
        """Log overall scraping statistics."""
        success_rate = (self.stats["successful"] / self.stats["total_scrapes"] * 100) if self.stats["total_scrapes"] > 0 else 0
        
        self.logger.info(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  📊 OVERALL SCRAPING STATISTICS
╠══════════════════════════════════════════════════════════════════════════╣
║  Total Scrapes:    {self.stats['total_scrapes']}
║  Successful:       {self.stats['successful']} ({success_rate:.1f}%)
║  Failed:           {self.stats['failed']}
║  Banned/Blocked:   {self.stats['banned']}
║  Avg Time:         {self.stats['avg_time']:.2f}s
╚══════════════════════════════════════════════════════════════════════════╝""")
    
    def _mask_proxy(self, proxy: Optional[dict]) -> str:
        """Mask proxy credentials for logging."""
        if not proxy:
            return ""
        server = proxy.get("server", "unknown")
        username = proxy.get("username", "")
        if username:
            return f"{server} (user: {username[:3]}***)"
        return server
    
    def _save_session_log(self, session: ScrapeSession):
        """Save session data to JSON file for analysis."""
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"scrape_sessions_{date_str}.json"

            # Load existing sessions or create new list
            sessions = []
            if log_file.exists():
                try:
                    with open(log_file, "r") as f:
                        sessions = json.load(f)
                except (json.JSONDecodeError, Exception):
                    sessions = []

            # Append new session
            sessions.append(session.to_dict())

            # Write back as formatted JSON
            with open(log_file, "w") as f:
                json.dump(sessions, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save session log: {e}")


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_advanced_logger: Optional[AdvancedScrapeLogger] = None

def get_advanced_logger() -> AdvancedScrapeLogger:
    """Get or create the advanced logger instance."""
    global _advanced_logger
    if _advanced_logger is None:
        _advanced_logger = AdvancedScrapeLogger()
    return _advanced_logger
