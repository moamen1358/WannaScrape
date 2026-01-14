# Website Scraper & API (Ultimate Anti-Detection Edition)

Production-ready article scraper and FastAPI service designed to extract clean content from dynamic websites while avoiding bot detection. Features **comprehensive anti-detection suite**, **advanced fingerprint spoofing**, **intelligent human behavior simulation**, **domain-level rate limiting**, **session persistence**, and **advanced proxy management**.

## 🆕 Latest Updates (January 14, 2026)

### 🛡️ Advanced Anti-Detection Suite (NEW)
- **Audio Fingerprint Spoofing**: Defeats AudioContext-based fingerprinting
- **Font Enumeration Spoofing**: Randomizes detected system fonts
- **ClientRects Noise**: Adds imperceptible noise to element measurements
- **Performance API Noise**: Defeats timing-based detection methods
- **Date/Time Precision Reduction**: Prevents high-resolution timing attacks
- **Permissions API Spoofing**: Returns realistic permission states
- **Media Devices Spoofing**: Fake camera/microphone enumeration
- **Document Visibility Spoofing**: Always reports as visible (not hidden/automated)

### 🚦 Domain-Level Rate Limiting (NEW)
- **Per-Domain Tracking**: Monitors requests per domain per hour (default: 30/hr)
- **Auto-Throttling**: Automatically delays when approaching limits
- **Smart Delays**: Scales delay based on request frequency
- **Prevents IP Blocks**: Avoids triggering server-side rate limiting

### 🍪 Session Persistence (NEW)
- **Cookie Management**: Saves/restores browser sessions per domain
- **localStorage Persistence**: Maintains client-side storage
- **Returning Visitor Simulation**: Appears as legitimate returning user
- **Sessions Directory**: All sessions saved in `/sessions/` folder

### 🔄 Enhanced Proxy Management (NEW)
- **Retry with Rotation**: Automatically switches proxy on failure
- **Health Tracking**: Advanced failure counting with cooldown periods
- **Success Marking**: Resets failure count on successful requests
- **Smart Selection**: Avoids recently used and failed proxies

### 🧪 Anti-Detection Testing (NEW)
- **Bot Detection Test Suite**: Automated testing against detection services
- **Challenging Sites Testing**: Tests against Cloudflare, DataDome, PerimeterX
- **Fingerprint Validation**: Verifies canvas, WebGL, and other fingerprints
- **Success Rate Monitoring**: Tracks effectiveness over time

### 🎭 Enhanced User Agent System
- **55+ Modern User Agents**: Chrome, Firefox, Safari, Edge across Windows/Mac/Linux
- **Consistent Fingerprinting**: Matching viewport, headers, and capabilities
- **OS-Specific Profiles**: Realistic combinations of OS and browser versions
- **Geographic Profiles**: 30+ global locations with matching timezones/locales

## Key Features

### 🛡️ Ultimate Anti-Detection Protection
| Feature | Status | Impact | Description |
|---------|--------|--------|-------------|
| Canvas Fingerprint Noise | ✅ | **Critical** | Injects imperceptible noise to randomize fingerprint |
| WebGL Vendor/Renderer Spoof | ✅ | **Critical** | Spoofs GPU info (NVIDIA/Intel/AMD) |
| Audio Context Spoofing | ✅ **NEW** | **High** | Defeats audio fingerprinting |
| Font Enumeration Spoofing | ✅ **NEW** | **High** | Randomizes detected fonts |
| ClientRects Noise | ✅ **NEW** | **Medium** | Adds noise to element measurements |
| Performance API Noise | ✅ **NEW** | **Medium** | Prevents timing-based detection |
| User-Agent Rotation | ✅ | **High** | 55+ modern browser fingerprints |
| Human Behavior Simulation | ✅ | **Critical** | Mouse, scroll, realistic delays |
| Stealth Mode | ✅ | **Critical** | Playwright-stealth integration |
| Session Persistence | ✅ **NEW** | **High** | Cookie/localStorage management |

### 🚦 Smart Request Management
| Feature | Status | Description |
|---------|--------|-------------|
| Domain-Level Rate Limiting | ✅ **NEW** | Tracks requests per domain (30/hr default) |
| Proxy Health Tracking | ✅ | Auto-cooldown for failed proxies |
| Retry with Rotation | ✅ **NEW** | Switches proxy on failure |
| Smart Delays | ✅ | Bell-curve distribution, scales with frequency |
| Resource Blocking | ✅ | Blocks images/media to save bandwidth |

