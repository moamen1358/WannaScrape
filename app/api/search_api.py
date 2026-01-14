import uvicorn
import time
import logging
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

# Import the RSS-based search function
from app.services.news_search import search_google_news_rss
# Import user agent manager for search requests
from app.services.user_agents import UserAgentManager

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging with DEBUG level for detailed error tracking
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/search.log")
    ]
)
logger = logging.getLogger("search_api")

# Set third-party loggers to WARNING to reduce noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Initialize UserAgentManager for search requests
ua_manager = UserAgentManager()

# Search request counter
_search_request_counter = 0

app = FastAPI(
    title="News-Search API",
    version="2.0.0",
    description=(
        "Free, no-API-key news search powered by Google News RSS. "
        "Supports complex boolean queries with rotating user agents and location spoofing."
    ),
)

class NewsItem(BaseModel):
    title: str
    link: str
    published: str
    source: str

class SearchResponse(BaseModel):
    query: str
    results: List[NewsItem]
    total: int
    duration: Optional[float] = None
    user_agent_used: Optional[str] = None
    location_used: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    delay: float = 0.0


@app.get("/health")
def health_check():
    """Health check endpoint with system info."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "user_agents": 55,
            "locations": 33,
            "rss_search": True
        }
    }


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    """
    Search for news using Google News RSS via a POST request.
    Uses rotating user agents and location profiles for anti-detection.
    """
    global _search_request_counter
    _search_request_counter += 1
    request_id = f"SEARCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_search_request_counter:04d}"
    
    start_time = time.time()
    
    # Get random profile for this search
    profile = ua_manager.get_random_profile()
    location = ua_manager.get_random_location()
    
    logger.info(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  🔍 SEARCH REQUEST: {request_id}
║  📝 Query: {req.query[:50]}{'...' if len(req.query) > 50 else ''}
║  📊 Limit: {req.limit}
║  🎭 User-Agent: {profile.browser.upper()}/{profile.version} on {profile.os.upper()}
║  📍 Location: {location['name']}
╚══════════════════════════════════════════════════════════════════════════╝""")

    try:
        if req.delay > 0:
            logger.info(f"    ⏳ Delaying search by {req.delay}s...")
            time.sleep(req.delay)

        raw = search_google_news_rss(req.query, limit=req.limit)

        duration = time.time() - start_time
        count = len(raw)

        if count == 0:
            logger.warning(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ⚠️ SEARCH RETURNED ZERO RESULTS: {request_id}
╠══════════════════════════════════════════════════════════════════════════╣
║  Query:         {req.query[:50]}{'...' if len(req.query) > 50 else ''}
║  Duration:      {duration:.2f}s
║  Note:          Could be rate limiting, proxy block, or no matching news
╚══════════════════════════════════════════════════════════════════════════╝""")
        else:
            logger.info(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  ✅ SEARCH SUCCESS: {request_id}
╠══════════════════════════════════════════════════════════════════════════╣
║  Query:         {req.query[:50]}{'...' if len(req.query) > 50 else ''}
║  Results:       {count} items found
║  Duration:      {duration:.2f}s
╚══════════════════════════════════════════════════════════════════════════╝""")

        items = [
            NewsItem(
                title=item["title"],
                link=item["link"],
                published=item["published"],
                source=item["source"]
            )
            for item in raw
        ]

        return SearchResponse(
            query=req.query,
            results=items,
            total=len(items),
            duration=duration,
            user_agent_used=f"{profile.browser}/{profile.version}",
            location_used=location['name']
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.exception(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  💥 SEARCH API ERROR: {request_id}
╠══════════════════════════════════════════════════════════════════════════╣
║  Query:         {req.query[:50]}{'...' if len(req.query) > 50 else ''}
║  Error:         {str(e)[:50]}{'...' if len(str(e)) > 50 else ''}
║  Error Type:    {type(e).__name__}
║  Duration:      {duration:.2f}s
╚══════════════════════════════════════════════════════════════════════════╝""")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run with: uvicorn app.api.search_api:app --host 0.0.0.0 --port 8001 --reload
    uvicorn.run("app.api.search_api:app", host="0.0.0.0", port=8001, reload=True)
