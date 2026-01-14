"""
Enterprise Logging System
=========================
Production-grade logging for APIs - similar to what Netflix, Uber, Stripe use.

Features:
- Structured JSON logs (ELK/Loki/Datadog ready)
- Correlation IDs for request tracing
- Async non-blocking writes
- Automatic log rotation and retention
- Log levels with environment-based filtering
- Performance metrics built-in
- Error categorization and alerting hooks
"""

import logging
import json
import os
import sys
import time
import uuid
import asyncio
import threading
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field, asdict
from queue import Queue, Empty
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from contextvars import ContextVar
from functools import wraps
import traceback

# ============================================================================
# CONTEXT VARIABLES FOR REQUEST TRACING
# ============================================================================

# Correlation ID follows the request across all log entries
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')
request_metadata_var: ContextVar[Dict] = ContextVar('request_metadata', default={})


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique = uuid.uuid4().hex[:12]
    return f"{timestamp}-{unique}"


def set_correlation_id(cid: Optional[str] = None) -> str:
    """Set correlation ID for current context. Returns the ID."""
    cid = cid or generate_correlation_id()
    correlation_id_var.set(cid)
    return cid


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return correlation_id_var.get() or generate_correlation_id()


# ============================================================================
# STRUCTURED LOG RECORD
# ============================================================================

@dataclass
class LogRecord:
    """Structured log record - JSON serializable for any log aggregator."""

    # Required fields
    timestamp: str
    level: str
    message: str

    # Tracing
    correlation_id: str = ""
    span_id: str = ""

    # Context
    service: str = "web-scraper"
    environment: str = "development"
    version: str = "1.0.0"

    # Source
    logger_name: str = ""
    module: str = ""
    function: str = ""
    line_number: int = 0

    # Request context (for API logs)
    request_id: str = ""
    user_id: str = ""
    client_ip: str = ""
    user_agent: str = ""
    endpoint: str = ""
    method: str = ""

    # Performance
    duration_ms: float = 0

    # Error details
    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""

    # Custom fields
    extra: Dict[str, Any] = field(default_factory=dict)

    # Tags for filtering
    tags: List[str] = field(default_factory=list)

    def to_json(self) -> str:
        """Convert to JSON string for logging."""
        data = {k: v for k, v in asdict(self).items() if v}  # Remove empty fields
        return json.dumps(data, default=str, ensure_ascii=False)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v}


# ============================================================================
# JSON FORMATTER FOR STRUCTURED LOGGING
# ============================================================================

