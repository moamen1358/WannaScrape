# WannaScrape

WannaScrape is a Python web scraper for article content with anti-detection
and a plugin-based bot-detection system. It extracts clean article text from
arbitrary websites while routing around Cloudflare, Akamai, PerimeterX,
DataDome, reCAPTCHA, and hCaptcha.

Delivered as both a CLI and a FastAPI HTTP service. Browser automation
runs on Playwright with rotating fingerprints, cookie-banner dismissal,
optional CAPTCHA solving, and optional proxy rotation.

## Install

```bash
git clone https://github.com/moamen1358/WannaScrape.git
cd WannaScrape
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Or with Docker:

```bash
docker compose up -d
```

## CLI

```bash
# Scrape one article (auto-saved to data/scraped/)
python main.py scrape https://example.com/article

# Visible browser for debugging
python main.py scrape https://example.com/article --no-headless

# Start the HTTP server
python main.py serve --port 8000
```

Run `python main.py --help` for the rest (`--no-save`, `-o json`,
`--save-dir`, `stats`, etc.).

## HTTP API

Start the server:

```bash
python main.py serve --port 8000
```

### POST `/scrape`

Request:

```json
{
  "url": "https://example.com/article",
  "company_name": "Example Corp"
}
```

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "company_name": "Example Corp"}'
```

Response (one article object per call):

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

### POST `/search`

Locate the source URL of a text fragment:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"text": "sample text to find source", "num_results": 3}'
```

### Other endpoints

| Method | Path | Returns |
|---|---|---|
| `GET` | `/health` | `{"status": "ok"}` |
| `GET` | `/stats` | Lifetime scrape counts and success rate |
| `GET` | `/metrics` | Prometheus metrics |

### Authentication (optional)

By default the API is open. If you set the `SCRAPER_API_KEY`
environment variable before starting the server, every endpoint then
requires the matching header:

```bash
curl ... -H "X-API-Key: $SCRAPER_API_KEY" ...
```

## Configuration

Three knobs you'll touch most:

| Where | Setting | Default |
|---|---|---|
| `SCRAPER_API_KEY` env | API key for HTTP authentication (when unset, API is open) | unset |
| `config/config.json` `human_behavior.speed` | `fast`, `normal`, `stealth` | `fast` |
| `config/config.json` `proxies.proxy_list` | Inline proxy URLs (or use `rotating_proxy_url`) | `[]` |

Full env-var list, every config key, project structure, test commands,
and the dependency rundown are in
[docs/architecture.md](docs/architecture.md).

## License

MIT.
