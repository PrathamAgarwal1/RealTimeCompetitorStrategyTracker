import requests
import re
import base64
import json
from bs4 import BeautifulSoup

def decrypt_price_history(encrypted, key):
    decoded = base64.b64decode(encrypted)
    result = ""
    for i in range(len(decoded)):
        result += chr(decoded[i] ^ ord(key[i % len(key)]))
    return result

def fetch_flipkart_price_history(url: str) -> dict:
    if "pricehistory.app" not in url:
        return {"success": False, "error": "Invalid pricehistory.app URL"}

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Extract encrypted dataset
        encrypted_match = re.search(
            r'var PagePriceHistoryDataSet\s*=\s*"([^"]+)"',
            html
        )
        if not encrypted_match:
             return {"success": False, "error": "Encrypted data not found on page"}

        encrypted = encrypted_match.group(1)

        # Extract key
        key_match = re.search(r"let CachedKey='([^']+)'", html)
        if not key_match:
             return {"success": False, "error": "Key not found on page"}

        key = key_match.group(1)

        # Decrypt JSON
        decrypted_json = decrypt_price_history(encrypted, key)
        data = json.loads(decrypted_json)

        # Extract price history
        history = data.get("History", {}).get("Price", [])
        
        # Product Name
        product_name = soup.title.string.replace("Price History", "").strip() if soup.title else "Flipkart Product"

        # Format output
        formatted_data = []
        for point in history:
            formatted_data.append({
                "product_name": product_name,
                "url": url,
                "price": float(point.get("y", 0)),
                "rating": None,
                "review_text": None,
                "timestamp": point.get("x"),
                "source": "flipkart_price_history"
            })

        return {"success": True, "product_name": product_name, "url": url, "data": formatted_data}

    except Exception as e:
        return {"success": False, "error": f"Failed to scrape: {str(e)}"}
