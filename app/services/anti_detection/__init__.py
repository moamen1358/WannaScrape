"""
Anti-Detection Module
=====================
Advanced anti-detection techniques to make the scraper appear as a real browser.

Provides JavaScript injection scripts for:
1. Audio fingerprint spoofing
2. Font enumeration spoofing
3. Speech synthesis spoofing
4. Permissions API spoofing
5. ClientRects noise injection
6. Date/Time precision reduction
7. Performance API noise
8. Media devices spoofing
9. Document visibility spoofing

Usage:
    from app.services.anti_detection import inject_advanced_anti_detection

    # Inject at context level (applies to all pages)
    inject_advanced_anti_detection(context, is_context=True)

    # Or inject at page level
    inject_advanced_anti_detection(page)
"""

import logging
from .scripts import ADVANCED_ANTI_DETECTION_SCRIPT

logger = logging.getLogger("scraper.anti_detection")


def inject_advanced_anti_detection(context_or_page, is_context: bool = False) -> bool:
    """
    Inject advanced anti-detection scripts.

    Args:
        context_or_page: Either a BrowserContext or Page object
        is_context: If True, inject at context level (applies to all pages)

    Returns:
        True if injection succeeded, False otherwise
    """
    try:
        target = context_or_page
        target_type = "context" if is_context else "page"

        target.add_init_script(ADVANCED_ANTI_DETECTION_SCRIPT)

        logger.info(f"Advanced anti-detection scripts injected at {target_type} level")
        logger.debug("   Audio, Font, Speech, ClientRects, DateTime, Permissions, Performance, MediaDevices, Visibility")

        return True
    except Exception as e:
        logger.warning(f"Failed to inject advanced anti-detection scripts: {e}")
        return False


# Re-export scripts for direct access
from .scripts import (
    AUDIO_FINGERPRINT_SCRIPT,
    FONT_FINGERPRINT_SCRIPT,
    SPEECH_SYNTHESIS_SCRIPT,
    CLIENTRECTS_NOISE_SCRIPT,
    DATE_TIME_SCRIPT,
    PERMISSIONS_SCRIPT,
    PERFORMANCE_API_SCRIPT,
    MEDIA_DEVICES_SCRIPT,
    VISIBILITY_SCRIPT,
    ADVANCED_ANTI_DETECTION_SCRIPT,
)

__all__ = [
    'inject_advanced_anti_detection',
    'AUDIO_FINGERPRINT_SCRIPT',
    'FONT_FINGERPRINT_SCRIPT',
    'SPEECH_SYNTHESIS_SCRIPT',
    'CLIENTRECTS_NOISE_SCRIPT',
    'DATE_TIME_SCRIPT',
    'PERMISSIONS_SCRIPT',
    'PERFORMANCE_API_SCRIPT',
    'MEDIA_DEVICES_SCRIPT',
    'VISIBILITY_SCRIPT',
    'ADVANCED_ANTI_DETECTION_SCRIPT',
]
