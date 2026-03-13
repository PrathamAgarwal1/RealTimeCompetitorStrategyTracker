import os
import requests
from urllib.parse import urlparse
from time import sleep
from datetime import datetime

API_URL = "https://django.prixhistory.com/api/product/history/updateFromSlug"

def extract_slug(u: str) -> str:
    parts = [p for p in urlparse(u).path.split("/") if p]
    return parts[1] if len(parts) >= 2 and parts[0] == "product" else parts[-1]

def fetch_amazon_price_history(product_url: str) -> dict:
    auth_token = os.getenv("AUTH_TOKEN")
    if not auth_token:
        return {"success": False, "error": "AUTH_TOKEN environment variable not set"}
        
    slug = extract_slug(product_url)
    sess = requests.Session()
    
    # 1) Load homepage & product to pick up any cookies/tokens
    try:
        for warmup_url in ["https://pricehistoryapp.com/", product_url]:
            sess.get(warmup_url, timeout=20)
    except Exception as e:
        return {"success": False, "error": f"Warmup failed: {str(e)}"}

    headers = {
        "name": "Amazon",
        "auth": auth_token,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin": "https://pricehistoryapp.com",
        "Referer": product_url,
        "X-Requested-With": "XMLHttpRequest",
    }
    data = {"slug": slug}

    payload = None
    for attempt in range(4):
        try:
            res = sess.post(API_URL, headers=headers, data=data, timeout=(10, 40))
            if res.status_code == 200:
                payload = res.json()
                break
            elif res.status_code in (429, 503):
                sleep(2 * (attempt + 1))
                continue
            elif res.status_code == 403:
                return {"success": False, "error": f"403 Forbidden. Body: {res.text}"}
            else:
                return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            if attempt == 3:
                return {"success": False, "error": f"Request failed: {str(e)}"}
            sleep(2)

    if not payload:
        return {"success": False, "error": "Gave up after retries"}

    hist = payload.get("history")
    if hist is None:
        return {"success": False, "error": "No 'history' in response."}

    formatted_data = []
    if isinstance(hist, dict):
        items = hist.items()
    else:
        items = []
        for x in hist:
             ts = x.get('ts') or x.get('timestamp')
             val = x.get('amount') or x.get('value')
             if ts and val is not None:
                 items.append((ts, val))
                 
    for k, v in items:
         try:
             if str(k).isnumeric():
                  num = float(k)
                  if num > 1e10: num = num / 1000.0
                  dt = datetime.fromtimestamp(num).isoformat()
             else:
                  dt = str(k)
         except:
             dt = str(k)
             
         formatted_data.append({
             "product_name": slug, 
             "url": product_url,
             "price": float(v),
             "rating": None,
             "review_text": None,
             "timestamp": dt,
             "source": "amazon_price_history"
         })

    return {"success": True, "product_name": slug, "url": product_url, "data": formatted_data}

