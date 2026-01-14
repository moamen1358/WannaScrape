#!/usr/bin/env python3
"""Test proxy connectivity."""

import requests
from pathlib import Path

def load_proxies(filepath="config/proxies.txt"):
    proxies = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) == 4:
                proxies.append({
                    "server": f"http://{parts[0]}:{parts[1]}",
                    "http": f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}",
                    "https": f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                })
    return proxies

def test_proxy(proxy, timeout=10):
    """Test a single proxy."""
    try:
        response = requests.get(
            "https://httpbin.org/ip",
            proxies={"http": proxy["http"], "https": proxy["https"]},
            timeout=timeout
        )
        if response.status_code == 200:
            ip = response.json().get("origin", "unknown")
            return True, ip
        return False, f"Status: {response.status_code}"
    except requests.exceptions.ProxyError as e:
        return False, "Proxy auth failed"
    except requests.exceptions.ConnectTimeout:
        return False, "Connection timeout"
    except requests.exceptions.ConnectionError as e:
        return False, "Connection refused"
    except Exception as e:
        return False, str(e)[:50]

def main():
    print("="*60)
    print("PROXY CONNECTIVITY TEST")
    print("="*60)

    proxies = load_proxies()
    print(f"Loaded {len(proxies)} proxies\n")

    working = 0
    for i, proxy in enumerate(proxies, 1):
        server = proxy["server"]
        print(f"[{i}/{len(proxies)}] Testing {server}...", end=" ", flush=True)

        success, result = test_proxy(proxy)

        if success:
            print(f"✅ OK (IP: {result})")
            working += 1
        else:
            print(f"❌ FAILED ({result})")

    print("\n" + "="*60)
    print(f"RESULT: {working}/{len(proxies)} proxies working")
    print("="*60)

    if working == 0:
        print("\n⚠️  No working proxies! Check:")
        print("   - Proxy credentials are correct")
        print("   - Proxies haven't expired")
        print("   - Your IP isn't blocked by the proxy provider")

if __name__ == "__main__":
    main()
