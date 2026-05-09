# WannaScrape architecture

## Capabilities (full list)

- Fingerprint rotation across 11 consistent browser profiles
  (user-agent, viewport, platform, WebGL, hardware all aligned)
- 33 geographic profiles with matching timezones and locales
- Anti-detection: canvas noise, WebGL spoofing, WebRTC leak protection,
  navigator-property patches
- Human-behavior simulation with Bezier-curve mouse movement and three
  speed modes (`fast` ~1 s, `normal` ~3-5 s, `stealth` ~5-8 s)
- Bot-detection plugins for Cloudflare, Akamai, PerimeterX, DataDome,
  reCAPTCHA, hCaptcha; auto-discovered via the registry
- CAPTCHA solving via 2captcha or Capsolver
- Cookie-banner dismissal for OneTrust, Cookiebot, Osano, TrustArc,
  Quantcast, Amazon SP, plus 30 generic selectors
- Proxy rotation with health tracking (file-based, rotating-URL, or
  inline proxy list)
- Tracker and resource blocking, early HTML snapshots before
  JS-induced page wipes
- Cookie persistence for returning-visitor simulation
- Optional API-key authentication, structured JSON logging,
  Prometheus metrics endpoint

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `SCRAPER_API_KEY` | unset | API key for HTTP authentication; when unset the API is open |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `console` | `console` or `json` |
| `WANNASCRAPE_DATA_DIR` | `data` | Directory for scraped articles, logs, screenshots, sessions |
| `WANNASCRAPE_CONFIG_DIR` | `config` | Directory for `config.json` and proxy lists |

## config.json

Operational settings (headless, proxies, CAPTCHA, fingerprinting, rate
limits) live here, not in env vars. Notable keys:

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
