# 🕷️ WannaScrape

[![CI](https://github.com/moamen1358/Search_news_and_scrape_them/actions/workflows/ci.yml/badge.svg)](https://github.com/moamen1358/Search_news_and_scrape_them/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-ready web scraper with advanced anti-detection features and a plugin-based bot detection system. Extract clean article content from any website while automatically detecting and bypassing bot protection systems.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎭 **55+ User Agents** | Rotating browser fingerprints (Chrome, Firefox, Safari, Edge, Opera) |
| 🌍 **30+ Locations** | Geographic profiles with matching timezones and locales |
| 🛡️ **Anti-Detection** | Canvas noise, WebGL spoofing, WebRTC protection |
| 🤖 **Human Behavior** | Bezier curve mouse movements, variable scrolling (1-3 actions) |
| 🔌 **Bot Detection Plugins** | Auto-detecting Cloudflare, Akamai, PerimeterX, DataDome, reCAPTCHA, hCaptcha |
| 🔐 **CAPTCHA Solving** | Support for 2captcha and Capsolver services |
| 🔄 **Proxy Rotation** | Smart proxy management with health tracking |
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
# Scrape an article
python main.py scrape https://example.com/article

# Scrape with visible browser (for debugging)
python main.py scrape https://example.com/article --no-headless

# JSON output format
python main.py scrape https://example.com -o json

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
    "slow_mo": 50,
    "timeout": 30000
  },
  "rate_limiting": {
    "min_delay_between_requests": 5,
    "max_delay_between_requests": 15
  },
  "proxies": {
    "enabled": false,
    "proxy_file": "config/proxies.txt"
  }
}
```

## 📁 Project Structure

```
WannaScrape/
├── app/
│   ├── api/              # FastAPI endpoints
│   ├── cli/              # Typer CLI commands  
│   ├── config/           # Settings, constants
│   ├── core/             # Main scraper logic
│   │   ├── scraper.py    # WebScraper class
│   │   ├── browser_manager.py
│   │   ├── content_extractor.py
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
│   └── utils/            # Helpers, human behavior
├── config/               # JSON config, proxies
├── data/                 # Runtime data
│   ├── logs/scrapes/     # Scrape logs
│   ├── screenshots/      # Failure screenshots
│   └── sessions/         # Browser sessions
├── docs/                 # Documentation
├── tests/                # Unit tests
├── main.py               # CLI entry point
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 🧪 Testing

```bash
# Run all tests
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
- **No data persistence**: Article content is not stored by default

## 📊 Anti-Detection Features

| Feature | Description |
|---------|-------------|
| Canvas Fingerprinting | Adds noise to canvas operations |
| WebGL Spoofing | Randomizes renderer/vendor info |
| WebRTC Protection | Prevents IP leaks |
| Navigator Patches | Hides webdriver property |
| Hardware Randomization | Random CPU cores, memory |
| Mouse Simulation | Bezier curves, tremor, variable speed |
| Scroll Simulation | Read/skim/back scroll patterns |
| Behavior Types | READER, SKIMMER, SEARCHER modes |

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
