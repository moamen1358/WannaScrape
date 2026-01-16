"""
Logging Utilities
=================
Utility functions for logging: timezone handling and correlation IDs.
"""

import uuid
from datetime import datetime
from typing import Optional
from contextvars import ContextVar
from zoneinfo import ZoneInfo

# Egypt timezone
EGYPT_TZ = ZoneInfo("Africa/Cairo")

# Context variable for correlation ID
_correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')


def get_egypt_time() -> datetime:
    """Get current time in Egypt timezone."""
    return datetime.now(EGYPT_TZ)


def get_correlation_id() -> str:
    """Get the current correlation ID."""
    return _correlation_id.get() or str(uuid.uuid4())[:8]


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set and return a correlation ID."""
    cid = correlation_id or str(uuid.uuid4())[:8]
    _correlation_id.set(cid)
    return cid


__all__ = [
    'EGYPT_TZ',
    'get_egypt_time',
    'get_correlation_id',
    'set_correlation_id',
]
