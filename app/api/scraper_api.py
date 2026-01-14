import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import logging
import time
import os
from datetime import datetime

# Import the existing scraper implementation
from app.services.scraper import WebScraper
# Import advanced logging and user agent manager for API-level insights
from app.services.advanced_logging import get_advanced_logger
from app.services.user_agents import UserAgentManager
# Import enterprise logging
from app.services.enterprise_logging import (
    EnterpriseLogger,
    set_correlation_id,
    get_correlation_id,
    create_logging_middleware
)

# Ensure logs and screenshots directories exist
os.makedirs("logs", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)

# Initialize enterprise logger (replaces basic logging config)
enterprise_logger = EnterpriseLogger.setup(
    service="web-scraper-api",
    environment=os.getenv("ENVIRONMENT", "development"),
    log_dir="logs",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    retention_days=30
)

# Legacy logger for backwards compatibility
logger = logging.getLogger("scraper_api")

# Set third-party loggers to WARNING to reduce noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Initialize advanced logger for API-level tracking
api_adv_logger = get_advanced_logger()

app = FastAPI(
    title="Web Scraper API",
    version="2.1.0",
    description="Advanced web scraper with 55 user agents, 33 locations, anti-detection scripts, and enterprise logging"
)

# Add logging middleware for automatic request/response logging
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Enterprise logging middleware - tracks all requests with correlation IDs."""
    # Generate or extract correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
    correlation_id = set_correlation_id(correlation_id)

    # Log request
    start_time = time.time()
    enterprise_logger.api.log_request(
        method=request.method,
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
        request_id=correlation_id
    )

    # Process request
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id

        # Log response
        enterprise_logger.api.log_response(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms
        )

        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        enterprise_logger.api.log_error(e, context={
            "method": request.method,
            "path": str(request.url.path),
            "duration_ms": duration_ms
        })
        raise

class ScrapeRequest(BaseModel):
    url: HttpUrl
    # Optional text snippet to find the source of – the scraper already supports this via the CLI
    text: Optional[str] = None
    # New options to control scraper behavior
    allow_manual: bool = True
    headless: Optional[bool] = None
    storage_state_path: Optional[str] = None

class ArticleResponse(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    source: Optional[str] = None
    text: Optional[str] = None
    error: Optional[str] = None
    # New fields for enhanced tracking
    scrape_duration: Optional[float] = None
    user_agent_used: Optional[str] = None
    location_used: Optional[str] = None


@app.get("/health")
def health_check():
    """Health check endpoint with system info."""
    ua_manager = UserAgentManager()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "user_agents": 55,
            "locations": 33,
            "anti_detection": ["canvas_noise", "webgl_spoof", "webrtc_protection", "network_spoof", "battery_spoof"],
            "advanced_logging": True
        },
        "sample_profile": {
            "browser": ua_manager.get_random_profile().browser,
            "location": ua_manager.get_random_location()["name"]
        }
    }


@app.get("/stats")
def get_stats():
    """Get scraping statistics from both legacy and enterprise loggers."""
    return {
        "timestamp": datetime.now().isoformat(),
        "correlation_id": get_correlation_id(),
        "legacy_stats": api_adv_logger.get_stats(),
        "enterprise_stats": enterprise_logger.scrape.get_stats()
    }


@app.post("/scrape", response_model=List[ArticleResponse])
def scrape_article(req: ScrapeRequest):
    """Fetch an article and return a list containing the result or error.

    Features:
        - 55 rotating user agents (Chrome, Firefox, Safari, Edge, Opera)
        - 33 location profiles with timezone/locale/geolocation
        - Anti-detection: Canvas noise, WebGL spoof, WebRTC protection
        - Enterprise logging with correlation IDs and structured JSON

    Returns:
        List[ArticleResponse]: A list with one item.
        - On success: The article data with scrape metadata.
        - On failure: An object with the 'error' field set.
        Always returns 200 OK to allow n8n to handle logic flow.
    """
    start_time = time.time()
    url = str(req.url)

    # Start enterprise scrape logging (generates correlation ID)
    session_id = enterprise_logger.scrape.log_scrape_start(
        url=url,
        attempt=1,
        max_attempts=3
    )

    try:
        scraper = WebScraper()

        # Extract Article using advanced scraper with all anti-detection features
        article_raw = scraper.extract_article(
            url,
            allow_manual=req.allow_manual,
            headless=req.headless,
            storage_state_path=req.storage_state_path,
        )

        duration_ms = (time.time() - start_time) * 1000
        duration_s = duration_ms / 1000

        if "error" in article_raw:
            error_type = article_raw.get("error_type", "unknown")
            likely_ban = article_raw.get("likely_ban", False)
            user_agent = article_raw.get("user_agent_used", "unknown")
            location = article_raw.get("location_used", "unknown")

            # Enterprise logging for failed scrape
            enterprise_logger.scrape.log_scrape_failed(
                url=url,
                error_type=error_type,
                error_message=article_raw["error"],
                duration_ms=duration_ms,
                is_blocked=likely_ban,
                attempt=1
            )

            return [ArticleResponse(
                error=article_raw["error"],
                scrape_duration=duration_s,
                user_agent_used=user_agent,
                location_used=location
            )]

        # Extract metadata from successful scrape
        user_agent = article_raw.get("user_agent_used", "unknown")
        location = article_raw.get("location_used", "unknown")
        text_content = article_raw.get("text", "")

        # Enterprise logging for successful scrape
        enterprise_logger.scrape.log_scrape_success(
            url=url,
            duration_ms=duration_ms,
            content_size=len(text_content),
            extraction_method=article_raw.get("extraction_method", ""),
            final_url=article_raw.get("final_url", url)
        )

        # Log anti-detection config used
        enterprise_logger.scrape.log_anti_detection(
            user_agent=user_agent,
            browser=article_raw.get("browser_used", "unknown"),
            viewport=article_raw.get("viewport_used", "unknown"),
            location=location,
            proxy=article_raw.get("proxy_used", "")
        )

        return [ArticleResponse(
            title=article_raw.get("title"),
            date=article_raw.get("date"),
            source=article_raw.get("source"),
            text=text_content,
            scrape_duration=duration_s,
            user_agent_used=user_agent,
            location_used=location
        )]

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        # Enterprise logging for exceptions
        enterprise_logger.scrape.log_scrape_failed(
            url=url,
            error_type=type(e).__name__,
            error_message=str(e),
            duration_ms=duration_ms,
            is_blocked=False,
            attempt=1
        )
        enterprise_logger.api.log_error(e, context={"url": url})

        return [ArticleResponse(error=str(e), scrape_duration=duration_ms / 1000)]


if __name__ == "__main__":
    # Run with: uvicorn app.api.scraper_api:app --host 0.0.0.0 --port 8888
    uvicorn.run("app.api.scraper_api:app", host="0.0.0.0", port=8888, reload=True)
