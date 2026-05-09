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

```bash
python main.py serve

# Scrape
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SCRAPER_API_KEY" \
  -d '{"url": "https://example.com/article", "company_name": "Example Corp"}'
```

Returns an article object with `title`, `text`, `date`, `source`,
`final_url`, plus diagnostic fields (`scrape_duration`,
`user_agent_used`, `location_used`).

Other endpoints: `GET /health`, `GET /stats`, `POST /search`.

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
