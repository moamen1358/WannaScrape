import requests
import json
import time

urls = [
    "https://news.google.com/rss/articles/CBMiiwFBVV95cUxQZE1NcVFpSmUtU3hHaWZIdnk3VEg2bWFVaXAxT2J5d2IxMGlrR19FZTFhQmU5SGVOdTZyWlVLTGx1QnlobDRNWmlMQTMycG5QX0xUQ1R6bkY2akszUGI2T0RicENwUHBNNVlFaHBsZ3NHcjZ0azlObUtlOE91MUZnbU9pc3JlM0RpQUNF?oc=5"
]

for url in urls:
    print(f"\n🚀 Sending request to Scraper API for: {url}")
    payload = {
        "url": url,
        "headless": False
    }

    try:
        start = time.time()
        response = requests.post("http://localhost:8000/scrape", json=payload, timeout=120)
        duration = time.time() - start
        
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # API returns a list
            if isinstance(data, list) and len(data) > 0:
                result = data[0]
                if result.get("error"):
                    print(f"❌ API Error: {result['error']}")
                else:
                    print(f"✅ SUCCESS!")
                    print(f"Title: {result.get('title')}")
                    print(f"Source: {result.get('source')}")
                    print(f"Date: {result.get('date')}")
                    print(f"Text Length: {len(result.get('text', ''))} chars")
            else:
                print(f"⚠️ Unexpected response format: {data}")
        else:
            print(f"❌ Request failed: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")


