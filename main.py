import argparse
import json
import logging
import sys
import os
from app.services.scraper import WebScraper

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging for CLI
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/scraper.log")
    ]
)
logger = logging.getLogger("cli")

def main():
    parser = argparse.ArgumentParser(description="Professional Web Scraper & Article Extractor")
    
    parser.add_argument("--url", help="The URL of the article to scrape")
    parser.add_argument("--text", help="Text snippet to search for the original source")
    parser.add_argument("--visible", action="store_true", help="Run browser in visible mode (headless=False)")
    
    args = parser.parse_args()
    
    if not args.url and not args.text:
        parser.print_help()
        return
    
    scraper = WebScraper()
    
    if args.url:
        logger.info(f"🚀 Starting scrape for URL: {args.url}")
        result = scraper.extract_article(args.url, headless=not args.visible)
        
        if "error" in result:
            logger.error("❌ Scrape failed:")
            print(json.dumps(result, indent=4, ensure_ascii=False))
        else:
            logger.info("✅ Scrape successful:")
            # Filter result to focus on main text and key metadata
            filtered_result = {
                "title": result.get("title"),
                "date": result.get("date"),
                "source": result.get("source"),
                "text": result.get("text")
            }
            print(json.dumps(filtered_result, indent=4, ensure_ascii=False))
        
    if args.text:
        logger.info(f"🔎 Searching for source of text: '{args.text[:50]}...'")
        results = scraper.find_source_from_text(args.text)
        print(json.dumps(results, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()