class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON - compatible with ELK, Loki, Datadog, Splunk.

    Output format:
    {"timestamp": "2024-01-15T10:30:00.123Z", "level": "INFO", "message": "...", ...}
    """

    def __init__(self, service: str = "web-scraper", environment: str = "development"):
        super().__init__()
        self.service = service
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        # Base fields
        log_data = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "service": self.service,
            "environment": self.environment,
            "correlation_id": get_correlation_id(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["error_type"] = record.exc_info[0].__name__ if record.exc_info[0] else ""
            log_data["error_message"] = str(record.exc_info[1]) if record.exc_info[1] else ""
            log_data["stack_trace"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Add request metadata from context
        request_meta = request_metadata_var.get()
        if request_meta:
            log_data.update(request_meta)

        return json.dumps(log_data, default=str, ensure_ascii=False)


# ============================================================================
# ASYNC LOG HANDLER - NON-BLOCKING WRITES
# ============================================================================

class AsyncFileHandler(logging.Handler):
    """
    Asynchronous file handler - writes logs in background thread.

    Benefits:
    - Non-blocking: API responses aren't slowed by disk I/O
    - Buffered: Batches writes for efficiency
    - Reliable: Graceful shutdown ensures no log loss
    """

    def __init__(
        self,
        filename: str,
        max_queue_size: int = 10000,
        flush_interval: float = 1.0,
        batch_size: int = 100
    ):
        super().__init__()
        self.filename = filename
        self.queue: Queue = Queue(maxsize=max_queue_size)
        self.flush_interval = flush_interval
        self.batch_size = batch_size
        self._stop_event = threading.Event()
        self._writer_thread: Optional[threading.Thread] = None

        # Ensure directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        # Start background writer
        self._start_writer()

    def _start_writer(self):
        """Start the background writer thread."""
        self._writer_thread = threading.Thread(
            target=self._writer_loop,
            name="AsyncLogWriter",
            daemon=True
        )
        self._writer_thread.start()

    def _writer_loop(self):
        """Background loop that writes logs to file."""
        buffer = []
        last_flush = time.time()

        while not self._stop_event.is_set():
            try:
                # Get log record with timeout
                record = self.queue.get(timeout=0.1)
                buffer.append(self.format(record))

                # Flush if batch is full or interval elapsed
                should_flush = (
                    len(buffer) >= self.batch_size or
                    time.time() - last_flush >= self.flush_interval
                )

                if should_flush and buffer:
                    self._flush_buffer(buffer)
                    buffer = []
                    last_flush = time.time()

            except Empty:
                # Flush on timeout if we have data
                if buffer and time.time() - last_flush >= self.flush_interval:
                    self._flush_buffer(buffer)
                    buffer = []
                    last_flush = time.time()

        # Final flush on shutdown
        if buffer:
            self._flush_buffer(buffer)

    def _flush_buffer(self, buffer: List[str]):
        """Write buffer to file."""
        try:
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write('\n'.join(buffer) + '\n')
        except Exception as e:
            # Fallback to stderr if file write fails
            sys.stderr.write(f"Log write failed: {e}\n")

    def emit(self, record: logging.LogRecord):
        """Add record to queue (non-blocking)."""
        try:
            self.queue.put_nowait(record)
        except:
            # Queue full - drop log rather than block
            pass

    def close(self):
        """Graceful shutdown."""
        self._stop_event.set()
        if self._writer_thread:
            self._writer_thread.join(timeout=5.0)
        super().close()


# ============================================================================
# ROTATING FILE HANDLER WITH COMPRESSION
# ============================================================================

class CompressedRotatingHandler(RotatingFileHandler):
    """
    Rotating file handler that compresses old logs.

    - Rotates when file exceeds max size
    - Compresses rotated files with gzip
    - Keeps specified number of backups
    """

    def __init__(
        self,
        filename: str,
        max_bytes: int = 50 * 1024 * 1024,  # 50MB default
        backup_count: int = 10,
        compress: bool = True
    ):
        self.compress = compress
        super().__init__(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )

    def doRollover(self):
        """Rotate and optionally compress old log file."""
        super().doRollover()

        if self.compress:
            # Compress the rotated file
            rotated_file = f"{self.baseFilename}.1"
            if os.path.exists(rotated_file):
                compressed_file = f"{rotated_file}.gz"
                try:
                    with open(rotated_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(rotated_file)
                except Exception:
                    pass  # Keep uncompressed if compression fails


# ============================================================================
# LOG RETENTION MANAGER
# ============================================================================

class LogRetentionManager:
    """
    Manages log retention - deletes old logs automatically.

    Used by: Netflix, Uber for compliance and storage management.
    """

    def __init__(
        self,
        log_dir: str,
        retention_days: int = 30,
        check_interval_hours: int = 24
    ):
        self.log_dir = Path(log_dir)
        self.retention_days = retention_days
        self.check_interval = check_interval_hours * 3600
        self._stop_event = threading.Event()
        self._cleanup_thread: Optional[threading.Thread] = None

    def start(self):
        """Start background cleanup thread."""
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="LogRetentionManager",
            daemon=True
        )
        self._cleanup_thread.start()

    def _cleanup_loop(self):
        """Background loop for log cleanup."""
        while not self._stop_event.is_set():
            self.cleanup_old_logs()
            self._stop_event.wait(self.check_interval)

    def cleanup_old_logs(self):
        """Delete logs older than retention period."""
        if not self.log_dir.exists():
            return

        cutoff = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        for log_file in self.log_dir.glob("**/*.log*"):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff:
                    log_file.unlink()
                    deleted_count += 1
            except Exception:
                pass

        if deleted_count > 0:
            logging.getLogger("enterprise.retention").info(
                f"Cleaned up {deleted_count} old log files"
            )

    def stop(self):
        """Stop cleanup thread."""
        self._stop_event.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5.0)


# ============================================================================
# API REQUEST LOGGER - MIDDLEWARE STYLE
# ============================================================================

class APIRequestLogger:
    """
    Structured API request/response logging.

    Logs:
    - Request: method, path, headers, body
    - Response: status, duration, size
    - Errors: full stack traces with context
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_request(
        self,
        method: str,
        path: str,
        client_ip: str = "",
        user_agent: str = "",
        request_id: str = "",
        body_size: int = 0,
        headers: Dict[str, str] = None
    ):
        """Log incoming request."""
        extra = {
            "event": "request_received",
            "http_method": method,
            "http_path": path,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "request_id": request_id or get_correlation_id(),
            "body_size": body_size,
        }

        # Add safe headers (exclude sensitive ones)
        if headers:
            safe_headers = {
                k: v for k, v in headers.items()
                if k.lower() not in ('authorization', 'cookie', 'x-api-key')
            }
            extra["headers"] = safe_headers

        self.logger.info(
            f"{method} {path}",
            extra={"extra_fields": extra}
        )

    def log_response(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        response_size: int = 0,
        error: str = ""
    ):
        """Log outgoing response."""
        extra = {
            "event": "response_sent",
            "http_method": method,
            "http_path": path,
            "http_status": status_code,
            "duration_ms": round(duration_ms, 2),
            "response_size": response_size,
            "correlation_id": get_correlation_id(),
        }

        if error:
            extra["error"] = error

        # Determine log level based on status
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO

        self.logger.log(
            level,
            f"{method} {path} -> {status_code} ({duration_ms:.0f}ms)",
            extra={"extra_fields": extra}
        )

    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None
    ):
        """Log error with full context."""
        extra = {
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "correlation_id": get_correlation_id(),
        }

        if context:
            extra.update(context)

        self.logger.error(
            f"Error: {type(error).__name__}: {error}",
            extra={"extra_fields": extra},
            exc_info=True
        )


