import requests
import re
import base64
import json
import pandas as pd
from bs4 import BeautifulSoup
import os

def decrypt_price_history(encrypted, key):
    decoded = base64.b64decode(encrypted)
    result = ""
    for i in range(len(decoded)):
        result += chr(decoded[i] ^ ord(key[i % len(key)]))
    return result

def scrape_price_history(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

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
        raise Exception("Encrypted data not found")

    encrypted = encrypted_match.group(1)

    # Extract key
    key_match = re.search(r"let CachedKey='([^']+)'", html)
    if not key_match:
        raise Exception("Key not found")

    key = key_match.group(1)

    # Decrypt JSON
    decrypted_json = decrypt_price_history(encrypted, key)
    data = json.loads(decrypted_json)

    # Extract price history
    history = data["History"]["Price"]

    df = pd.DataFrame(history)
    df["x"] = pd.to_datetime(df["x"])
    df.rename(columns={"x": "Date", "y": "Price"}, inplace=True)

    return df


# ----------------------------- #
# 🔥 USER INPUT
# ----------------------------- #

url = input("Paste pricehistory.app product URL: ").strip()

if "pricehistory.app" not in url:
    raise ValueError("Invalid pricehistory.app URL")

df = scrape_price_history(url)

print(df.tail())

# Save CSV safely
os.makedirs("raw", exist_ok=True)
df.to_csv("raw/flipkart_historical_prices.csv", index=False)

print("\nSaved as raw/flipkart_historical_prices.csv")
