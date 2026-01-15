"""
Unified logging system for the web scraper.
Provides structured JSON logging with correlation IDs and scrape session tracking.
"""

import os
import json
import uuid
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextvars import ContextVar

# Context variable for correlation ID
_correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')


def get_correlation_id() -> str:
    """Get the current correlation ID."""
    return _correlation_id.get() or str(uuid.uuid4())[:8]


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set and return a correlation ID."""
    cid = correlation_id or str(uuid.uuid4())[:8]
    _correlation_id.set(cid)
    return cid


class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        if hasattr(record, 'extra_data'):
            log_obj.update(record.extra_data)

        return json.dumps(log_obj)


class ConsoleFormatter(logging.Formatter):
    """Pretty console formatter with colors."""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cid = get_correlation_id()

        return f"{timestamp} {color}[{record.levelname:8}]{self.RESET} [{cid}] {record.getMessage()}"


class ScrapeSession:
    """Tracks a single scrape session with detailed logging."""

    def __init__(self, url: str, session_id: str):
        self.url = url
        self.session_id = session_id
        self.start_time = datetime.now()
        self.events: list = []
        self.status = "in_progress"
        self.logger = logging.getLogger("scraper.session")

    def log_event(self, event_type: str, data: Dict[str, Any] = None):
        """Log an event in this session."""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self.events.append(event)
        self.logger.debug(f"[{self.session_id}] {event_type}: {data}")

    def complete(self, status: str = "success", result: Dict[str, Any] = None):
        """Mark session as complete."""
        self.status = status
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        self.log_event("session_complete", {
            "status": status,
            "duration_seconds": duration,
            "result": result
        })

        return {
            "session_id": self.session_id,
            "url": self.url,
            "status": status,
            "duration_seconds": duration,
            "events_count": len(self.events)
        }


class ScrapeLogger:
    """
    Unified scrape logging with session tracking and statistics.
    """

    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, ScrapeSession] = {}
        self.stats = {
            "total_scrapes": 0,
            "successful": 0,
            "failed": 0,
            "captcha_blocked": 0,
            "timeout": 0,
        }
        self.logger = logging.getLogger("scraper")

    def start_session(self, url: str, attempt: int = 1, max_attempts: int = 3) -> str:
        """Start a new scrape session."""
        session_id = f"{datetime.now().strftime('%H%M%S')}_{str(uuid.uuid4())[:6]}"
        set_correlation_id(session_id)

        session = ScrapeSession(url, session_id)
        session.log_event("session_start", {
            "url": url,
            "attempt": attempt,
            "max_attempts": max_attempts
        })

        self.sessions[session_id] = session
        self.stats["total_scrapes"] += 1

        self.logger.info(f"Starting scrape: {url} (attempt {attempt}/{max_attempts})")
        return session_id

    def log_browser_config(self, session_id: str, profile: Dict[str, Any]):
        """Log browser configuration for a session."""
        if session_id in self.sessions:
            self.sessions[session_id].log_event("browser_config", profile)

    def log_navigation(self, session_id: str, final_url: str, title: str):
        """Log successful page navigation."""
        if session_id in self.sessions:
            self.sessions[session_id].log_event("navigation", {
                "final_url": final_url,
                "title": title
            })

    def log_cloudflare(self, session_id: str, detected: bool, wait_time: float = 0):
        """Log Cloudflare detection."""
        if session_id in self.sessions:
            self.sessions[session_id].log_event("cloudflare", {
                "detected": detected,
                "wait_time": wait_time
            })

    def log_captcha(self, session_id: str, captcha_type: str, solved: bool):
        """Log CAPTCHA detection and solving."""
        if session_id in self.sessions:
            self.sessions[session_id].log_event("captcha", {
                "type": captcha_type,
                "solved": solved
            })
            if not solved:
                self.stats["captcha_blocked"] += 1

    def log_content_extracted(self, session_id: str, method: str, text_length: int):
        """Log successful content extraction."""
        if session_id in self.sessions:
            self.sessions[session_id].log_event("content_extracted", {
                "method": method,
                "text_length": text_length
            })

    def log_error(self, session_id: str, error_type: str, message: str, likely_ban: bool = False):
        """Log an error during scraping."""
        if session_id in self.sessions:
            self.sessions[session_id].log_event("error", {
                "type": error_type,
                "message": message,
                "likely_ban": likely_ban
            })

    def complete_session(self, session_id: str, success: bool, result: Dict[str, Any] = None):
        """Complete a scrape session."""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        status = "success" if success else "failed"

        if success:
            self.stats["successful"] += 1
        else:
            self.stats["failed"] += 1
            error_type = result.get("error_type", "unknown") if result else "unknown"
            if error_type == "timeout":
                self.stats["timeout"] += 1

        summary = session.complete(status, result)
        self.logger.info(f"Scrape {status}: {session.url} ({summary['duration_seconds']:.1f}s)")

        return summary

    def get_stats(self) -> Dict[str, Any]:
        """Get current scraping statistics."""
        success_rate = 0
        if self.stats["total_scrapes"] > 0:
            success_rate = (self.stats["successful"] / self.stats["total_scrapes"]) * 100

        return {
            **self.stats,
            "success_rate": f"{success_rate:.1f}%",
            "active_sessions": len([s for s in self.sessions.values() if s.status == "in_progress"])
        }


def setup_logging(
    level: str = "INFO",
    log_dir: str = "data/logs",
    json_format: bool = False
) -> logging.Logger:
    """
    Setup the logging configuration for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        json_format: Use JSON format for file logs

    Returns:
        The root scraper logger
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Root logger for scraper
    root_logger = logging.getLogger("scraper")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with pretty formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ConsoleFormatter())
    root_logger.addHandler(console_handler)

    # File handler with JSON or standard formatting
    log_file = log_path / f"scraper_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)

    if json_format:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        ))

    root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    for noisy_logger in ["httpx", "httpcore", "urllib3", "playwright"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    return root_logger


# Global logger instance
_scrape_logger: Optional[ScrapeLogger] = None


def get_scrape_logger() -> ScrapeLogger:
    """Get the global scrape logger instance."""
    global _scrape_logger
    if _scrape_logger is None:
        _scrape_logger = ScrapeLogger()
    return _scrape_logger
