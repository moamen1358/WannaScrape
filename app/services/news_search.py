import feedparser
import urllib.parse
import json
import argparse
from datetime import datetime
import time
import logging

import requests
import random
from pathlib import Path

# Configure logger
logger = logging.getLogger("news_search")
if not logger.handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def _mask_proxy_url(proxy_dict: dict) -> str:
    """Mask proxy credentials for safe logging."""
    if not proxy_dict:
        return "None"
    # Extract server part from http://user:pass@host:port
    proxy_url = proxy_dict.get("http", "")
    if "@" in proxy_url:
        parts = proxy_url.split("@")
        return f"***@{parts[-1]}"
    return proxy_url


def _classify_search_error(error_msg: str, status_code: int = None, response_text: str = "") -> dict:
    """Classify search error type for debugging."""
    error_lower = error_msg.lower()
    response_lower = response_text.lower() if response_text else ""

    classification = {
        "type": "unknown",
        "likely_ban": False,
        "retry_recommended": True,
        "details": ""
    }

    # Rate limiting
    if status_code == 429 or "rate limit" in error_lower or "too many requests" in error_lower:
        classification["type"] = "rate_limit"
        classification["likely_ban"] = True
        classification["retry_recommended"] = False
        classification["details"] = "Rate limited by Google News - increase delay or rotate proxy"

    # Forbidden / Access Denied
    elif status_code == 403 or "forbidden" in error_lower or "access denied" in error_lower:
        classification["type"] = "access_denied"
        classification["likely_ban"] = True
        classification["retry_recommended"] = False
        classification["details"] = "Access denied - IP or proxy may be blocked by Google"

    # CAPTCHA / Bot detection
    elif any(x in response_lower for x in ["captcha", "unusual traffic", "automated queries"]):
        classification["type"] = "bot_detection"
        classification["likely_ban"] = True
        classification["retry_recommended"] = False
        classification["details"] = "Bot detection triggered - Google detected automated access"

    # Connection / Network errors
    elif any(x in error_lower for x in ["connection", "timeout", "network", "refused"]):
        classification["type"] = "connection_error"
        classification["likely_ban"] = False
        classification["retry_recommended"] = True
        classification["details"] = "Connection error - check network or proxy"

    # Server errors
    elif status_code and status_code >= 500:
        classification["type"] = "server_error"
        classification["likely_ban"] = False
        classification["retry_recommended"] = True
        classification["details"] = "Google News server error - try again later"

    return classification

def _load_config():
    """Load configuration from JSON file"""
    try:
        config_path = Path("config/config.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
    except Exception:
        pass
    return None

def _get_proxies(config):
    """Load proxies from file defined in config"""
    if not config or not config.get("proxies", {}).get("enabled"):
        return []
        
    proxy_filename = config["proxies"]["proxy_file"]
    
    # Try to find it in config directory first
    config_dir = Path("config")
    proxy_file = config_dir / proxy_filename
    
    if not proxy_file.exists():
        # Fallback to current directory
        proxy_file = Path(proxy_filename)
        
    if not proxy_file.exists():
        return []
    
    proxies = []
    try:
        with open(proxy_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(":")
                if len(parts) == 4:
                    proxies.append({
                        "http": f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}",
                        "https": f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                    })
    except Exception:
        pass
    return proxies

def search_google_news_rss(query, limit=10):
    """Search Google News RSS feed with detailed logging for debugging."""
    start_time = time.time()

    # Load config and prepare request
    config = _load_config()
    proxies = _get_proxies(config)

    # Select random proxy and user agent
    proxy = random.choice(proxies) if proxies else None
    user_agent = "Mozilla/5.0"  # Default
    if config and config.get("user_agents"):
        user_agent = random.choice(config["user_agents"])

    headers = {"User-Agent": user_agent}

    # Encode the query for the URL
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    logger.info(f"Fetching RSS Feed for query: '{query}'")
    logger.debug(f"RSS URL: {rss_url}")
    logger.debug(f"Proxy: {_mask_proxy_url(proxy)}")
    logger.debug(f"User-Agent: {user_agent}")

    response = None
    try:
        # Fetch with requests to use proxy/headers
        response = requests.get(rss_url, headers=headers, proxies=proxy, timeout=30)
        response.raise_for_status()
        content = response.content
        logger.debug(f"Response status: {response.status_code}, Content-Length: {len(content)}")
    except requests.exceptions.HTTPError as e:
        status_code = response.status_code if response else None
        response_text = response.text[:500] if response else ""
        error_classification = _classify_search_error(str(e), status_code, response_text)

        logger.error(f"""
=== SEARCH REQUEST FAILED (HTTP Error) ===
Query: {query}
RSS URL: {rss_url}
Proxy: {_mask_proxy_url(proxy)}
User-Agent: {user_agent}
Status Code: {status_code}
Error: {e}
Error Type: {error_classification['type']}
Likely Ban: {error_classification['likely_ban']}
Recommendation: {error_classification['details']}
Response Preview: {response_text[:200] if response_text else 'N/A'}
Duration: {time.time() - start_time:.2f}s
===========================================""")
        return []

    except requests.exceptions.RequestException as e:
        error_classification = _classify_search_error(str(e))

        logger.error(f"""
=== SEARCH REQUEST FAILED (Connection Error) ===
Query: {query}
RSS URL: {rss_url}
Proxy: {_mask_proxy_url(proxy)}
User-Agent: {user_agent}
Error: {e}
Error Type: {error_classification['type']}
Likely Ban: {error_classification['likely_ban']}
Recommendation: {error_classification['details']}
Duration: {time.time() - start_time:.2f}s
=================================================""")
        return []

    except Exception as e:
        logger.error(f"""
=== SEARCH REQUEST FAILED (Unknown Error) ===
Query: {query}
RSS URL: {rss_url}
Proxy: {_mask_proxy_url(proxy)}
User-Agent: {user_agent}
Error: {e}
Error Type: {type(e).__name__}
Duration: {time.time() - start_time:.2f}s
==============================================""")
        return []

    # Parse the feed content
    feed = feedparser.parse(content)

    # Check for feed errors
    if feed.bozo:
        logger.warning(f"Feed parsing issue: {feed.bozo_exception}")

    results = []

    if hasattr(feed, 'entries'):
        for entry in feed.entries[:limit]:
            # Extract relevant fields
            article = {
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "source": entry.source.title if hasattr(entry, 'source') else "Unknown"
            }
            results.append(article)

    duration = time.time() - start_time
    logger.info(f"Search completed: Found {len(results)} results for '{query}' in {duration:.2f}s")

    if len(results) == 0:
        logger.warning(f"""
=== ZERO RESULTS WARNING ===
Query: {query}
Proxy: {_mask_proxy_url(proxy)}
Response Length: {len(content)}
Feed Entries: {len(feed.entries) if hasattr(feed, 'entries') else 0}
This could indicate: rate limiting, blocked proxy, or no matching news
===============================""")

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search Google News via RSS (Free & Powerful)")
    parser.add_argument("--query", required=True, help="Complex query string")
    parser.add_argument("--limit", type=int, default=10, help="Number of results")
    
    args = parser.parse_args()
    
    results = search_google_news_rss(args.query, args.limit)
    print(json.dumps(results, indent=4))
