#!/usr/bin/env python3
"""
Test script for single URL scraping.

Usage:
    python test_scrape.py <url>
    python test_scrape.py https://www.bbc.com/news
    python test_scrape.py https://example.com --no-headless
"""

import sys
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from app.core import WebScraper
from app.logging import setup_logging


def test_scrape(url: str, headless: bool = True, verbose: bool = False):
    """Test scraping a single URL."""
    
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level)
    
    print("=" * 60)
    print(f"🧪 Web Scraper Test")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Headless: {headless}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Initialize scraper
    print("🔧 Initializing scraper...")
    scraper = WebScraper()
    print("✅ Scraper initialized")
    print()
    
    # Run scrape
    print("🚀 Starting scrape...")
    start_time = datetime.now()
    
    result = scraper.extract_article(url, headless=headless)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print()
    print("=" * 60)
    print(f"📊 Results (took {duration:.1f}s)")
    print("=" * 60)
    
    if "error" in result:
        print(f"❌ FAILED")
        print(f"   Error: {result['error']}")
        print(f"   Type: {result.get('error_type', 'unknown')}")
        print(f"   Likely Ban: {result.get('likely_ban', False)}")
        if result.get('recommendation'):
            print(f"   Recommendation: {result['recommendation']}")
    else:
        print(f"✅ SUCCESS")
        print(f"   Title: {result.get('title', 'N/A')}")
        print(f"   Date: {result.get('date', 'N/A')}")
        print(f"   Source: {result.get('source', 'N/A')}")
        print(f"   Final URL: {result.get('final_url', 'N/A')}")
        print(f"   User Agent: {result.get('user_agent_used', 'N/A')}")
        print(f"   Location: {result.get('location_used', 'N/A')}")
        
        text = result.get('text', '')
        print(f"   Text Length: {len(text)} chars")
        
        if text:
            print()
            print("📝 Content Preview (first 500 chars):")
            print("-" * 40)
            print(text[:500] + "..." if len(text) > 500 else text)
    
    print()
    print("=" * 60)
    
    # Save full result to file
    output_file = "test_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"💾 Full result saved to: {output_file}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Test URL scraping")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    result = test_scrape(
        url=args.url,
        headless=not args.no_headless,
        verbose=args.verbose
    )
    
    # Exit with error code if failed
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default test URL
        print("Usage: python test_scrape.py <url>")
        print()
        print("Example URLs to test:")
        print("  python test_scrape.py https://www.bbc.com/news")
        print("  python test_scrape.py https://example.com")
        print("  python test_scrape.py https://www.reuters.com --no-headless")
        sys.exit(0)
    
    main()
