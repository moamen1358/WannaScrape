# Web Scraper

Production-ready web scraper with advanced anti-detection features. Extract clean article content from any website while bypassing bot detection systems.

## Features

- **50+ User Agents**: Rotating browser fingerprints (Chrome, Firefox, Safari, Edge)
- **30+ Locations**: Geographic profiles with matching timezones and locales
- **Anti-Detection Suite**: Canvas noise, WebGL spoofing, WebRTC protection
- **CAPTCHA Solving**: Support for 2captcha and Capsolver services
- **Proxy Rotation**: Smart proxy management with health tracking
- **Human Behavior**: Realistic mouse movements and scrolling
- **Session Persistence**: Cookie management for returning visitor simulation
- **Dual Interface**: CLI + REST API

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/website_scraper.git
cd website_scraper

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### CLI Usage

```bash
# Scrape an article
python main.py scrape https://example.com/article

# Scrape with visible browser (for debugging)
python main.py scrape https://example.com/article --no-headless

# Search for text source
python main.py search "Breaking news about technology"

# Start API server
python main.py serve --port 8000

# Show help
python main.py --help
```

### API Usage

```bash
# Start the server
python main.py serve

# Scrape an article
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'

# Check health
curl http://localhost:8000/health

# Get statistics
curl http://localhost:8000/stats
```

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `SCRAPER_HEADLESS` | `true` | Run browser in headless mode |
| `SCRAPER_CAPTCHA_ENABLED` | `false` | Enable CAPTCHA solving |
| `SCRAPER_PROXY_ENABLED` | `false` | Enable proxy rotation |
| `SCRAPER_MAX_REQUESTS_PER_HOUR` | `60` | Rate limit per domain |

## Project Structure

```
website_scraper/
├── app/
│   ├── core/                   # Core scraping logic
│   │   ├── scraper.py          # Main WebScraper class
│   │   ├── captcha_solver.py   # CAPTCHA detection and solving
│   │   ├── browser_manager.py  # Browser setup and anti-detection
│   │   └── content_extractor.py # Article extraction
│   ├── api/                    # REST API
│   │   └── scraper_api.py      # FastAPI endpoints
│   ├── cli/                    # Command-line interface
│   │   └── commands.py         # Typer CLI commands
│   ├── config/                 # Configuration
│   │   ├── settings.py         # Pydantic settings
│   │   └── constants.py        # Anti-detection scripts
│   ├── logging/                # Logging system
│   │   └── logger.py           # Unified logging
│   ├── services/               # Advanced features
│   │   ├── user_agents.py      # User agent profiles
│   │   └── advanced_anti_detection.py
│   └── utils/                  # Utilities
│       ├── cloudflare.py       # Cloudflare bypass
│       ├── human_behavior.py   # Human simulation
│       ├── proxy_manager.py    # Proxy management
│       └── helpers.py          # Helper functions
├── config/
│   ├── config.json.example     # Example configuration
│   └── proxies.txt             # Proxy list (one per line)
├── data/                       # Runtime data (gitignored)
│   ├── logs/                   # Log files
│   ├── screenshots/            # Failure screenshots
│   └── sessions/               # Browser sessions
├── main.py                     # Entry point
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Docker

```bash
# Build and run
docker-compose up --build

# Or manually
docker build -t web-scraper .
docker run -p 8000:8000 web-scraper
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with feature list |
| `/stats` | GET | Scraping statistics |
| `/scrape` | POST | Scrape an article |
| `/search` | POST | Search for text source |

### Request Examples

**Scrape Article:**
```json
POST /scrape
{
  "url": "https://example.com/article",
  "headless": true
}
```

**Search Source:**
```json
POST /search
{
  "text": "Article text to find source",
  "num_results": 5
}
```

## Anti-Detection Features

| Feature | Description |
|---------|-------------|
| Canvas Fingerprint Noise | Randomizes canvas fingerprint |
| WebGL Spoofing | Spoofs GPU vendor/renderer |
| WebRTC Protection | Prevents IP leaks |
| Navigator Patches | Hardware/memory spoofing |
| Stealth Mode | Hides automation indicators |
| Human Behavior | Realistic mouse and scroll |

## License

MIT License

## Contributing

Contributions are welcome! Please read the contributing guidelines first.
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