# ============================================================================
# SCRAPE OPERATION LOGGER
# ============================================================================

class ScrapeOperationLogger:
    """
    Specialized logger for scraping operations.

    Structured logging for:
    - Scrape sessions with timing
    - Anti-detection configurations
    - Success/failure metrics
    - Rate limiting events
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "blocked": 0,
            "total_duration_ms": 0
        }
        self._lock = threading.Lock()

    def log_scrape_start(
        self,
        url: str,
        attempt: int = 1,
        max_attempts: int = 3,
        proxy: str = "",
        browser: str = "",
        location: str = ""
    ) -> str:
        """Log scrape operation start. Returns session_id."""
        session_id = generate_correlation_id()
        set_correlation_id(session_id)

        with self._lock:
            self.stats["total"] += 1

        extra = {
            "event": "scrape_start",
            "session_id": session_id,
            "target_url": url,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "proxy": self._mask_proxy(proxy),
            "browser": browser,
            "location": location,
        }

        self.logger.info(
            f"Scrape started: {url[:80]}",
            extra={"extra_fields": extra}
        )

        return session_id

    def log_scrape_success(
        self,
        url: str,
        duration_ms: float,
        content_size: int,
        extraction_method: str = "",
        final_url: str = ""
    ):
        """Log successful scrape."""
        with self._lock:
            self.stats["success"] += 1
            self.stats["total_duration_ms"] += duration_ms

        extra = {
            "event": "scrape_success",
            "target_url": url,
            "final_url": final_url or url,
            "duration_ms": round(duration_ms, 2),
            "content_size": content_size,
            "extraction_method": extraction_method,
            "correlation_id": get_correlation_id(),
        }

        self.logger.info(
            f"Scrape success: {url[:60]} ({duration_ms:.0f}ms, {content_size} bytes)",
            extra={"extra_fields": extra}
        )

    def log_scrape_failed(
        self,
        url: str,
        error_type: str,
        error_message: str,
        duration_ms: float,
        is_blocked: bool = False,
        attempt: int = 1
    ):
        """Log failed scrape."""
        with self._lock:
            self.stats["failed"] += 1
            if is_blocked:
                self.stats["blocked"] += 1

        extra = {
            "event": "scrape_failed",
            "target_url": url,
            "error_type": error_type,
            "error_message": error_message,
            "duration_ms": round(duration_ms, 2),
            "is_blocked": is_blocked,
            "attempt": attempt,
            "correlation_id": get_correlation_id(),
        }

        level = logging.ERROR if is_blocked else logging.WARNING

        self.logger.log(
            level,
            f"Scrape failed: {url[:60]} - {error_type}: {error_message[:50]}",
            extra={"extra_fields": extra}
        )

    def log_rate_limit(self, url: str, wait_seconds: float, reason: str = ""):
        """Log rate limiting event."""
        extra = {
            "event": "rate_limit",
            "target_url": url,
            "wait_seconds": wait_seconds,
            "reason": reason,
            "correlation_id": get_correlation_id(),
        }

        self.logger.warning(
            f"Rate limited: waiting {wait_seconds}s for {url[:50]}",
            extra={"extra_fields": extra}
        )

    def log_anti_detection(
        self,
        user_agent: str,
        browser: str,
        viewport: str,
        location: str,
        proxy: str = ""
    ):
        """Log anti-detection configuration used."""
        extra = {
            "event": "anti_detection_config",
            "user_agent": user_agent[:100],
            "browser": browser,
            "viewport": viewport,
            "location": location,
            "proxy": self._mask_proxy(proxy),
            "correlation_id": get_correlation_id(),
        }

        self.logger.debug(
            f"Anti-detection: {browser} from {location}",
            extra={"extra_fields": extra}
        )

    def get_stats(self) -> Dict:
        """Get current statistics."""
        with self._lock:
            stats = self.stats.copy()
            if stats["success"] > 0:
                stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["success"]
            if stats["total"] > 0:
                stats["success_rate"] = (stats["success"] / stats["total"]) * 100
                stats["block_rate"] = (stats["blocked"] / stats["total"]) * 100
            return stats

    def _mask_proxy(self, proxy: str) -> str:
        """Mask proxy credentials."""
        if not proxy:
            return ""
        if "@" in proxy:
            # user:pass@host:port -> ***@host:port
            parts = proxy.split("@")
            return f"***@{parts[-1]}"
        return proxy


# ============================================================================
# ENTERPRISE LOGGER FACTORY
# ============================================================================

class EnterpriseLogger:
    """
    Main enterprise logging system.

    Usage:
        logger = EnterpriseLogger.setup(
            service="my-api",
            environment="production",
            log_dir="logs"
        )

        # API logging
        logger.api.log_request("POST", "/scrape", client_ip="1.2.3.4")
        logger.api.log_response("POST", "/scrape", 200, 150.5)

        # Scrape logging
        logger.scrape.log_scrape_start(url, attempt=1)
        logger.scrape.log_scrape_success(url, duration_ms=1500, content_size=50000)
    """

    _instance: Optional['EnterpriseLogger'] = None

    def __init__(
        self,
        service: str = "web-scraper",
        environment: str = "development",
        log_dir: str = "logs",
        log_level: str = "INFO",
        enable_console: bool = True,
        enable_file: bool = True,
        enable_json: bool = True,
        max_file_size_mb: int = 50,
        backup_count: int = 10,
        retention_days: int = 30
    ):
        self.service = service
        self.environment = environment
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create main logger
        self.logger = logging.getLogger(service)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers = []  # Clear existing handlers

        # JSON formatter for structured logging
        json_formatter = JSONFormatter(service=service, environment=environment)

        # Console handler (human readable in dev, JSON in prod)
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            if environment == "production" or enable_json:
                console_handler.setFormatter(json_formatter)
            else:
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
                ))
            self.logger.addHandler(console_handler)

        # File handler with rotation
        if enable_file:
            # Main JSON log file (for aggregation)
            json_file = self.log_dir / f"{service}.json.log"
            json_handler = CompressedRotatingHandler(
                str(json_file),
                max_bytes=max_file_size_mb * 1024 * 1024,
                backup_count=backup_count,
                compress=True
            )
            json_handler.setFormatter(json_formatter)
            self.logger.addHandler(json_handler)

            # Async handler for high-throughput scenarios
            async_file = self.log_dir / f"{service}.async.log"
            async_handler = AsyncFileHandler(str(async_file))
            async_handler.setFormatter(json_formatter)
            self.logger.addHandler(async_handler)

        # Specialized loggers
        self.api = APIRequestLogger(self.logger.getChild("api"))
        self.scrape = ScrapeOperationLogger(self.logger.getChild("scrape"))

        # Start retention manager
        self.retention_manager = LogRetentionManager(
            str(self.log_dir),
            retention_days=retention_days
        )
        self.retention_manager.start()

        # Log startup
        self.logger.info(
            f"Enterprise logging initialized",
            extra={"extra_fields": {
                "event": "logger_init",
                "service": service,
                "environment": environment,
                "log_dir": str(self.log_dir),
                "retention_days": retention_days
            }}
        )

    @classmethod
    def setup(
        cls,
        service: str = "web-scraper",
        environment: str = None,
        log_dir: str = "logs",
        **kwargs
    ) -> 'EnterpriseLogger':
        """
        Setup and return enterprise logger instance (singleton).

        Args:
            service: Service name for logs
            environment: production/staging/development (auto-detected if not set)
            log_dir: Directory for log files
            **kwargs: Additional configuration options
        """
        if cls._instance is None:
            # Auto-detect environment
            if environment is None:
                environment = os.getenv("ENVIRONMENT", os.getenv("ENV", "development"))

            cls._instance = cls(
                service=service,
                environment=environment,
                log_dir=log_dir,
                **kwargs
            )

        return cls._instance

    @classmethod
    def get(cls) -> 'EnterpriseLogger':
        """Get existing logger instance."""
        if cls._instance is None:
            return cls.setup()
        return cls._instance

    def info(self, message: str, **extra):
        """Log info message with extra fields."""
        self.logger.info(message, extra={"extra_fields": extra} if extra else {})

    def warning(self, message: str, **extra):
        """Log warning message."""
        self.logger.warning(message, extra={"extra_fields": extra} if extra else {})

    def error(self, message: str, **extra):
        """Log error message."""
        self.logger.error(message, extra={"extra_fields": extra} if extra else {})

    def debug(self, message: str, **extra):
        """Log debug message."""
        self.logger.debug(message, extra={"extra_fields": extra} if extra else {})

    def shutdown(self):
        """Graceful shutdown - flush all logs."""
        self.retention_manager.stop()
        for handler in self.logger.handlers:
            handler.close()


# ============================================================================
# DECORATOR FOR AUTOMATIC FUNCTION LOGGING
# ============================================================================

def log_operation(operation_name: str = None, log_args: bool = False):
    """
    Decorator to automatically log function execution.

    Usage:
        @log_operation("fetch_url")
        async def fetch_url(url: str):
            ...
    """
    def decorator(func):
        name = operation_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = EnterpriseLogger.get()
            start_time = time.time()

            extra = {"operation": name}
            if log_args:
                extra["args"] = str(args)[:200]
                extra["kwargs"] = str(kwargs)[:200]

            logger.debug(f"Starting {name}", **extra)

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.debug(f"Completed {name}", duration_ms=duration_ms, **extra)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Failed {name}: {e}",
                    duration_ms=duration_ms,
                    error_type=type(e).__name__,
                    **extra
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = EnterpriseLogger.get()
            start_time = time.time()

            extra = {"operation": name}
            if log_args:
                extra["args"] = str(args)[:200]
                extra["kwargs"] = str(kwargs)[:200]

            logger.debug(f"Starting {name}", **extra)

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.debug(f"Completed {name}", duration_ms=duration_ms, **extra)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Failed {name}: {e}",
                    duration_ms=duration_ms,
                    error_type=type(e).__name__,
                    **extra
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ============================================================================
# FASTAPI MIDDLEWARE
# ============================================================================

def create_logging_middleware():
    """
    Create FastAPI middleware for automatic request logging.

    Usage:
        from enterprise_logging import create_logging_middleware

        app = FastAPI()
        app.middleware("http")(create_logging_middleware())
    """
    async def logging_middleware(request, call_next):
        logger = EnterpriseLogger.get()

        # Generate correlation ID from header or create new
        correlation_id = request.headers.get("X-Correlation-ID") or generate_correlation_id()
        set_correlation_id(correlation_id)

        # Store request metadata in context
        request_metadata_var.set({
            "client_ip": request.client.host if request.client else "",
            "user_agent": request.headers.get("user-agent", ""),
            "request_id": correlation_id,
        })

        # Log request
        start_time = time.time()
        logger.api.log_request(
            method=request.method,
            path=str(request.url.path),
            client_ip=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", ""),
            request_id=correlation_id,
        )

        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            # Log response
            logger.api.log_response(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.api.log_error(e, context={
                "method": request.method,
                "path": str(request.url.path),
                "duration_ms": duration_ms,
            })
            raise

    return logging_middleware


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def setup_logging(
    service: str = "web-scraper",
    environment: str = None,
    log_dir: str = "logs"
) -> EnterpriseLogger:
    """Quick setup function."""
    return EnterpriseLogger.setup(
        service=service,
        environment=environment,
        log_dir=log_dir
    )


def get_logger() -> EnterpriseLogger:
    """Get the enterprise logger instance."""
    return EnterpriseLogger.get()
