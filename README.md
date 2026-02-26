# 🕷️ WannaScrape

[![CI](https://github.com/moamen1358/Search_news_and_scrape_them/actions/workflows/ci.yml/badge.svg)](https://github.com/moamen1358/Search_news_and_scrape_them/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-ready web scraper with advanced anti-detection features and a plugin-based bot detection system. Extract clean article content from any website while automatically detecting and bypassing bot protection systems.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎭 **Fingerprint Rotation** | 10 realistic browser fingerprints with consistent UA ↔ viewport ↔ platform ↔ WebGL ↔ hardware profiles |
| 🌍 **30+ Locations** | Geographic profiles with matching timezones and locales |
| 🛡️ **Anti-Detection** | Canvas noise, WebGL spoofing, WebRTC protection, navigator patches |
| 🤖 **Human Behavior** | Bezier curve mouse movements, variable scrolling — fast / normal / stealth modes |
| 🔌 **Bot Detection Plugins** | Auto-detecting Cloudflare, Akamai, PerimeterX, DataDome, reCAPTCHA, hCaptcha |
| 🔐 **CAPTCHA Solving** | Support for 2captcha and Capsolver services |
| 🍪 **Cookie Banner Dismisser** | Auto-dismisses OneTrust, Cookiebot, Osano, TrustArc, Quantcast, Amazon SP + 30 generic selectors |
| 🔄 **Proxy Rotation** | Smart proxy management with health tracking — file-based, rotating URL, or proxy list |
| ⚡ **Speed Optimized** | Resource & tracker blocking, fast human behavior mode (~0.2s), reduced delays, early HTML snapshots |
| 💾 **Auto-Save Content** | Scraped articles saved to `data/scraped/` as JSON (configurable, `--no-save` to disable) |
| 💾 **Session Persistence** | Cookie management for returning visitor simulation |
| 📡 **Dual Interface** | CLI + REST API |
| 🔑 **API Authentication** | Optional API key protection |
| 📊 **Structured Logging** | JSON format option for production |
| 📈 **Prometheus Metrics** | Built-in monitoring and observability |

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/moamen1358/Search_news_and_scrape_them.git
cd Search_news_and_scrape_them

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: conda activate scraper_env

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Docker

```bash
# Build and run
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

## 📖 Usage

### CLI Commands

```bash
# Scrape an article (content auto-saved to data/scraped/)
python main.py scrape https://example.com/article

# Scrape with visible browser (for debugging)
python main.py scrape https://example.com/article --no-headless

# Scrape without saving content
python main.py scrape https://example.com --no-save

# JSON output format
python main.py scrape https://example.com -o json

# Save to custom directory
python main.py scrape https://example.com --save-dir output/articles

# Start API server
python main.py serve --port 8000

# Show statistics
python main.py stats

# Show version
python main.py version
```

### REST API

```bash
# Start the server
python main.py serve

# Health check (no auth required)
curl http://localhost:8000/health

# Scrape an article (with API key if configured)
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"url": "https://example.com/article", "company_name": "Example Corp"}'

# Search for text source
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"text": "sample text to find source", "num_results": 3}'

