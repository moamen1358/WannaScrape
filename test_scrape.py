#!/usr/bin/env python3
"""
Test script for single URL scraping.

Usage:
    python test_scrape.py <url>
    python test_scrape.py https://www.bbc.com/news
    python test_scrape.py https://example.com --visible
    python test_scrape.py https://example.com --visible --slow
"""

import sys
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from app.core import WebScraper
from app.logging import setup_logging


def test_scrape(url: str, headless: bool = True, verbose: bool = False, slow_mode: bool = False):
    """Test scraping a single URL."""
    
    # Setup logging - always DEBUG to see mouse/scroll details
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level)
    
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + "  🧪 WEB SCRAPER TEST".center(58) + "║")
    print("╠" + "═" * 58 + "╣")
    print(f"║  URL: {url[:50]}{'...' if len(url) > 50 else ''}".ljust(59) + "║")
    print(f"║  Mode: {'👁️  VISIBLE (watch browser)' if not headless else '🔒 Headless'}".ljust(59) + "║")
    print(f"║  Slow Mode: {'✅ Yes (slower movements)' if slow_mode else '❌ No'}".ljust(59) + "║")
    print(f"║  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(59) + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Initialize scraper
    print("🔧 Initializing scraper...")
    scraper = WebScraper()
    print("✅ Scraper initialized")
    print()
    
    if not headless:
        print("┌" + "─" * 58 + "┐")
        print("│" + "  👁️  VISIBLE MODE - WATCH THE BROWSER!".center(58) + "│")
        print("├" + "─" * 58 + "┤")
        print("│  You will see:".ljust(59) + "│")
        print("│  • 🔴 Red dot = mouse cursor position".ljust(59) + "│")
        print("│  • Mouse movements (curved paths)".ljust(59) + "│")
        print("│  • Page scrolling (up/down)".ljust(59) + "│")
        print("│  • Random number of movements (1-5)".ljust(59) + "│")
        print("└" + "─" * 58 + "┘")
        print()
    
    # Run scrape
    print("🚀 Starting scrape...")
    start_time = datetime.now()
    
    result = scraper.extract_article(url, headless=headless)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print()
    print("╔" + "═" * 58 + "╗")
    print(f"║  📊 RESULTS (took {duration:.1f}s)".ljust(59) + "║")
    print("╠" + "═" * 58 + "╣")
    
    if "error" in result:
        print("║  ❌ FAILED".ljust(59) + "║")
        print(f"║  Error: {result['error'][:45]}...".ljust(59) + "║")
        print(f"║  Type: {result.get('error_type', 'unknown')}".ljust(59) + "║")
        print(f"║  Likely Ban: {result.get('likely_ban', False)}".ljust(59) + "║")
        if result.get('recommendation'):
            print(f"║  Tip: {result['recommendation'][:48]}".ljust(59) + "║")
    else:
        print("║  ✅ SUCCESS".ljust(59) + "║")
        title = result.get('title', 'N/A')[:45]
        print(f"║  Title: {title}".ljust(59) + "║")
        print(f"║  Date: {result.get('date', 'N/A')}".ljust(59) + "║")
        print(f"║  User Agent: {result.get('user_agent_used', 'N/A')[:40]}".ljust(59) + "║")
        print(f"║  Location: {result.get('location_used', 'N/A')}".ljust(59) + "║")
        
        text = result.get('text', '')
        print(f"║  Text: {len(text):,} chars".ljust(59) + "║")
    
    print("╚" + "═" * 58 + "╝")
    
    if "error" not in result:
        text = result.get('text', '')
        if text:
            print()
            print("📝 Content Preview:")
            print("─" * 60)
            preview = text[:600].replace('\n', ' ').strip()
            print(preview + "..." if len(text) > 600 else preview)
            print("─" * 60)
    
    # Save full result to file
    output_file = "test_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Full result saved to: {output_file}")
    
    # Show log file location
    print()
    print("📋 Check the detailed log in: logs/scrapes/")
    print("   Look for lines like:")
    print("   • 🖱️ Will perform X mouse movements (random 1-5)")
    print("   • 🖱️ Moving: (x1, y1) → (x2, y2)")
    print("   • 📜 Will perform X scroll actions (random 1-5)")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Test URL scraping with visible mouse movements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_scrape.py https://example.com
  python test_scrape.py https://bbc.com/news --visible
  python test_scrape.py https://reuters.com --visible -v

In visible mode, you'll see:
  • A red dot showing mouse position
  • Curved mouse movements
  • Page scrolling
        """
    )
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--visible", action="store_true", 
                        help="Show browser window (headless=false)")
    parser.add_argument("--slow", action="store_true",
                        help="Slow down movements for visibility")
    parser.add_argument("-v", "--verbose", action="store_true", 
                        help="Show DEBUG level logs")
    
    args = parser.parse_args()
    
    result = test_scrape(
        url=args.url,
        headless=not args.visible,
        verbose=args.verbose,
        slow_mode=args.slow
    )
    
    # Exit with error code if failed
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print()
        print("╔" + "═" * 58 + "╗")
        print("║" + "  🧪 WEB SCRAPER TEST".center(58) + "║")
        print("╚" + "═" * 58 + "╝")
        print()
        print("Usage: python test_scrape.py <url> [options]")
        print()
        print("Options:")
        print("  --visible    Show browser window (see mouse movements)")
        print("  --slow       Slower movements for better visibility")
        print("  -v           Verbose debug output")
        print()
        print("Examples:")
        print("  python test_scrape.py https://example.com")
        print("  python test_scrape.py https://bbc.com/news --visible")
        print("  python test_scrape.py https://reuters.com --visible -v")
        print()
        sys.exit(0)
    
    main()
