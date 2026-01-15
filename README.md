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

### Configuration

```bash
# Copy environment example
cp .env.example .env

# Copy config example
cp config/config.json.example config/config.json

# Edit settings as needed
```

### CLI Usage

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

### Test Script

```bash
# Quick test
python test_scrape.py https://example.com/article

# With visible browser and verbose output
python test_scrape.py https://example.com --no-headless -v
```

## Configuration

### Environment Variables

| Setting | Default | Description |
|---------|---------|-------------|
| `SCRAPER_HEADLESS` | `true` | Run browser in headless mode |
| `SCRAPER_CAPTCHA_ENABLED` | `false` | Enable CAPTCHA solving |
| `SCRAPER_PROXY_ENABLED` | `false` | Enable proxy rotation |
| `SCRAPER_MAX_REQUESTS_PER_HOUR` | `60` | Rate limit per domain |
| `TWOCAPTCHA_API_KEY` | - | 2Captcha API key |
| `CAPSOLVER_API_KEY` | - | Capsolver API key |

### Config File (`config/config.json`)

```json
{
    "proxies": {
        "enabled": false,
        "proxy_file": "proxies.txt"
    },
    "browser": {
        "headless": true,
        "slow_mo": 200,
        "timeout": 60000
    },
    "rate_limiting": {
        "max_requests_per_domain_per_hour": 30
    },
    "anti_detection": {
        "simulate_human_behavior": true,
        "inject_fingerprint_noise": true
    }
}
```

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
│   │   ├── news_search.py      # News search functionality
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
├── test_scrape.py              # Test script
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Docker

```bash
# Build and run with docker-compose
docker-compose up --build

# Or manually
docker build -t web-scraper .
docker run -p 8000:8000 -v $(pwd)/config:/app/config web-scraper
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with feature list |
| `/stats` | GET | Scraping statistics |
| `/scrape` | POST | Scrape an article |

### Request Examples

**Scrape Article:**
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "headless": true}'
```

**Response:**
```json
{
  "title": "Article Title",
  "date": "2024-01-15",
  "source": "example.com",
  "text": "Full article content..."
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

## Debugging

When scraping fails, check:

1. **Screenshots**: `data/screenshots/YYYY-MM-DD/` contains failure screenshots
2. **Logs**: `data/logs/` for detailed logs

## License

MIT License
