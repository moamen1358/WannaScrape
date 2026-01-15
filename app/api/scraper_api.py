"""
Web Scraper API - FastAPI application with dependency injection.

Production-ready API for web scraping with anti-detection features.
"""

import time
import os
import uuid
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

# Import the core scraper
from app.core import WebScraper

# Import logging
from app.logging import setup_logging, get_scrape_logger, get_correlation_id, set_correlation_id

# Ensure directories exist
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/screenshots", exist_ok=True)

# Setup logging
logger = setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

# Singleton scraper instance
_scraper_instance: Optional[WebScraper] = None


def get_scraper() -> WebScraper:
    """Dependency injection for WebScraper singleton."""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = WebScraper()
    return _scraper_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Web Scraper API...")
    get_scraper()  # Initialize scraper on startup
    yield
    # Shutdown
    logger.info("Shutting down Web Scraper API...")


# Create FastAPI app
app = FastAPI(
    title="Web Scraper API",
    version="2.0.0",
    description="Production-ready web scraper with anti-detection features",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ScrapeRequest(BaseModel):
    """Request model for scraping."""
    url: HttpUrl
    headless: Optional[bool] = None
    storage_state_path: Optional[str] = None


class ArticleResponse(BaseModel):
    """Response model for scraped articles."""
    title: Optional[str] = None
    date: Optional[str] = None
    source: Optional[str] = None
    text: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    scrape_duration: Optional[float] = None
    user_agent_used: Optional[str] = None
    location_used: Optional[str] = None
    final_url: Optional[str] = None


class SearchRequest(BaseModel):
    """Request model for text search."""
    text: str
    num_results: int = 3


class SearchResult(BaseModel):
    """Response model for search results."""
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None


# Middleware for correlation ID
@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    """Add correlation ID to all requests."""
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())[:8]
    set_correlation_id(correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "50+ user agents",
            "30+ locations",
            "Anti-detection scripts",
            "CAPTCHA solving",
            "Proxy rotation",
        ]
    }


@app.get("/stats")
def get_stats(scraper: WebScraper = Depends(get_scraper)):
    """Get scraping statistics."""
    return {
        "timestamp": datetime.now().isoformat(),
        "correlation_id": get_correlation_id(),
        "stats": scraper.get_stats()
    }


@app.post("/scrape", response_model=List[ArticleResponse])
def scrape_article(
    req: ScrapeRequest,
    scraper: WebScraper = Depends(get_scraper)
):
    """
    Scrape an article from a URL.

    Features:
    - 50+ rotating user agents
    - 30+ location profiles
    - Anti-detection: Canvas noise, WebGL spoof, WebRTC protection
    - CAPTCHA solving support
    - Proxy rotation

    Returns:
        List[ArticleResponse]: A list with one item (for n8n compatibility).
    """
    start_time = time.time()
    url = str(req.url)

    try:
        article_raw = scraper.extract_article(
            url,
            headless=req.headless,
            storage_state_path=req.storage_state_path,
        )

        duration_s = time.time() - start_time

        if "error" in article_raw:
            return [ArticleResponse(
                error=article_raw["error"],
                error_type=article_raw.get("error_type", "unknown"),
                scrape_duration=duration_s,
                user_agent_used=article_raw.get("user_agent_used", "unknown"),
                location_used=article_raw.get("location_used", "unknown"),
                final_url=article_raw.get("final_url", url),
            )]

        return [ArticleResponse(
            title=article_raw.get("title"),
            date=article_raw.get("date"),
            source=article_raw.get("source"),
            text=article_raw.get("text"),
            scrape_duration=duration_s,
            user_agent_used=article_raw.get("user_agent_used", "unknown"),
            location_used=article_raw.get("location_used", "unknown"),
            final_url=article_raw.get("final_url", url),
        )]

    except Exception as e:
        duration_s = time.time() - start_time
        logger.error(f"Scrape error: {e}")
        return [ArticleResponse(error=str(e), scrape_duration=duration_s)]


@app.post("/search", response_model=List[SearchResult])
def search_source(
    req: SearchRequest,
    scraper: WebScraper = Depends(get_scraper)
):
    """
    Search for the original source of a text snippet.
    """
    try:
        results = scraper.find_source_from_text(req.text, num_results=req.num_results)
        return [SearchResult(**r) for r in results]
    except Exception as e:
        logger.error(f"Search error: {e}")
        return [SearchResult(error=str(e))]


if __name__ == "__main__":
    uvicorn.run("app.api.scraper_api:app", host="0.0.0.0", port=8000, reload=True)
