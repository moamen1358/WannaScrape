import uvicorn
from fastapi import FastAPI, HTTPException, Request
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

# Ensure logs and screenshots directories exist
os.makedirs("logs", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)

# Configure logging with DEBUG level for detailed error tracking
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/scraper.log")
    ]
)
logger = logging.getLogger("scraper_api")

# Set third-party loggers to WARNING to reduce noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Initialize advanced logger for API-level tracking
api_adv_logger = get_advanced_logger()

# API request counter for session tracking
_api_request_counter = 0

app = FastAPI(
    title="Web Scraper API", 
    version="2.0.0",
    description="Advanced web scraper with 55 user agents, 33 locations, anti-detection scripts, and comprehensive logging"
)

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
    """Get scraping statistics from advanced logger."""
    return {
        "timestamp": datetime.now().isoformat(),
        "stats": api_adv_logger.get_stats()
    }


@app.post("/scrape", response_model=List[ArticleResponse])
def scrape_article(req: ScrapeRequest):
    """Fetch an article and return a list containing the result or error.
    
    Features:
        - 55 rotating user agents (Chrome, Firefox, Safari, Edge, Opera)
        - 33 location profiles with timezone/locale/geolocation
        - Anti-detection: Canvas noise, WebGL spoof, WebRTC protection
        - Comprehensive session logging with timing metrics
    
    Returns:
        List[ArticleResponse]: A list with one item. 
        - On success: The article data with scrape metadata.
        - On failure: An object with the 'error' field set.
        Always returns 200 OK to allow n8n to handle logic flow.
    """
    global _api_request_counter
    _api_request_counter += 1
    request_id = f"API_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_api_request_counter:04d}"
    
    start_time = time.time()
    
    logger.info(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  📥 API REQUEST: {request_id}
║  🌐 URL: {str(req.url)[:60]}{'...' if len(str(req.url)) > 60 else ''}
║  ⚙️  Options: headless={req.headless}, allow_manual={req.allow_manual}
╚══════════════════════════════════════════════════════════════════════════╝""")
    
    try:
        scraper = WebScraper()
        
        # 1. Extract Article using advanced scraper with all anti-detection features
        article_raw = scraper.extract_article(
            str(req.url),
            allow_manual=req.allow_manual,
            headless=req.headless,
            storage_state_path=req.storage_state_path,
        )
        
        duration = time.time() - start_time
        
        if "error" in article_raw:
            error_type = article_raw.get("error_type", "unknown")
            likely_ban = article_raw.get("likely_ban", False)
            recommendation = article_raw.get("recommendation", "")
            user_agent = article_raw.get("user_agent_used", "unknown")
            location = article_raw.get("location_used", "unknown")

            logger.error(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ❌ API SCRAPE FAILED: {request_id}
╠══════════════════════════════════════════════════════════════════════════╣
║  URL:           {str(req.url)[:55]}{'...' if len(str(req.url)) > 55 else ''}
║  Error:         {article_raw['error'][:50]}{'...' if len(article_raw['error']) > 50 else ''}
║  Error Type:    {error_type}
║  Likely Ban:    {'🔴 YES' if likely_ban else '🟢 NO'}
║  User-Agent:    {user_agent[:40]}{'...' if len(str(user_agent)) > 40 else ''}
║  Location:      {location}
║  Duration:      {duration:.2f}s
║  Recommendation: {recommendation[:50] if recommendation else 'N/A'}
╚══════════════════════════════════════════════════════════════════════════╝""")

            # Return error as a valid response item
            return [ArticleResponse(
                error=article_raw["error"],
                scrape_duration=duration,
                user_agent_used=user_agent,
                location_used=location
            )]
        
        # Extract metadata from successful scrape
        user_agent = article_raw.get("user_agent_used", "unknown")
        location = article_raw.get("location_used", "unknown")
        
        logger.info(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ✅ API SCRAPE SUCCESS: {request_id}
╠══════════════════════════════════════════════════════════════════════════╣
║  URL:           {str(req.url)[:55]}{'...' if len(str(req.url)) > 55 else ''}
║  Title:         {article_raw.get('title', 'N/A')[:50]}{'...' if len(str(article_raw.get('title', ''))) > 50 else ''}
║  Content:       {len(article_raw.get('text', ''))} chars
║  User-Agent:    {user_agent[:40]}{'...' if len(str(user_agent)) > 40 else ''}
║  Location:      {location}
║  Duration:      {duration:.2f}s
╚══════════════════════════════════════════════════════════════════════════╝""")
        
        # 2. Return success with enhanced metadata
        return [ArticleResponse(
            title=article_raw.get("title"),
            date=article_raw.get("date"),
            source=article_raw.get("source"),
            text=article_raw.get("text"),
            scrape_duration=duration,
            user_agent_used=user_agent,
            location_used=location
        )]

    except Exception as e:
        duration = time.time() - start_time
        logger.exception(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  💥 API CRITICAL ERROR: {request_id}
╠══════════════════════════════════════════════════════════════════════════╣
║  URL:           {str(req.url)[:55]}{'...' if len(str(req.url)) > 55 else ''}
║  Error:         {str(e)[:50]}{'...' if len(str(e)) > 50 else ''}
║  Error Type:    {type(e).__name__}
║  Duration:      {duration:.2f}s
╚══════════════════════════════════════════════════════════════════════════╝""")
        return [ArticleResponse(error=str(e), scrape_duration=duration)]


if __name__ == "__main__":
    # Run with: uvicorn app.api.scraper_api:app --host 0.0.0.0 --port 8888
    uvicorn.run("app.api.scraper_api:app", host="0.0.0.0", port=8888, reload=True)
