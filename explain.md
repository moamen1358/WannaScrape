# TLS/JA3 Fingerprint Implementation

## What Was Added

### 1. New TLS Client Module
**File:** `app/services/tls_client.py`

A new HTTP client that uses `curl_cffi` to impersonate real browser TLS fingerprints.

### 2. Updated Dependencies
**File:** `requirements.txt`

Added `curl_cffi>=0.7.0` - a library that can impersonate browser TLS/JA3 fingerprints.

### 3. Integrated into News Search
**File:** `app/services/news_search.py`

The news search now uses the TLS fingerprint client for all HTTP requests.

---

## Why This Matters

### The Problem: Python's Detectable TLS Fingerprint

When Python's `requests` library makes HTTPS connections, it creates a unique TLS fingerprint (called JA3) that is distinctly different from real browsers. Anti-bot systems can detect this:

```
Python requests TLS fingerprint: 771,49195-49196-52393-49199...(detectable as bot)
Chrome browser TLS fingerprint:  771,4865-4866-4867-49195...(legitimate browser)
```

### The Solution: curl_cffi

`curl_cffi` is a Python library built on curl that can impersonate real browser TLS fingerprints:

- **Chrome** (versions 99-120)
- **Firefox** (various versions)
- **Safari** (versions 15.3-17.0)
- **Edge** (versions 99-101)

---

## How It Works

### 1. Browser Impersonation
```python
from app.services.tls_client import tls_get

# Makes request with Chrome 120 TLS fingerprint
response = tls_get("https://example.com", headers=headers, proxies=proxy)
print(response.impersonation)  # "chrome120"
```

### 2. Automatic Rotation
The client randomly rotates between browser fingerprints:
- Chrome (weighted higher - most common browser)
- Edge
- Safari

### 3. Graceful Fallback
If `curl_cffi` isn't installed, it falls back to standard `requests`:
```python
if is_tls_client_available():
    response = tls_get(url, headers=headers)
else:
    response = requests.get(url, headers=headers)  # Fallback
```

---

## Available Browser Impersonations

| Browser | Versions Available |
|---------|-------------------|
| Chrome | 99, 100, 101, 104, 107, 110, 116, 119, 120 |
| Edge | 99, 101 |
| Safari | 15.3, 15.5, 17.0 |

---

## Usage Examples

### Basic GET Request
```python
from app.services.tls_client import tls_get

response = tls_get(
    "https://news.google.com/rss/search?q=test",
    headers={"User-Agent": "Mozilla/5.0..."},
    proxies={"http": "http://proxy:port"},
    timeout=30
)

print(response.status_code)
print(response.text)
print(response.impersonation)  # Shows which browser was impersonated
```

### Specific Browser
```python
from app.services.tls_client import tls_get

# Force Chrome 120 fingerprint
response = tls_get(url, impersonate="chrome120")
```

### POST Request
```python
from app.services.tls_client import tls_post

response = tls_post(
    "https://api.example.com/data",
    json={"key": "value"},
    headers=headers
)
```

### Using the Client Class
```python
from app.services.tls_client import TLSClient

client = TLSClient(impersonate="safari17_0")
response = client.get("https://example.com")
```

---

## Installation

```bash
pip install curl_cffi>=0.7.0
```

Or update all dependencies:
```bash
pip install -r requirements.txt
```

---

## Verification

To verify TLS fingerprint is working, check the logs:

```
DEBUG Using TLS fingerprint: chrome120
DEBUG Response status: 200, Content-Length: 45231, TLS: chrome120
```

---

## What Was NOT Implemented (Requires Paid Services)

1. **CAPTCHA Solving** - Requires 2Captcha/Anti-Captcha API keys (~$3/1000 solves)
2. **Distributed Scraping** - Requires infrastructure (Redis, Celery) - adds complexity

---

## Impact on Anti-Detection

| Before | After |
|--------|-------|
| Python `requests` with detectable TLS | Browser-like TLS fingerprint |
| Single fingerprint pattern | Rotating fingerprints (Chrome, Edge, Safari) |
| Easily flagged by Cloudflare/Akamai | Appears as legitimate browser traffic |

This significantly reduces detection by advanced anti-bot systems that fingerprint TLS handshakes.
