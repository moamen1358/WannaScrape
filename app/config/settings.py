"""
Application settings using Pydantic for type-safe configuration.
Supports environment variables and .env files.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("scraper.settings")


class BrowserSettings(BaseSettings):
    """Browser configuration settings."""
    headless: bool = True
    slow_mo: int = 50
    timeout: int = 30000


class RetrySettings(BaseSettings):
    """Retry configuration settings."""
    max_attempts: int = 3
    min_wait: int = 1
    max_wait: int = 5


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration settings."""
    max_requests_per_domain_per_hour: int = 60
    min_delay_between_requests: int = 2
    max_delay_between_requests: int = 8


class CaptchaSettings(BaseSettings):
    """CAPTCHA solving configuration settings."""
    enabled: bool = False
    service: str = "2captcha"
    api_key: str = ""
    timeout: int = 120
    max_retries: int = 3


class ProxySettings(BaseSettings):
    """Proxy configuration settings."""
    enabled: bool = False
    proxy_file: str = "config/proxies.txt"


class HumanBehaviorSettings(BaseSettings):
    """Human behavior simulation settings."""
    mouse_movements_min: int = 2
    mouse_movements_max: int = 3
    scroll_actions_min: int = 2
    scroll_actions_max: int = 3
    movement_speed: float = 0.008
    pause_min: float = 0.1
    pause_max: float = 0.3


class Settings(BaseSettings):
    """
    Main application settings.

    Settings are loaded in order of priority:
    1. Environment variables
    2. .env file
    3. config/config.json
    4. Default values
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SCRAPER_",
        extra="ignore"
    )

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"

    # Browser Settings
    headless: bool = True
    slow_mo: int = 50
    browser_timeout: int = 30000

    # CAPTCHA Settings
    captcha_enabled: bool = False
    captcha_service: str = "2captcha"
    captcha_api_key: str = ""
    captcha_timeout: int = 120

    # Proxy Settings
    proxy_enabled: bool = False
    proxy_file: str = "config/proxies.txt"

    # Rate Limiting
    max_requests_per_hour: int = 60
    min_delay: int = 2
    max_delay: int = 8

    # Timeouts
    max_scrape_timeout: int = 120

    # Logging
    log_level: str = "INFO"
    log_dir: str = "data/logs"

    # Data directories
    screenshots_dir: str = "data/screenshots"
    sessions_dir: str = "data/sessions"

    # User agents (loaded from user_agents.py)
    user_agents: List[str] = Field(default_factory=list)

    # Navigation strategies
    strategies: List[Dict[str, Any]] = Field(default_factory=lambda: [
        {"wait": "domcontentloaded", "timeout": 40000, "sleep": 4},
        {"wait": "load", "timeout": 60000, "sleep": 3},
        {"wait": "networkidle", "timeout": 80000, "sleep": 2}
    ])

    @classmethod
    def from_config_file(cls, config_path: str = "config/config.json") -> "Settings":
        """
        Load settings from JSON config file, with env vars taking precedence.
        """
        config_data = {}

        if Path(config_path).exists():
            try:
                with open(config_path) as f:
                    config_data = json.load(f)
                logger.info(f"Loaded config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

        # Map config.json structure to flat settings
        flat_config = {}

        if "browser" in config_data:
            browser = config_data["browser"]
            flat_config["headless"] = browser.get("headless", True)
            flat_config["slow_mo"] = browser.get("slow_mo", 50)
            flat_config["browser_timeout"] = browser.get("timeout", 30000)

        if "captcha" in config_data:
            captcha = config_data["captcha"]
            flat_config["captcha_enabled"] = captcha.get("enabled", False)
            flat_config["captcha_service"] = captcha.get("service", "2captcha")
            flat_config["captcha_api_key"] = captcha.get("api_key", "")
            flat_config["captcha_timeout"] = captcha.get("timeout", 120)

        if "proxies" in config_data:
            proxies = config_data["proxies"]
            flat_config["proxy_enabled"] = proxies.get("enabled", False)
            flat_config["proxy_file"] = proxies.get("proxy_file", "config/proxies.txt")

        if "rate_limiting" in config_data:
            rate = config_data["rate_limiting"]
            flat_config["max_requests_per_hour"] = rate.get("max_requests_per_domain_per_hour", 60)
            flat_config["min_delay"] = rate.get("min_delay_between_requests", 2)
            flat_config["max_delay"] = rate.get("max_delay_between_requests", 8)

        if "user_agents" in config_data:
            flat_config["user_agents"] = config_data["user_agents"]

        if "strategies" in config_data:
            flat_config["strategies"] = config_data["strategies"]

        if "max_scrape_timeout" in config_data:
            flat_config["max_scrape_timeout"] = config_data["max_scrape_timeout"]

        return cls(**flat_config)

    def to_legacy_config(self) -> dict:
        """
        Convert settings to legacy config.json format for backward compatibility.
        """
        return {
            "browser": {
                "headless": self.headless,
                "slow_mo": self.slow_mo,
                "timeout": self.browser_timeout
            },
            "captcha": {
                "enabled": self.captcha_enabled,
                "service": self.captcha_service,
                "api_key": self.captcha_api_key,
                "timeout": self.captcha_timeout
            },
            "proxies": {
                "enabled": self.proxy_enabled,
                "proxy_file": self.proxy_file
            },
            "rate_limiting": {
                "max_requests_per_domain_per_hour": self.max_requests_per_hour,
                "min_delay_between_requests": self.min_delay,
                "max_delay_between_requests": self.max_delay
            },
            "retry": {
                "max_attempts": 3,
                "min_wait": 2,
                "max_wait": 10
            },
            "human_behavior": {
                "mouse_movements": {"min": 2, "max": 3},
                "scroll_actions": {"min": 2, "max": 3},
                "movement_speed": 0.008,
                "pause_between_actions": {"min": 0.1, "max": 0.3}
            },
            "user_agents": self.user_agents,
            "strategies": self.strategies,
            "max_scrape_timeout": self.max_scrape_timeout
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_config_file()
    return _settings


def reload_settings(config_path: str = "config/config.json") -> Settings:
    """Reload settings from config file."""
    global _settings
    _settings = Settings.from_config_file(config_path)
    return _settings
