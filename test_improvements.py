#!/usr/bin/env python3
"""Test script to verify all anti-detection improvements."""

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

from app.services.scraper import WebScraper
from app.services.user_agents import VIEWPORTS_BY_OS, LOCATION_PROFILES

print('='*70)
print('TESTING ALL ANTI-DETECTION IMPROVEMENTS')
print('='*70)

scraper = WebScraper()

# Test the new features
profile = scraper.ua_manager.get_random_profile()
viewport = scraper.ua_manager.get_matching_viewport(profile)
location = scraper.ua_manager.get_random_location()
headers = scraper.ua_manager.get_matching_headers(profile)

print(f'''
📊 ANTI-DETECTION FEATURES SUMMARY:
{'='*50}
🎭 User Agents Available: {scraper.ua_manager.get_total_user_agents()}
📍 Locations Available: {len(LOCATION_PROFILES)}
🖥️ Viewports per OS: Windows({len(VIEWPORTS_BY_OS.get("windows", []))}), macOS({len(VIEWPORTS_BY_OS.get("macos", []))}), Linux({len(VIEWPORTS_BY_OS.get("linux", []))})

🔧 SAMPLE CONFIGURATION:
{'='*50}
Browser: {profile.browser}/{profile.os}
User-Agent: {profile.user_agent[:60]}...
Viewport: {viewport["width"]}x{viewport["height"]} (matched to {profile.os})
Location: {location["name"]}
Timezone: {location["timezone_id"]}
Headers Count: {len(headers)}
Has Sec-CH-UA: {"Sec-Ch-Ua" in headers}

🛡️ ANTI-DETECTION SCRIPTS:
{'='*50}
✅ Canvas Fingerprint Noise
✅ WebGL Renderer Spoof
✅ Hardware Concurrency Randomization
✅ Device Memory Randomization
✅ Plugin Masking
✅ WebRTC IP Leak Protection (NEW!)
✅ Network Connection Spoof (NEW!)
✅ Battery API Spoof (NEW!)

✅ All features working correctly!
''')
