import requests
import re
import base64
import json
import pandas as pd
from bs4 import BeautifulSoup

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

    # Fetch webpage
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    html = response.text

    # Extract encrypted dataset
    encrypted_match = re.search(r'var PagePriceHistoryDataSet\s*=\s*"([^"]+)"', html)
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

    # Extract historical prices
    history = data["History"]["Price"]
    df = pd.DataFrame(history)
    df["x"] = pd.to_datetime(df["x"])
    df.rename(columns={"x": "Date", "y": "Price"}, inplace=True)
    return df


# ----------------------------- #
# 🔥 RUN FOR ANY PRODUCT HERE:
# ----------------------------- #

url = "https://pricehistory.app/p/apple-iphone-15-black-256-gb-olByzcG5"

df = scrape_price_history(url)

print(df)

# Save CSV
df.to_csv("raw/flipkart_historical_prices.csv", index=False)
print("\nSaved as historical_prices.csv")