# Get statistics
curl http://localhost:8000/stats
```

### API Response Example

```json
[
  {
    "company_name": "Example Corp",
    "title": "Article Title",
    "date": "2026-01-15",
    "source": "https://example.com/article",
    "text": "Full article content...",
    "scrape_duration": 5.23,
    "user_agent_used": "Mozilla/5.0...",
    "location_used": "New York, USA",
    "final_url": "https://example.com/article"
  }
]
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPER_HEADLESS` | `true` | Run browser in headless mode |
| `SCRAPER_API_KEY` | `None` | API key for authentication (optional) |
| `SCRAPER_PROXY_ENABLED` | `false` | Enable proxy rotation |
| `SCRAPER_CAPTCHA_ENABLED` | `false` | Enable CAPTCHA solving |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | `console` | Log format (`console` or `json`) |

### Config File

Edit `config/config.json` for advanced settings:

```json
{
  "browser": {
    "headless": true,
    "slow_mo": 20,
    "timeout": 30000
  },
  "rate_limiting": {
    "min_delay_between_requests": 1,
    "max_delay_between_requests": 4
  },
  "fingerprint": {
    "enabled": true,
    "rotate_per_request": true
  },
  "human_behavior": {
    "speed": "fast"
  },
  "cookie_dismisser": {
    "enabled": true,
    "aggressive": false
  },
  "proxies": {
    "enabled": false,
    "proxy_file": "proxies.txt",
    "rotating_proxy_url": "",
    "proxy_username": "",
    "proxy_password": "",
    "proxy_list": []
  }
}
```

### Configuration Reference

| Section | Key | Default | Description |
|---------|-----|---------|-------------|
| `fingerprint` | `enabled` | `true` | Rotate browser fingerprints (UA, viewport, platform, WebGL, hardware) |
| `fingerprint` | `rotate_per_request` | `true` | Use a new fingerprint for each request |
| `human_behavior` | `speed` | `"fast"` | `"fast"` (~0.2s), `"normal"` (~3-5s), or `"stealth"` (~5-7s) |
| `cookie_dismisser` | `enabled` | `true` | Auto-dismiss cookie consent banners |
| `cookie_dismisser` | `aggressive` | `false` | Try reject/close buttons if accept fails |
| `browser` | `slow_mo` | `20` | Milliseconds between browser actions |
| `proxies` | `rotating_proxy_url` | `""` | URL for rotating proxy service (e.g., BrightData, Oxylabs) |
| `proxies` | `proxy_list` | `[]` | Inline list of proxy URLs |

## 📁 Project Structure

```
WannaScrape/
├── app/
│   ├── api/              # FastAPI endpoints
│   ├── cli/              # Typer CLI commands (--save, --save-dir)
│   ├── config/           # Settings, constants
│   ├── core/             # Main scraper logic
│   │   ├── scraper.py    # WebScraper class (orchestrator)
│   │   ├── browser_manager.py  # Browser setup, fingerprint integration, tracker blocking
│   │   ├── content_extractor.py # Trafilatura + fallback extraction
│   │   ├── fingerprint_manager.py # 🆕 10 realistic fingerprint profiles + rotation
│   │   ├── cookie_dismisser.py    # 🆕 Cookie banner auto-dismisser (30+ selectors)
│   │   ├── captcha_solver.py
│   │   ├── rate_limiter.py
│   │   ├── session_manager.py
│   │   └── exceptions.py # Custom exceptions
│   ├── detections/       # 🔌 Bot detection plugin system
│   │   ├── base.py       # BaseDetection abstract class
│   │   ├── registry.py   # Auto-discovery engine
│   │   ├── handler.py    # Interface for scraper.py
│   │   ├── cloudflare.py # Cloudflare WAF
│   │   ├── akamai.py     # Akamai Bot Manager
│   │   ├── perimeterx.py # PerimeterX (HUMAN)
│   │   ├── datadome.py   # DataDome
│   │   ├── recaptcha.py  # Google reCAPTCHA
│   │   └── hcaptcha.py   # hCaptcha
│   ├── logging/          # Custom logger
│   ├── monitoring/       # Prometheus metrics
│   ├── services/         # Anti-detection, user agents
│   └── utils/            # Helpers, human behavior (fast/normal/stealth)
├── config/               # JSON config, proxies
├── data/                 # Runtime data
│   ├── scraped/          # 💾 Auto-saved article content (JSON)
│   ├── logs/scrapes/     # Scrape logs
│   ├── screenshots/      # Failure screenshots
│   └── sessions/         # Browser sessions
├── docs/                 # Documentation
├── tests/                # Unit tests (120 tests)
├── main.py               # CLI entry point
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 🧪 Testing

```bash
# Run all tests (120 tests)
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

## 🔒 Security

- **API Key Authentication**: Set `SCRAPER_API_KEY` environment variable to enable
- **CORS**: Configured for cross-origin requests (customize in production)
- **Rate Limiting**: Built-in delays between requests
- **Data saved locally**: Scraped content saved to `data/scraped/` (use `--no-save` to disable)

## 📊 Anti-Detection Features

| Feature | Description |
|---------|-------------|
| 🎭 Fingerprint Rotation | 10 consistent profiles (UA ↔ viewport ↔ platform ↔ WebGL ↔ hardware), avoids last 3 used |
| 🖼️ Canvas Fingerprinting | Adds noise to canvas operations |
| 🎮 WebGL Spoofing | Randomizes renderer/vendor per fingerprint profile |
| 🌐 WebRTC Protection | Prevents IP leaks |
| 🧭 Navigator Patches | Hides webdriver property, consistent platform |
| 💻 Hardware Randomization | Per-fingerprint CPU cores, memory, device pixel ratio |
| 🖱️ Mouse Simulation | Bezier curves, tremor, variable speed |
| 📜 Scroll Simulation | Read/skim/back scroll patterns |
| 🎭 Behavior Modes | Fast (~0.2s), Normal (~3-5s), Stealth (~5-7s) |
| 🍪 Cookie Banner Dismissal | OneTrust, Cookiebot, Osano, TrustArc, Quantcast, Amazon SP + generics |
| 🚫 Tracker Blocking | Blocks google-analytics, facebook.net, hotjar, doubleclick, etc. |
| 📸 Early HTML Snapshot | Captures content before JS crashes can blank the page |
| 🔄 Multi-Strategy Fallback | domcontentloaded → load → networkidle with auto-retry |

## 📝 Logging

Logs are saved to `data/logs/scrapes/` with format:
```
2026-01-15_143535_example.com.log
```

Enable JSON logging for production:
```bash
LOG_FORMAT=json python main.py serve
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) - Browser automation
- [Trafilatura](https://github.com/adbar/trafilatura) - Article extraction
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Typer](https://typer.tiangolo.com/) - CLI framework
