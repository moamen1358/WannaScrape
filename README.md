# WannaScrape

WannaScrape is a Python web scraper for article content with anti-detection
and a plugin-based bot-detection system. It extracts clean article text
from arbitrary websites while detecting and routing around common bot
protection products (Cloudflare, Akamai, PerimeterX, DataDome, reCAPTCHA,
hCaptcha).

The scraper is delivered as both a CLI and a FastAPI HTTP service. It
ships with a Playwright-based browser, fingerprint rotation, cookie-banner
dismissal, optional CAPTCHA solving, optional proxy rotation, and
Prometheus metrics.

## Capabilities

- Fingerprint rotation across 10 consistent browser profiles (user-agent,
  viewport, platform, WebGL, hardware all aligned)
- 30+ geographic profiles with matching timezones and locales
- Anti-detection: canvas noise, WebGL spoofing, WebRTC leak protection,
  navigator-property patches
- Human-behavior simulation with Bezier-curve mouse movement and three
  speed modes (`fast` ~0.2 s, `normal` ~3-5 s, `stealth` ~5-7 s)
- Bot-detection plugins for Cloudflare, Akamai, PerimeterX, DataDome,
  reCAPTCHA, hCaptcha; auto-discovered via the registry
- CAPTCHA solving via 2captcha or Capsolver
- Cookie-banner dismissal for OneTrust, Cookiebot, Osano, TrustArc,
  Quantcast, Amazon SP, plus 30 generic selectors
- Proxy rotation with health tracking (file-based, rotating-URL, or
  inline proxy list)
- Tracker and resource blocking, early HTML snapshots before
  JS-induced page wipes
- Scraped articles auto-saved to `data/scraped/` as JSON (configurable,
  `--no-save` to disable)
- Cookie persistence for returning-visitor simulation
- Optional API-key authentication, structured JSON logging, Prometheus
  metrics endpoint

## Installation

```bash
git clone https://github.com/moamen1358/WannaScrape.git
cd WannaScrape

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

For a containerized run:

```bash
docker compose up -d
docker compose logs -f
```

## CLI

```bash
# Scrape a single article (auto-saved to data/scraped/)
python main.py scrape https://example.com/article

# Visible browser for debugging
python main.py scrape https://example.com/article --no-headless

# Skip auto-save
python main.py scrape https://example.com --no-save

# JSON output
python main.py scrape https://example.com -o json

# Custom save directory
python main.py scrape https://example.com --save-dir output/articles

# Start the HTTP server
python main.py serve --port 8000

# Show statistics
python main.py stats
```

## HTTP API

```bash
python main.py serve

# Health
curl http://localhost:8000/health

# Scrape (with API key if SCRAPER_API_KEY is set)
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"url": "https://example.com/article", "company_name": "Example Corp"}'

# Locate the source of a text fragment
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"text": "sample text to find source", "num_results": 3}'

# Statistics
curl http://localhost:8000/stats
```

Response shape:

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

## Configuration

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `SCRAPER_HEADLESS` | `true` | Run browser in headless mode |
| `SCRAPER_API_KEY` | unset | API key for HTTP authentication |
| `SCRAPER_PROXY_ENABLED` | `false` | Enable proxy rotation |
| `SCRAPER_CAPTCHA_ENABLED` | `false` | Enable CAPTCHA solving |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `console` | `console` or `json` |

Advanced settings live in `config/config.json`. Notable keys:

| Section | Key | Default | Description |
|---|---|---|---|
| `fingerprint` | `enabled` | `true` | Rotate browser fingerprints |
| `fingerprint` | `rotate_per_request` | `true` | New fingerprint per request |
| `human_behavior` | `speed` | `fast` | `fast`, `normal`, `stealth` |
| `cookie_dismisser` | `enabled` | `true` | Auto-dismiss cookie banners |
| `cookie_dismisser` | `aggressive` | `false` | Try reject/close if accept fails |
| `browser` | `slow_mo` | `20` | Milliseconds between browser actions |
| `proxies` | `rotating_proxy_url` | `""` | URL for rotating-proxy service |
| `proxies` | `proxy_list` | `[]` | Inline list of proxy URLs |

## Project structure

```
WannaScrape/
├── app/
│   ├── api/                # FastAPI endpoints
│   ├── cli/                # Typer CLI commands
│   ├── config/             # Settings, constants
│   ├── core/               # Main scraper logic
│   │   ├── scraper.py
│   │   ├── browser_manager.py
│   │   ├── content_extractor.py    # Trafilatura plus fallback
│   │   ├── fingerprint_manager.py
│   │   ├── cookie_dismisser.py
│   │   ├── captcha_solver.py
│   │   ├── rate_limiter.py
│   │   ├── session_manager.py
│   │   └── exceptions.py
│   ├── detections/         # Bot-detection plugin system
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── handler.py
│   │   ├── cloudflare.py
│   │   ├── akamai.py
│   │   ├── perimeterx.py
│   │   ├── datadome.py
│   │   ├── recaptcha.py
│   │   └── hcaptcha.py
│   ├── logging/
│   ├── monitoring/         # Prometheus metrics
│   ├── services/           # Anti-detection, user agents
│   └── utils/
├── config/                 # JSON config, proxies
├── data/
│   ├── scraped/            # Auto-saved article JSON
│   ├── logs/scrapes/
│   ├── screenshots/        # Failure captures
│   └── sessions/
├── tests/                  # 120 unit tests
├── main.py                 # CLI entry point
├── Dockerfile
└── docker-compose.yml
```

## Tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=app --cov-report=html
pytest tests/test_api.py -v
```

## Logging

Per-scrape logs land in `data/logs/scrapes/` named
`YYYY-MM-DD_HHMMSS_host.log`. Set `LOG_FORMAT=json` for structured
production logging.

## Built on

[Playwright](https://playwright.dev/) for browser automation,
[Trafilatura](https://github.com/adbar/trafilatura) for article
extraction, [FastAPI](https://fastapi.tiangolo.com/) for the HTTP
server, [Typer](https://typer.tiangolo.com/) for the CLI.

## License

MIT.
