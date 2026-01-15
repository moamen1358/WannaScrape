"""
Proxy management with health tracking and rotation.
"""

import time
import random
import logging
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger("scraper.proxy")


class ProxyManager:
    """Manages proxy rotation with health tracking."""

    def __init__(self, proxies: List[dict]):
        self.proxies = proxies
        self.failed_counts: Dict[str, int] = {}
        self.last_used: Dict[str, float] = {}
        self.cooldown_until: Dict[str, float] = {}

    def get_proxy(self) -> Optional[dict]:
        """Get a healthy proxy that hasn't been used recently."""
        if not self.proxies:
            return None

        now = time.time()
        min_interval = 30

        available = [
            p for p in self.proxies
            if self.failed_counts.get(p['server'], 0) < 3
            and now - self.last_used.get(p['server'], 0) > min_interval
            and now > self.cooldown_until.get(p['server'], 0)
        ]

        if not available:
            logger.warning("All proxies exhausted, resetting...")
            self.failed_counts = {}
            self.cooldown_until = {}
            available = self.proxies

        proxy = random.choice(available)
        self.last_used[proxy['server']] = now
        return proxy

    def mark_failed(self, proxy: dict, cooldown_seconds: int = 120):
        """Mark a proxy as failed and put it on cooldown."""
        if not proxy:
            return

        server = proxy['server']
        self.failed_counts[server] = self.failed_counts.get(server, 0) + 1
        self.cooldown_until[server] = time.time() + cooldown_seconds

        logger.warning(f"Proxy {server} marked failed (count: {self.failed_counts[server]})")

    def mark_success(self, proxy: dict):
        """Mark a proxy as successful, reset its failure count."""
        if not proxy:
            return

        server = proxy['server']
        self.failed_counts[server] = 0
        if server in self.cooldown_until:
            del self.cooldown_until[server]


def load_proxies_from_file(proxy_file: str) -> List[dict]:
    """
    Load proxies from a text file.
    Expected format: host:port:username:password (one per line)
    """
    proxies = []
    proxy_path = Path(proxy_file)

    if not proxy_path.exists():
        logger.warning(f"Proxy file not found: {proxy_file}")
        return []

    try:
        with open(proxy_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(':')
                if len(parts) >= 2:
                    host = parts[0]
                    port = parts[1]

                    proxy = {
                        "server": f"http://{host}:{port}"
                    }

                    if len(parts) >= 4:
                        proxy["username"] = parts[2]
                        proxy["password"] = parts[3]

                    proxies.append(proxy)

        logger.info(f"Loaded {len(proxies)} proxies from {proxy_file}")
    except Exception as e:
        logger.error(f"Error loading proxies: {e}")

    return proxies


def mask_proxy(proxy: dict) -> str:
    """Mask proxy credentials for safe logging."""
    if not proxy:
        return "None"
    server = proxy.get("server", "unknown")
    username = proxy.get("username", "")
    if username:
        return f"{server} (user: {username[:3]}***)"
    return server
