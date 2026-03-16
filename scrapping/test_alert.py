import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_alert():
    print("1. Subscribing to alerts for 'Test Product' at target price 1000...")
    res = requests.post(f"{BASE_URL}/api/subscribe", json={
        "email": "test@example.com",
        "product_name": "Test Product",
        "target_price": 1000.0
    })
    print("Subscribe response:", res.json())

    # We need to trigger the alert by calling an endpoint that runs `make_decision`
    # Let's hit the scrape or decision endpoint. 
    # But wait, make_decision loads from database. We can just manually call the make_decision logic 
    # or write a dummy test route in the app, or manually add to the raw_data.csv 
    # actually, the decision endpoint needs real data. Instead of full data, let's just make a POST to /api/decision
    # for a product we know. Let's list products first.
    products_res = requests.get(f"{BASE_URL}/api/products")
    products = products_res.json().get("products", [])
    if not products:
        print("No products found in DB. Test cannot proceed without data.")
        return
        
    prod = products[0]
    print(f"2. Subscribing to '{prod}' at target price 999999 (to guarantee it triggers)...")
    res = requests.post(f"{BASE_URL}/api/subscribe", json={
        "email": "test@example.com",
        "product_name": prod,
        "target_price": 999999.0
    })
    print("Subscribe response:", res.json())

    print(f"3. Triggering decision endpoint for '{prod}' to check price...")
    res = requests.post(f"{BASE_URL}/api/decision", json={"product_name": prod})
    print("Decision response:", res.json())

if __name__ == "__main__":
    test_alert()
