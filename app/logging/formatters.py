"""
Log Formatters
==============
Custom log formatters for console and JSON output.
"""

import json
import logging

from .utils import get_egypt_time, get_correlation_id


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
        timestamp = get_egypt_time().strftime("%Y-%m-%d %H:%M:%S")
        cid = get_correlation_id()
        return f"{timestamp} {color}[{record.levelname:8}]{self.RESET} [{cid}] {record.getMessage()}"


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for production logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": get_egypt_time().isoformat(),
            "level": record.levelname,
            "correlation_id": get_correlation_id(),
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry, ensure_ascii=False)


__all__ = ['ConsoleFormatter', 'JSONFormatter']
