# Website Scraper - Technical Report

## Overview

This document provides a comprehensive report of all tools, techniques, and features implemented in the website scraper, including recent additions.

---

## Table of Contents

1. [Anti-Detection Techniques](#1-anti-detection-techniques)
2. [Browser Fingerprint Spoofing](#2-browser-fingerprint-spoofing)
3. [Network & Proxy Management](#3-network--proxy-management)
4. [Human Behavior Simulation](#4-human-behavior-simulation)
5. [User Agent Management](#5-user-agent-management)
6. [TLS/JA3 Fingerprint Matching](#6-tlsja3-fingerprint-matching-new)
7. [Rate Limiting & Request Spacing](#7-rate-limiting--request-spacing)
8. [Cloudflare & Bot Detection Bypass](#8-cloudflare--bot-detection-bypass)
9. [Session Management](#9-session-management)
10. [Logging & Analytics](#10-logging--analytics)
11. [Recent Changes](#11-recent-changes)
12. [What's NOT Implemented](#12-whats-not-implemented)

---

## 1. Anti-Detection Techniques

### Summary Table

| Category | Techniques | Status |
|----------|-----------|--------|
| Browser Fingerprints | Canvas, WebGL, Audio, Fonts | Implemented |
| TLS Fingerprints | JA3 impersonation via curl_cffi | Implemented |
| User Agents | 50+ modern browsers | Implemented |
| Human Behavior | Mouse, scroll, typing simulation | Implemented |
| Proxy Management | Health tracking, rotation | Implemented |
| Rate Limiting | Per-domain throttling | Implemented |
| Session Persistence | Cookie/localStorage reuse | Implemented |

---

## 2. Browser Fingerprint Spoofing

### 2.1 Canvas Fingerprint Noise
**File:** `app/services/scraper.py`

Injects imperceptible noise into canvas rendering to randomize fingerprints.

```javascript
// Adds tiny random noise (imperceptible but changes fingerprint)
imageData.data[i] = Math.max(0, Math.min(255, imageData.data[i] + (Math.random() * 2 - 1)));
```

### 2.2 WebGL Fingerprint Spoofing
**File:** `app/services/scraper.py`

Randomizes GPU vendor/renderer information:
- NVIDIA GeForce GTX 1080/1660/RTX 2060/3070/3080
- Intel UHD Graphics 630/Iris Xe
- AMD Radeon RX 580/5700

### 2.3 Audio Fingerprint Spoofing
**File:** `app/services/advanced_anti_detection.py`

- Adds noise to AudioContext channel data
- Randomizes sample rates (44100, 48000, 96000 Hz)
- Spoofs analyser frequency data

### 2.4 Font Enumeration Spoofing
**File:** `app/services/advanced_anti_detection.py`

- Reports 14 common fonts (Arial, Courier, Georgia, etc.)
- Adds random "installed" fonts from pool
- Noise injection on font measurements

### 2.5 ClientRects Noise
**File:** `app/services/advanced_anti_detection.py`

Adds +/- 0.005 noise to bounding box coordinates to prevent fingerprinting.

### 2.6 Hardware Property Randomization
**File:** `app/services/scraper.py`

| Property | Randomized Values |
|----------|------------------|
| Hardware Concurrency | 4, 6, 8, 12, 16 cores |
| Device Memory | 4, 8, 16, 32 GB |
| Screen Dimensions | Offset by -30 to -40px |

### 2.7 Date/Time Precision Reduction
**File:** `app/services/advanced_anti_detection.py`

- `Date.now()` rounded to nearest 100ms
- `performance.now()` rounded to nearest 5ms
- Prevents timing-based fingerprinting

---

## 3. Network & Proxy Management

### 3.1 Proxy Manager
**File:** `app/services/scraper.py`

| Feature | Configuration |
|---------|--------------|
| Min Proxy Interval | 30 seconds |
| Max Failures Before Cooldown | 3 |
| Cooldown Duration | 120-180 seconds |
| Health Tracking | Per-proxy failure counts |

### 3.2 WebRTC IP Leak Prevention
**File:** `app/services/scraper.py`

- Forces TURN-only mode
- Removes ICE servers
- Prevents real IP exposure

### 3.3 Network Connection Spoofing
**File:** `app/services/scraper.py`

| Property | Randomized Values |
|----------|------------------|
| Connection Type | wifi, 4g, ethernet |
| Effective Type | 4g, 3g |
| Downlink Speed | 1-10 Mbps |
| RTT | 50-150ms |

### 3.4 Battery API Spoofing
**File:** `app/services/scraper.py`

- Random charging state
- Battery level: 50-100%
- Random charging/discharging times

---

## 4. Human Behavior Simulation

### 4.1 Mouse Movement
**File:** `app/services/scraper.py` & `app/services/advanced_anti_detection.py`

- 3-6 random mouse movements per page
- Bezier curve paths (natural movement)
- 15-40 steps per movement
- 50-300ms micro-pauses
- Avoids page edges (100px margin)

### 4.2 Scroll Behavior
**File:** `app/services/scraper.py`

- Scrolls in 100-400px chunks (reading pattern)
- 300-1200ms pauses between scrolls
- 40% chance to scroll back up
- Max scroll: 60% of page or 3000px

### 4.3 Typing Simulation
**File:** `app/services/advanced_anti_detection.py`

- 3% typo rate with correction
- 50-150ms per character
- 2x delay after punctuation
- 5% chance of "thinking" pauses

### 4.4 Delay Distribution
**File:** `app/services/scraper.py`

Uses Gaussian (bell curve) distribution for natural timing variation.

---

## 5. User Agent Management

### 5.1 Browser Coverage
**File:** `app/services/user_agents.py`

| Browser | OS | Versions | Weight |
|---------|-----|----------|--------|
| Chrome | Windows | 119-126 | 35% |
| Chrome | macOS | 119-126 | 15% |
| Chrome | Linux | 119-126 | 5% |
| Firefox | Windows | 120-125 | 8% |
| Firefox | macOS | 120-125 | 5% |
| Safari | macOS | 16.6-17.3 | 12% |
| Edge | Windows | 119-122 | 12% |
| Opera | Windows/macOS | 105-106 | 6% |

**Total: 50+ unique user agents**

### 5.2 Consistent Header Matching
- Sec-CH-UA matches browser version
- Sec-CH-UA-Platform matches OS
- Accept-Language varies by region

### 5.3 Viewport Profiles
**OS-Specific Viewports:**

| OS | Resolutions |
|----|------------|
| Windows | 1920x1080, 1366x768, 1536x864, 2560x1440 |
| macOS | 1440x900, 1680x1050, 2560x1440, 2880x1800 |
| Linux | 1920x1080, 1366x768, 2560x1440, 3840x2160 |

---

## 6. TLS/JA3 Fingerprint Matching (NEW)

### 6.1 Overview
**File:** `app/services/tls_client.py`

Uses `curl_cffi` to impersonate real browser TLS fingerprints.

### 6.2 Why It Matters

| Without TLS Spoofing | With TLS Spoofing |
|---------------------|-------------------|
| Python TLS fingerprint detectable | Browser-like TLS fingerprint |
| Easily flagged by Cloudflare/Akamai | Appears as legitimate browser |

### 6.3 Supported Browser Fingerprints

| Browser | Versions |
|---------|----------|
| Chrome | 99, 100, 101, 104, 107, 110, 116, 119, 120 |
| Edge | 99, 101 |
| Safari | 15.3, 15.5, 17.0 |

### 6.4 Weighted Distribution
- Chrome 120: 30% (most common)
- Chrome 119: 20%
- Chrome 116: 10%
- Edge/Safari: 10% each
- Others: 2-5%

### 6.5 Usage
```python
from app.services.tls_client import tls_get

response = tls_get(url, headers=headers, proxies=proxy)
print(response.impersonation)  # "chrome120"
```

---

## 7. Rate Limiting & Request Spacing

### 7.1 Domain Rate Limiter
**File:** `app/services/advanced_anti_detection.py`

| Setting | Value |
|---------|-------|
| Max Requests/Domain/Hour | 30 |
| Min Delay Between Requests | 5 seconds |
| Max Delay Between Requests | 15 seconds |
| Cooling Period After Ban | 300 seconds |

### 7.2 Dynamic Delay Scaling
- Adds 2 extra seconds per request over 10/hour
- Separate tracking per domain
- Auto-cleanup of old request timestamps

---

## 8. Cloudflare & Bot Detection Bypass

### 8.1 Challenge Detection
**File:** `app/services/scraper.py`

**DOM Selectors Checked:**
- `#challenge-running`
- `#cf-challenge-running`
- `.cf-browser-verification`
- `#cf-hcaptcha-container`
- `.cf-turnstile`

**Title Patterns:**
- "Just a Moment"
- "Checking your browser"
- "Attention Required"
- "Please Wait"

### 8.2 Wait Mechanism
- 45-second extended timeout
- Polls every 3 seconds for completion
- Logs wait time and outcome

### 8.3 Playwright Stealth
**File:** `app/services/scraper.py`

- Patches `navigator.webdriver`
- Fake plugin list injection
- Language randomization
- Chrome automation flag removal

**Browser Launch Args:**
```
--disable-blink-features=AutomationControlled
--disable-dev-shm-usage
--no-sandbox
--disable-web-security
```

---

## 9. Session Management

### 9.1 Session Persistence
**File:** `app/services/advanced_anti_detection.py`

- Saves cookies/localStorage per domain
- 80% chance to reuse saved sessions
- Appears as returning visitor
- Stored in `sessions/` directory

---

## 10. Logging & Analytics

### 10.1 Advanced Scrape Logger
**File:** `app/services/advanced_logging.py`

**Tracked Metrics:**
- Session ID
- Browser fingerprint details
- Timing breakdown (browser launch, page load, CF wait, extraction)
- Content metrics (HTML size, word count)
- Popup interactions
- Error classification

### 10.2 Enterprise Logger
**File:** `app/services/enterprise_logging.py`

- Structured JSON logging
- ELK/Loki/Datadog compatible
- Correlation IDs for tracing
- Async non-blocking writes
- 30-day retention with gzip compression

---

## 11. Recent Changes

### 11.1 TLS/JA3 Fingerprint Implementation (Latest)

**Files Modified:**
| File | Change |
|------|--------|
| `app/services/tls_client.py` | NEW - TLS fingerprint client |
| `app/services/news_search.py` | Integrated TLS client |
| `requirements.txt` | Added `curl_cffi>=0.7.0` |
| `explain.md` | Documentation |

**Impact:**
- HTTP requests now use browser-like TLS fingerprints
- Significantly reduces detection by advanced anti-bot systems
- Automatic rotation between Chrome, Edge, Safari fingerprints

---

## 12. What's NOT Implemented

### 12.1 CAPTCHA Solving (Requires Paid Service)
- Would need 2Captcha or Anti-Captcha API
- Cost: ~$2-3 per 1000 CAPTCHAs
- Currently: Detection only, no solving

### 12.2 Distributed Scraping (Architecture Change)
- Would need Celery + Redis/RabbitMQ
- Adds significant complexity
- Only needed for large-scale operations

### 12.3 Residential Proxy Integration
- Would need subscription to residential proxy service
- Datacenter proxies are more detectable

---

## Architecture Diagram

```
                                    +------------------+
                                    |   Config JSON    |
                                    +--------+---------+
                                             |
+----------------+                           v
|  News Search   |    +------------------------------------------+
|  (RSS Feed)    |--->|              TLS Client                  |
+----------------+    |  (curl_cffi - Browser TLS Fingerprints)  |
                      +------------------------------------------+
                                             |
                                             v
+----------------+    +------------------------------------------+
|   Scraper      |--->|           Playwright Browser             |
|   (Main)       |    |  + Stealth Patches                       |
+----------------+    |  + Anti-Detection Scripts                |
        |             +------------------------------------------+
        |                            |
        v                            v
+----------------+    +------------------------------------------+
| User Agent     |    |        Advanced Anti-Detection           |
| Manager        |    |  - Canvas/WebGL/Audio Fingerprints      |
| (50+ agents)   |    |  - Human Behavior Simulation            |
+----------------+    |  - Rate Limiting                         |
        |             |  - Session Management                    |
        v             +------------------------------------------+
+----------------+                   |
| Proxy Manager  |                   v
| (Health Track) |    +------------------------------------------+
+----------------+    |           Logging System                 |
                      |  - Advanced Logger                       |
                      |  - Enterprise Logger (JSON/ELK)          |
                      +------------------------------------------+
```

---

## Files Overview

| File | Purpose | Lines |
|------|---------|-------|
| `app/services/scraper.py` | Main scraper with anti-detection | ~1400 |
| `app/services/advanced_anti_detection.py` | Fingerprint scripts, rate limiting | ~500 |
| `app/services/user_agents.py` | 50+ user agents, viewports | ~450 |
| `app/services/tls_client.py` | TLS fingerprint client | ~280 |
| `app/services/news_search.py` | Google News RSS search | ~260 |
| `app/services/advanced_logging.py` | Scrape analytics logger | ~350 |
| `app/services/enterprise_logging.py` | JSON/ELK logging | ~300 |
| `config/config.json` | Configuration settings | ~50 |

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| playwright | 1.56.0 | Browser automation |
| playwright-stealth | latest | Stealth patches |
| curl_cffi | >=0.7.0 | TLS fingerprint impersonation |
| trafilatura | 2.0.0 | Content extraction |
| requests | 2.32.5 | HTTP fallback |
| fastapi | 0.124.0 | API server |
| feedparser | 6.0.12 | RSS parsing |
| fake-useragent | 2.2.0 | User agent database |

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Install playwright browsers
playwright install chromium

# Run the scraper
python -m app.services.scraper --url "https://example.com"

# Run news search
python -m app.services.news_search --query "tech news"
```

---

*Report generated: January 2026*
*Total anti-detection techniques: 21 categories*
*Total user agents: 50+*
*Total location profiles: 30+*
