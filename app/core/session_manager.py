"""
Session Manager
===============
Manage browser sessions with cookie persistence.
Makes the scraper look like a returning visitor.
"""

import os
import time
import random
import logging
from urllib.parse import urlparse

logger = logging.getLogger("scraper.session_manager")


class SessionManager:
    """
    Manage browser sessions with cookie persistence.

    Saves and restores browser state (cookies, localStorage) per domain
    to make the scraper appear as a returning visitor.

    Usage:
        manager = SessionManager()

        # Check if session exists
        session_path = manager.get_session(url)
        if session_path:
            context = browser.new_context(storage_state=session_path)

        # After successful scrape
        manager.save_session(context, url)
    """

    def __init__(self, sessions_dir: str = "sessions"):
        """
        Initialize the session manager.

        Args:
            sessions_dir: Directory to store session files
        """
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)

        # Track session usage: {domain: {"path": path, "last_used": timestamp, "success_count": int}}
        self.session_usage: dict = {}

    def _get_session_path(self, domain: str) -> str:
        """
        Get session file path for a domain.

        Args:
            domain: The domain name

        Returns:
            Path to session file
        """
        safe_domain = domain.replace(".", "_").replace(":", "_")
        return os.path.join(self.sessions_dir, f"{safe_domain}.json")

    def get_session(self, url: str) -> str | None:
        """
        Get session storage path for URL's domain if it exists.

        Args:
            url: The URL to get session for

        Returns:
            Path to session file if exists, None otherwise
        """
        domain = urlparse(url).netloc
        path = self._get_session_path(domain)

        if os.path.exists(path):
            logger.info(f"Using saved session for {domain}")
            return path

        return None

    def save_session(self, context, url: str) -> str | None:
        """
        Save browser context state (cookies, localStorage) for domain.

        Args:
            context: Playwright browser context
            url: The URL associated with this session

        Returns:
            Path to saved session file, or None on failure
        """
        try:
            domain = urlparse(url).netloc
            path = self._get_session_path(domain)

            context.storage_state(path=path)

            self.session_usage[domain] = {
                "path": path,
                "last_used": time.time(),
                "success_count": self.session_usage.get(domain, {}).get("success_count", 0) + 1
            }

            logger.info(f"Saved session for {domain}")
            return path
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")
            return None

    def should_use_session(self, url: str) -> bool:
        """
        Decide if we should use saved session (randomize to look natural).

        Args:
            url: The URL to check

        Returns:
            True if should use saved session, False otherwise
        """
        domain = urlparse(url).netloc
        path = self._get_session_path(domain)

        if not os.path.exists(path):
            return False

        # 80% chance to use saved session (some variance)
        return random.random() < 0.8

    def clear_session(self, url: str):
        """
        Clear saved session for domain.

        Args:
            url: The URL whose session should be cleared
        """
        domain = urlparse(url).netloc
        path = self._get_session_path(domain)

        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Cleared session for {domain}")

    def get_stats(self) -> dict:
        """
        Get session manager statistics.

        Returns:
            Dict with session statistics
        """
        return {
            "sessions_dir": self.sessions_dir,
            "tracked_domains": len(self.session_usage),
            "sessions": {
                domain: {
                    "last_used": info.get("last_used"),
                    "success_count": info.get("success_count", 0)
                }
                for domain, info in self.session_usage.items()
            }
        }
