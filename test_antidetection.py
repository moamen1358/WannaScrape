#!/usr/bin/env python3
"""
Anti-Detection Test Suite
=========================
Test your scraper against common bot detection services.
"""

import asyncio
import json
import sys
import argparse
from datetime import datetime
from app.services.scraper import WebScraper

# Test URLs for bot detection
BOT_DETECTION_TESTS = [
    {
        "name": "Sannysoft Bot Detection",
        "url": "https://bot.sannysoft.com/",
        "check": "Check for 'missing' or 'failed' indicators in the page"
    },
    {
        "name": "CreepJS Fingerprint",
        "url": "https://abrahamjuliot.github.io/creepjs/",
        "check": "Check trust score - aim for 'B' or better"
    },
    {
        "name": "BrowserLeaks Canvas",
        "url": "https://browserleaks.com/canvas",
        "check": "Should show randomized canvas fingerprint"
    },
    {
        "name": "BrowserLeaks WebGL",
        "url": "https://browserleaks.com/webgl",
        "check": "Should show spoofed GPU info"
    },
    {
        "name": "PixelScan",
        "url": "https://pixelscan.net/",
        "check": "Should pass fingerprint consistency checks"
    },
    {
        "name": "BrowserScan",
        "url": "https://www.browserscan.net/",
        "check": "Comprehensive bot detection - aim for green checks"
    },
    {
        "name": "Incolumitas Bot Detection",
        "url": "https://bot.incolumitas.com/",
        "check": "Advanced detection tests"
    },
    {
        "name": "Device Info",
        "url": "https://www.deviceinfo.me/",
        "check": "Should show consistent device profile"
    }
]

# Challenging websites to test
CHALLENGING_SITES = [
    {
        "name": "Cloudflare Protected",
        "url": "https://nowsecure.nl/",
        "expected": "Should pass Cloudflare challenge"
    },
    {
        "name": "DataDome Protected", 
        "url": "https://www.footlocker.com/",
        "expected": "May require residential proxy"
    },
    {
        "name": "PerimeterX Protected",
        "url": "https://www.zillow.com/",
        "expected": "May require residential proxy"
    }
]


def test_bot_detection(scraper: WebScraper, url: str, name: str) -> dict:
    """Test a single bot detection URL."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        result = scraper.extract_article(url, headless=False)
        
        if "error" in result:
            return {
                "name": name,
                "url": url,
                "status": "FAILED",
                "error": result.get("error", "Unknown error"),
                "likely_ban": result.get("likely_ban", False)
            }
        
        # Check if we got content
        text = result.get("text", "")
        html_length = len(result.get("html", ""))
        
        return {
            "name": name,
            "url": url,
            "status": "SUCCESS",
            "text_length": len(text),
            "html_length": html_length,
            "final_url": result.get("url", url)
        }
        
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "status": "ERROR",
            "error": str(e)
        }


def run_tests(test_type: str = "detection"):
    """Run selected test suite."""
    print(f"\n{'#'*60}")
    print(f"# ANTI-DETECTION TEST SUITE - {datetime.now()}")
    print(f"{'#'*60}")
    
    scraper = WebScraper()
    results = []
    
    if test_type == "detection":
        tests = BOT_DETECTION_TESTS
    else:
        tests = CHALLENGING_SITES
    
    for test in tests:
        result = test_bot_detection(scraper, test["url"], test["name"])
        result["check"] = test.get("check") or test.get("expected", "")
        results.append(result)
        
        # Status indicator
        if result["status"] == "SUCCESS":
            print(f"✅ {test['name']}: PASSED")
        else:
            print(f"❌ {test['name']}: {result['status']} - {result.get('error', '')[:50]}")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    passed = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] != "SUCCESS")
    
    print(f"✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    
    # Save results
    output_file = f"test_antidetection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test anti-detection capabilities")
    parser.add_argument(
        "--type", "-t",
        choices=["detection", "challenging"],
        default="detection",
        help="Test type: 'detection' for bot detection sites, 'challenging' for protected sites"
    )
    parser.add_argument(
        "--url", "-u",
        help="Test a specific URL instead of the test suite"
    )
    
    args = parser.parse_args()
    
    if args.url:
        scraper = WebScraper()
        result = test_bot_detection(scraper, args.url, "Custom URL")
        print(json.dumps(result, indent=2))
    else:
        run_tests(args.type)
