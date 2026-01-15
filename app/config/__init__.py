"""
Configuration module.
"""

from app.config.settings import Settings, get_settings, reload_settings
from app.config.constants import (
    COMMON_VIEWPORTS,
    CAPTCHA_PHRASES,
    ACCESS_DENIED_INDICATORS,
    POPUP_SELECTORS,
    CANVAS_NOISE_SCRIPT,
    WEBGL_SPOOF_SCRIPT,
    BROWSER_PATCHES_SCRIPT,
    DEFAULT_CONFIG,
)

__all__ = [
    "Settings",
    "get_settings",
    "reload_settings",
    "COMMON_VIEWPORTS",
    "CAPTCHA_PHRASES",
    "ACCESS_DENIED_INDICATORS",
    "POPUP_SELECTORS",
    "CANVAS_NOISE_SCRIPT",
    "WEBGL_SPOOF_SCRIPT",
    "BROWSER_PATCHES_SCRIPT",
    "DEFAULT_CONFIG",
]
