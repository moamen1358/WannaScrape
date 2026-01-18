"""
Detailed Scrape Log
===================
Creates detailed, beautifully formatted log files for individual scrape sessions.
"""

from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse

from .utils import get_egypt_time
from app.config.settings import get_data_dir


class DetailedScrapeLog:
    """
    Creates detailed scrape logs with beautiful formatting.
    One log file per scrape session.
    """

    def __init__(self, url: str, log_dir: str = None):
        if log_dir is None:
            log_dir = f"{get_data_dir()}/logs/scrapes"
        self.url = url
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with Egypt timezone
        domain = urlparse(url).netloc.replace('www.', '')
        egypt_now = get_egypt_time()
        timestamp = egypt_now.strftime("%Y-%m-%d_%H%M%S")
        self.log_file = self.log_dir / f"{timestamp}_{domain}.log"
        self.lines = []
        self.start_time = egypt_now
        self.session_id = None

        # Timing tracking
        self.timings = {
            'browser_launch': 0,
            'page_load': 0,
            'cloudflare': 0,
            'human_behavior': 0,
            'extraction': 0,
        }

    def _ts(self) -> str:
        """Get current timestamp in Egypt timezone."""
        return get_egypt_time().strftime("%H:%M:%S.%f")[:-3]

    def _log(self, level: str, msg: str):
        """Add log line."""
        self.lines.append(f"[{self._ts()}] [{level:5}] {msg}")

    def info(self, msg: str):
        self._log("INFO ", msg)

    def debug(self, msg: str):
        self._log("DEBUG", msg)

    def warning(self, msg: str):
        self._log("WARN ", msg)

    def error(self, msg: str):
        self._log("ERROR", msg)

    def header(self, session_id: str):
        """Write log header."""
        self.session_id = session_id
        self.lines.append("=" * 80)
        self.lines.append(f"SCRAPE LOG: {self.url}")
        self.lines.append(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.lines.append(f"Session ID: {session_id}")
        self.lines.append("=" * 80)

    def log_timeout(self, timeout: int):
        """Log timeout setting."""
        self.info(f"Scrape log: {self.log_file}")
        self.debug(f"Timeout set to {timeout}s for this scrape")

    def log_browser_launch(self, headless: bool, slow_mo: int, launch_time: float):
        """Log browser launch."""
        self.timings['browser_launch'] = launch_time
        mode = "Headless" if headless else "Visible"
        self.info("")
        self.info("    BROWSER LAUNCHED")
        self.info(f"    |- Mode:       {mode}")
        self.info(f"    |- Slow Mo:    {slow_mo}ms")
        self.info(f"    |- Launch Time: {launch_time:.2f}s")
        self.info("    |- Args:       Anti-automation flags enabled")

    def log_browser_profile(self, viewport: Dict, locale: str, timezone: str):
        """Log browser profile."""
        self.debug(f"Browser profile: viewport={viewport}, locale={locale}, tz={timezone}")

    def log_session_start(self, attempt: int, max_attempts: int, fingerprint: Dict[str, Any]):
        """Log session start with fingerprint details."""
        self.info("")
        self.info("=" * 76)
        self.info(f"  SESSION: {self.session_id}")
        self.info(f"  URL: {self.url}")
        self.info(f"  ATTEMPT: {attempt}/{max_attempts}")
        self.info(f"  STARTED: {get_egypt_time().isoformat()} (Egypt Time)")
        self.info("=" * 76)
        self.info("")

        # Browser fingerprint
        self.info("    |- BROWSER FINGERPRINT -|")
        self.info(f"    | Browser:     {fingerprint.get('browser', 'N/A')}")
        ua = fingerprint.get('user_agent', 'N/A')
        self.info(f"    | User-Agent:  {ua[:70]}...")
        vp = fingerprint.get('viewport', {})
        self.info(f"    | Viewport:    {vp.get('width', 0)}x{vp.get('height', 0)}")
        self.info("    | Sec-CH-UA:   (not applicable)...")

        # Location profile
        loc = fingerprint.get('location', {})
        self.info("    |- LOCATION PROFILE -|")
        self.info(f"    | Location:    {loc.get('name', 'N/A')}")
        self.info(f"    | Timezone:    {loc.get('timezone', 'N/A')}")
        self.info(f"    | Locale:      {loc.get('locale', 'N/A')}")
        self.info(f"    | Geo:         {loc.get('latitude', 0)}, {loc.get('longitude', 0)}")

        # Network
        proxy = fingerprint.get('proxy', 'Direct (no proxy)')
        self.info("    |- NETWORK -|")
        self.info(f"    | Proxy:       {proxy}")
        self.info(f"    | Referrer:    {fingerprint.get('referrer', 'https://www.google.com/')}")

    def log_anti_detection(self, level: str = "context"):
        """Log anti-detection injection."""
        self.info(f"Injected anti-detection scripts at {level} level")
        self.debug("   |- Canvas noise, WebGL spoof, Browser patches")
        self.info("")
        self.info(f"    ANTI-DETECTION SCRIPTS INJECTED ({level.upper()} level)")
        self.info("    |- Canvas fingerprint noise")
        self.info("    |- WebGL renderer/vendor spoof")
        self.info("    |- Hardware concurrency randomization")
        self.info("    |- Device memory randomization")
        self.info("    |- Plugin masking")
        self.info("    |- WebRTC IP leak protection")
        self.info("    |- Network connection spoof")
        self.info("    |- Battery API spoof")

    def log_stealth_mode(self):
        """Log stealth mode application."""
        self.info("")
        self.info("    STEALTH MODE APPLIED")
        self.info("    |- Navigator patches (webdriver, plugins, languages)")
        self.info("    |- Chrome runtime patches")
        self.info("    |- Console patches")
        self.info("    |- Permission patches")

    def log_navigation_start(self, strategy: str, timeout: float):
        """Log navigation start."""
        self.debug("Enabled resource blocking (images, media, fonts)")
        self.info("")
        self.info("    NAVIGATING TO URL")
        self.info(f"    |- Strategy:   {strategy}")
        self.info(f"    |- Timeout:    {timeout:.1f}s")
        self.info("    |- Sleep:      1s after load")

    def log_page_loaded(self, final_url: str, title: str, load_time: float):
        """Log successful page load."""
        self.timings['page_load'] = load_time
        self.info("")
        self.info("    PAGE LOADED")
        self.info(f"    |- Final URL:  {final_url}")
        self.info(f"    |- Title:      {title}")
        self.info(f"    |- Load Time:  {load_time:.2f}s")

    def log_cloudflare(self, detected: bool, wait_time: float = 0):
        """Log Cloudflare handling."""
        self.timings['cloudflare'] = wait_time
        if detected:
            self.info(f"Cloudflare detected, waiting {wait_time:.1f}s...")
        else:
            self.debug("No Cloudflare challenge detected")

    def log_human_behavior_start(self):
        """Log human behavior start."""
        self.info("Human behavior simulation...")

    def log_human_behavior(self, mouse_moves: int, scrolls: int, duration: float, viewport: Dict = None):
        """Log human behavior simulation."""
        self.timings['human_behavior'] = duration
        vp_height = viewport.get('height', 1440) if viewport else 1440
        vp_width = viewport.get('width', 2560) if viewport else 2560

        self.info(f"Mouse: {mouse_moves} moves in {vp_width}x{vp_height}")
        self.info(f"Mouse completed: {mouse_moves} moves")
        self.info(f"Scroll: page height, viewport={vp_height}px")
        self.info(f"Scroll completed: {scrolls} scrolls")
        self.info(f"Human behavior completed in {duration:.1f}s")
        self.info("")
        self.info("    HUMAN BEHAVIOR SIMULATED")
        self.info(f"    |- Mouse Movements: {mouse_moves}")
        self.info(f"    |- Scroll Actions:  {scrolls}")
        self.info(f"    |- Time Spent:      {duration:.2f}s")

    def log_content_metrics(self, title: str, final_url: str, html_size: int, text: str, method: str):
        """Log content extraction metrics."""
        text_length = len(text) if text else 0
        word_count = len(text.split()) if text else 0
        has_article = "Yes" if text_length > 100 else "No"

        self.info("")
        self.info("    |- CONTENT METRICS -|")
        self.info(f"    | Title:            {title[:50]}")
        self.info(f"    | Final URL:        {final_url}")
        self.info(f"    | HTML Size:        {html_size:,} bytes")
        self.info(f"    | Text Size:        {text_length:,} chars")
        self.info(f"    | Word Count:       ~{word_count} words")
        self.info(f"    | Extraction:       {method}")
        self.info(f"    | Has Article:      {has_article}")

    def log_captcha(self, captcha_type: str, detected: bool, solved: bool = False):
        """Log CAPTCHA handling."""
        if detected:
            status = "Solved" if solved else "Not solved"
            self.info(f"CAPTCHA detected: {captcha_type} - {status}")
        else:
            self.debug("No CAPTCHA detected")

    def log_error(
        self,
        error_type: str,
        message: str,
        page_url: str = None,
        page_title: str = None,
        html_size: int = None,
        likely_ban: bool = False,
        recommendation: str = None,
        screenshot_path: str = None
    ):
        """Log an error with detailed diagnostic information."""
        self.info("")
        self.info("=" * 76)
        self.info("  ERROR DETECTED")
        self.info("=" * 76)
        self.info("")

        # Error details
        self.info("    |- ERROR DETAILS -|")
        self.info(f"    | Error Type:       {error_type}")
        self.info(f"    | Message:          {message[:60]}...")
        if len(message) > 60:
            remaining = message[60:]
            while remaining:
                chunk = remaining[:56]
                remaining = remaining[56:]
                self.info(f"    |                   {chunk}")
        self.info("    |")
        self.info(f"    | Likely Ban:       {'YES' if likely_ban else 'No'}")
        if recommendation:
            self.info(f"    | Recommendation:   {recommendation[:50]}")

        # Page state at error
        if page_url or page_title or html_size:
            self.info("")
            self.info("    |- PAGE STATE AT ERROR -|")
            if page_url:
                self.info(f"    | Page URL:         {page_url[:55]}")
            if page_title:
                self.info(f"    | Page Title:       {page_title[:55]}")
            if html_size is not None:
                size_indicator = "Suspiciously small" if html_size < 5000 else "Normal"
                self.info(f"    | HTML Size:        {html_size:,} bytes ({size_indicator})")

        # Screenshot info
        if screenshot_path:
            self.info("")
            self.info("    |- DEBUG SCREENSHOT -|")
            self.info(f"    | Saved to: {screenshot_path}")

        self.info("")
        self.error(f"{error_type}: {message}")

    def log_success(self, content: Dict[str, Any], extraction_time: float):
        """Log successful scrape completion."""
        self.timings['extraction'] = extraction_time
        total_time = sum(self.timings.values())

        self.info("")
        self.info("=" * 76)
        self.info(f"  SCRAPE SUCCESSFUL - {self.session_id}")
        self.info("=" * 76)
        self.info("")

        # Timing breakdown
        self.info("    |- TIMING BREAKDOWN -|")
        self.info(f"    | Browser Launch:      {self.timings['browser_launch']:.2f}s")
        self.info(f"    | Page Load:           {self.timings['page_load']:.2f}s")
        self.info(f"    | Cloudflare Wait:     {self.timings['cloudflare']:.2f}s")
        self.info(f"    | Human Simulation:    {self.timings['human_behavior']:.2f}s")
        self.info("    |")
        self.info(f"    | Content Extraction:  {self.timings['extraction']:.2f}s")
        self.info("    | ---------------------------------------------------------")
        self.info(f"    | TOTAL TIME:          {total_time:.2f}s")
        self.info("")

        # Content metrics
        title = content.get('title', 'N/A')[:50]
        final_url = content.get('final_url', self.url)
        html_size = content.get('html_size', 0)
        text = content.get('text', '')
        text_length = len(text)
        word_count = len(text.split()) if text else 0
        has_article = "Yes" if text_length > 100 else "No"
        method = content.get('extraction_method', 'trafilatura')

        self.info("    |- CONTENT METRICS -|")
        self.info(f"    | Title:            {title}")
        self.info(f"    | Final URL:        {final_url}")
        self.info(f"    | HTML Size:        {html_size:,} bytes")
        self.info(f"    | Text Size:        {text_length:,} chars")
        self.info(f"    | Word Count:       ~{word_count} words")
        self.info(f"    | Extraction:       {method}")
        self.info(f"    | Has Article:      {has_article}")

        self.info("=" * 76)
        self.info("  SESSION STATS")
        self.info("  |- Strategies Tried:   domcontentloaded")
        self.info("  |- Popups Dismissed:   0")
        self.info("  |- Cloudflare:         " + ("Detected" if self.timings['cloudflare'] > 0 else "Not detected"))
        self.info("  |- Proxy Used:         Direct")
        self.info("")

    def log_failure(
        self,
        error_type: str,
        message: str,
        likely_ban: bool = False,
        recommendation: str = None,
        screenshot_path: str = None,
        retries_attempted: int = 0
    ):
        """Log failed scrape with comprehensive details."""
        total_time = sum(self.timings.values())

        self.info("")
        self.info("=" * 76)
        self.info(f"  SCRAPE FAILED - {self.session_id}")
        self.info("=" * 76)
        self.info("")

        # Error summary
        self.info("    |- FAILURE SUMMARY -|")
        self.info(f"    | URL:              {self.url[:55]}")
        self.info(f"    | Error Type:       {error_type}")
        self.info(f"    | Likely Ban:       {'YES' if likely_ban else 'No'}")
        self.info(f"    | Retries Used:     {retries_attempted}")
        self.info("    |")
        self.info("    | Error Message:")
        msg_lines = [message[i:i+56] for i in range(0, len(message), 56)]
        for line in msg_lines[:5]:
            self.info(f"    |   {line}")
        if len(msg_lines) > 5:
            self.info("    |   ... (truncated)")

        # Timing at failure
        self.info("")
        self.info("    |- TIMING AT FAILURE -|")
        self.info(f"    | Browser Launch:     {self.timings.get('browser_launch', 0):.2f}s")
        self.info(f"    | Page Load:          {self.timings.get('page_load', 0):.2f}s")
        self.info(f"    | Cloudflare Wait:    {self.timings.get('cloudflare', 0):.2f}s")
        self.info(f"    | Human Simulation:   {self.timings.get('human_behavior', 0):.2f}s")
        self.info("    | ---------------------------------------------------------")
        self.info(f"    | FAILED AT:          {total_time:.2f}s")

        # Recommendation
        if recommendation:
            self.info("")
            self.info("    |- RECOMMENDATION -|")
            rec_lines = [recommendation[i:i+56] for i in range(0, len(recommendation), 56)]
            for line in rec_lines[:3]:
                self.info(f"    | {line}")

        # Screenshot
        if screenshot_path:
            self.info("")
            self.info("    |- DEBUG SCREENSHOT -|")
            self.info(f"    | {screenshot_path}")

        self.info("")

    def footer(self, status: str, total_time: float = None):
        """Write log footer."""
        if total_time is None:
            total_time = (get_egypt_time() - self.start_time).total_seconds()
        self.lines.append("")
        self.lines.append("=" * 80)
        self.lines.append(f"STATUS: {status}")
        self.lines.append(f"TOTAL TIME: {total_time:.2f}s")
        self.lines.append(f"ENDED: {get_egypt_time().isoformat()} (Egypt Time)")
        self.lines.append("END OF SCRAPE LOG")
        self.lines.append("=" * 80)

    def save(self) -> str:
        """Save log to file and return path."""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.lines))
        return str(self.log_file)


__all__ = ['DetailedScrapeLog']