### 🔍 Advanced Debugging & Monitoring
| Feature | Status | Description |
|---------|--------|-------------|
| Screenshot on Failure | ✅ | PNG + JSON metadata capture |
| Error Classification | ✅ | Identifies ban types and provides recommendations |
| Success Rate Tracking | ✅ | Monitors effectiveness over time |
| Anti-Detection Testing | ✅ **NEW** | Test suite against bot detection services |
| Detailed Logging | ✅ | Comprehensive session logs with context |

## Project Structure

```
website_scraper/
├── app/
│   ├── services/
│   │   ├── scraper.py                  # Core scraper with anti-detection suite
│   │   ├── advanced_anti_detection.py  # 🆕 Advanced fingerprint spoofing
│   │   ├── user_agents.py              # 🆕 55+ user agent profiles
│   │   ├── advanced_logging.py         # 🆕 Comprehensive session logging
│   │   └── news_search.py              # Google News RSS searcher
│   └── api/
│       ├── scraper_api.py              # FastAPI endpoint for scraping
│       └── search_api.py               # FastAPI endpoint for news search
├── config/
│   ├── config.json                     # Your configuration (gitignored)
│   ├── config.json.example             # Example configuration
│   └── proxies.txt                     # Your proxy list (gitignored)
├── sessions/                           # 🆕 Saved browser sessions (gitignored)
├── logs/                               # Log files (gitignored)
├── screenshots/                        # Failure screenshots (gitignored)
├── test_antidetection.py               # 🆕 Anti-detection test suite
├── test_single_url.py                  # Single URL testing script
├── RECOMMENDATIONS.md                  # 🆕 Advanced setup guide
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── run_api.sh
```

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

2. **Configure**:
   ```bash
   cp config/config.json.example config/config.json
   # Edit config/config.json with your settings
   # Add proxies to config/proxies.txt (format: IP:PORT:USER:PASS)
   ```

## Configuration (`config/config.json`)

```json
{
    "proxies": {
        "enabled": true,
        "proxy_file": "proxies.txt"
    },
    "browser": {
        "headless": true,
        "slow_mo": 200,
        "timeout": 60000
    },
    "rate_limiting": {
        "max_requests_per_domain_per_hour": 30,
        "min_delay_between_requests": 5,
        "max_delay_between_requests": 15,
        "cooling_period_after_ban": 300
    },
    "anti_detection": {
        "min_request_interval": 5,
        "simulate_human_behavior": true,
        "randomize_viewport": true,
        "randomize_timezone": true,
        "inject_fingerprint_noise": true,
        "block_resources": ["image", "media", "font"],
        "use_smart_user_agent_rotation": true,
        "log_user_agent_selection": true
    },
    "proxy_manager": {
        "min_proxy_interval": 30,
        "max_failures_before_cooldown": 3,
        "cooldown_seconds": 120
    }
}
```

## Running the API

### Local Development
```bash
# Start both APIs
./run_api.sh

# Or run individually
uvicorn app.api.scraper_api:app --host 0.0.0.0 --port 8000
uvicorn app.api.search_api:app --host 0.0.0.0 --port 8001
```

### Docker
```bash
docker-compose up -d
```

### Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| Scraper API | `http://localhost:8000` | Article extraction |
| Search API | `http://localhost:8001` | Google News search |

## API Usage

### Scrape a URL
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

**Response**:
```json
[{
    "title": "Article Title",
    "date": "2024-01-15",
    "source": "example.com",
    "text": "Full article content..."
}]
```

### Search Google News
```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "limit": 5}'
```

## Debugging Failed Scrapes

When scraping fails, check:

1. **Screenshots**: `screenshots/YYYY-MM-DD/` contains PNG + JSON metadata
2. **Logs**: `logs/scraper.log` has detailed error blocks:
   ```
   === BAN/BLOCK DETECTED ===
   URL: https://example.com
   Proxy: http://1.2.3.4:8080 (user: abc***)
   Error Type: access_denied
   Details: Access denied - IP or proxy may be blocked
   ===========================
   ```

3. **Error Types**:
   - `rate_limit`: Too many requests, increase delays
   - `access_denied`: IP/proxy blocked, rotate proxy
   - `bot_detection`: CAPTCHA triggered, slow down
   - `cloudflare_challenge`: Wait longer or use different proxy
   - `paywall`: Content requires subscription

