import cloudscraper
import json
import re

s = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
r = s.get("https://pricehistoryapp.com/product/apple-iphone-15-128-gb-black", timeout=20)
print("Status:", r.status_code)

html = r.text
match = re.search(
    r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>',
    html,
    re.DOTALL
)

if match:
    data = json.loads(match.group(1))
    props = data.get("props", {}).get("pageProps", {})
    product = props.get("ogProduct", {})
    
    print("\n=== Top-level pageProps keys ===")
    print(list(props.keys()))
    
    print("\n=== ogProduct keys ===")
    print(list(product.keys()))
    
    print("\n=== ogProduct (without history) ===")
    display = {k: v for k, v in product.items() if k != "history" and k != "similar_products" and k != "similar_deals" and k != "features"}
    print(json.dumps(display, indent=2, default=str)[:2000])
    
    print("\n=== History ===")
    history = product.get("history", {})
    print(f"Type: {type(history).__name__}")
    if isinstance(history, dict):
        items = list(history.items())
        print(f"Count: {len(items)}")
        if items:
            print(f"First 3: {items[:3]}")
            print(f"Last 3: {items[-3:]}")
    elif isinstance(history, list):
        print(f"Count: {len(history)}")
        if history:
            print(f"First 3: {history[:3]}")
    else:
        print(f"Value: {history}")

    print("\n=== apiUrl ===")
    print(props.get("apiUrl"))
else:
    print("__NEXT_DATA__ not found!")
