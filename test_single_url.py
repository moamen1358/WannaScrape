#!/usr/bin/env python3
"""
Test script to scrape a single URL and display results.

Usage:
    python test_single_url.py <url>
    python test_single_url.py https://example.com/article

Options:
    --no-headless    Show browser window (useful for debugging)
    --verbose        Show debug logs
"""

import sys
import json
import logging
import argparse
from app.services.scraper import WebScraper


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Test scraping a single URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python test_single_url.py https://www.bbc.com/news/technology-12345
    python test_single_url.py https://techcrunch.com/article --no-headless
    python test_single_url.py https://example.com --verbose
        """
    )
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger("test")

    print("\n" + "="*60)
    print("WEBSITE SCRAPER TEST")
    print("="*60)
    print(f"URL: {args.url}")
    print(f"Headless: {not args.no_headless}")
    print("="*60 + "\n")

    # Initialize scraper
    logger.info("Initializing scraper...")
    scraper = WebScraper()

    # Show proxy status
    if scraper.proxies:
        logger.info(f"Proxies loaded: {len(scraper.proxies)}")
    else:
        logger.warning("No proxies configured - using direct connection")

    # Scrape the URL
    logger.info("Starting scrape...")
    print()

    try:
        result = scraper.extract_article(
            url=args.url,
            headless=not args.no_headless
        )

        print("\n" + "="*60)
        print("RESULT")
        print("="*60)

        if "error" in result:
            print(f"\n[ERROR] {result['error']}")
            if "error_type" in result:
                print(f"  Type: {result['error_type']}")
            if "likely_ban" in result:
                print(f"  Likely Ban: {result['likely_ban']}")
            if "recommendation" in result:
                print(f"  Recommendation: {result['recommendation']}")
            if "final_url" in result:
                print(f"  Final URL: {result['final_url']}")
            print()
            return 1

        # Success - display results
        print(f"\n[SUCCESS]")
        print(f"  Title: {result.get('title', 'N/A')}")
        print(f"  Date: {result.get('date', 'N/A')}")
        print(f"  Source: {result.get('source', 'N/A')}")
        print(f"  Final URL: {result.get('final_url', 'N/A')}")

        text = result.get('text', '')
        print(f"  Text Length: {len(text)} characters")

        # Show preview of text
        print("\n" + "-"*60)
        print("CONTENT PREVIEW (first 500 chars)")
        print("-"*60)
        preview = text[:500] + "..." if len(text) > 500 else text
        print(preview)
        print("-"*60)

        # Option to save full result
        save_path = "test_result.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nFull result saved to: {save_path}")

        return 0

    except KeyboardInterrupt:
        print("\n\nScraping cancelled by user.")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
