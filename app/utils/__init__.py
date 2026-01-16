"""
Utility functions.
"""

from app.utils.human_behavior import (
    simulate_human_behavior,
    simulate_mouse_movement,
    simulate_scroll,
    human_delay,
)
from app.utils.proxy_manager import ProxyManager, load_proxies_from_file, mask_proxy
from app.utils.helpers import (
    get_referrer,
    classify_error,
    save_failure_screenshot,
    load_config,
)

__all__ = [
    # Human behavior
    "simulate_human_behavior",
    "simulate_mouse_movement",
    "simulate_scroll",
    "human_delay",
    # Proxy
    "ProxyManager",
    "load_proxies_from_file",
    "mask_proxy",
    # Helpers
    "get_referrer",
    "classify_error",
    "save_failure_screenshot",
    "load_config",
]