## 🧪 Testing Anti-Detection

### Test Against Bot Detection Services
```bash
# Test your setup against popular detection sites
python test_antidetection.py --type detection

# Test against challenging protected sites
python test_antidetection.py --type challenging

# Test specific URL
python test_antidetection.py --url https://bot.sannysoft.com/
```

### Single URL Testing
```bash
# Test original functionality
python test_single_url.py https://example.com/article --no-headless --verbose
```

### Recommended Test Sites
| Site | Tests | Target Score |
|------|-------|--------------|
| [bot.sannysoft.com](https://bot.sannysoft.com/) | Automation detection | All green checks |
| [pixelscan.net](https://pixelscan.net/) | Fingerprint consistency | No red flags |
| [browserleaks.com/canvas](https://browserleaks.com/canvas) | Canvas fingerprint | Randomized values |
| [browserleaks.com/webgl](https://browserleaks.com/webgl) | WebGL fingerprint | Spoofed GPU info |
| [creepjs.com](https://abrahamjuliot.github.io/creepjs/) | Trust score | Grade B or better |

## Anti-Detection Features Explained

### 🎭 Advanced Fingerprint Spoofing
- **Canvas Noise**: Imperceptible pixel-level changes to fingerprint
- **WebGL Spoofing**: Randomized GPU renderer (NVIDIA/Intel/AMD variants)
- **Audio Context**: Noise injection in audio processing fingerprints
- **Font Detection**: Randomized system font availability
- **ClientRects**: Tiny noise in element positioning measurements
- **Performance API**: Timing variations to prevent timing attacks

### 🤖 Human Behavior Simulation  
- **Mouse Movement**: Bezier curves for natural cursor paths
- **Scrolling**: Reading-like patterns (150-400px chunks with pauses)
- **Delays**: Normal distribution (bell curve) not uniform random
- **Typing**: Variable keystroke timing with occasional "typos"
- **Focus Events**: Realistic tab focus/blur simulation

### 🚦 Intelligent Rate Limiting
- **Domain Tracking**: Separate counters for each domain
- **Frequency Scaling**: Longer delays as request count increases  
- **Exponential Backoff**: Progressive delays after failures
- **Time-based Recovery**: Counters reset after time windows

### 🍪 Session Management
- **Cookie Persistence**: Saves authentication and preference cookies
- **localStorage/sessionStorage**: Maintains client-side state
- **Fingerprint Consistency**: Same "browser" across visits
- **Session Rotation**: Occasionally starts fresh to avoid staleness

## ⚠️ Current Limitations & Next Steps

### Known Limitations
- **Hard Paywalls**: Cannot bypass subscription-only content (WSJ, FT, etc.)
- **Advanced CAPTCHAs**: Some hCaptcha/reCAPTCHA v3 may require solving
- **TLS/JA3 Fingerprinting**: Playwright's TLS signature may be detected by advanced WAFs
- **IP Reputation**: Without residential proxies, datacenter IPs will eventually get blocked

### 🚀 Recommended Upgrades (See RECOMMENDATIONS.md)
1. **🔴 CRITICAL**: Add residential proxy rotation (Bright Data, Smartproxy, etc.)
2. **🟡 HIGH**: Implement TLS fingerprint matching (curl_cffi, Camoufox)
3. **🟡 HIGH**: Add CAPTCHA solving service (2Captcha, CapSolver)
4. **🟢 MEDIUM**: Distribute scraping across multiple VPS instances
5. **🟢 MEDIUM**: Add request jittering with Pareto distribution

### Success Rate Targets
- **Without Proxies**: ~60-80% (datacenter IPs get blocked)
- **With Datacenter Proxies**: ~80-90% (some sites block datacenter IPs)  
- **With Residential Proxies**: ~95-98% (premium setup)
- **With Full Setup**: ~98%+ (enterprise-grade anti-detection)

## 📊 Monitoring & Analytics

Check these files for insights:
- `logs/scrape_sessions_*.jsonl` - Detailed session logs
- `screenshots/YYYY-MM-DD/` - Failure analysis screenshots  
- `sessions/` - Saved browser cookies and state
- Use `test_antidetection.py` for regular validation

---

*Last Updated: January 14, 2026*
