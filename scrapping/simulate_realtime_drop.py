import requests
import time
import os
import sys

# Ensure this matches the FastAPI server URL
BASE_URL = "http://127.0.0.1:8000"

def test_live_alert():
    # 1. Grab a product from the database
    try:
        products_res = requests.get(f"{BASE_URL}/api/products")
        products = products_res.json().get("products", [])
    except Exception as e:
        print(f"Could not connect to {BASE_URL}. Is the server running? Error: {e}")
        sys.exit(1)

    if not products:
        print("No products found in the database. Cannot run simulation.")
        sys.exit(1)
        
    prod = products[0]
    
    # Let's get the current price of the product
    try:
        decision_res = requests.post(f"{BASE_URL}/api/decision", json={"product_name": prod}).json()
        current_price = decision_res.get("current_price")
        if not current_price:
            print(f"Could not get current price for {prod}.")
            sys.exit(1)
    except Exception as e:
        print(f"Failed to fetch decision for {prod}. Error: {e}")
        sys.exit(1)

    print(f"=== Real-Time Simulation Started ===")
    print(f"Product: {prod}")
    print(f"Current true price: ₹{current_price}")
    
    # We will set a target price somewhat below the current price
    target_price = current_price - 3000
    
    # Prompt for email or just use the one provided via .env / known
    # Because we want to test the email sending, we subscribe the user
    user_email = os.getenv("EMAIL_SENDER", "dhruvildholakia10@gmail.com")
    
    print(f"Subscribing {user_email} to alerts for '{prod}' with Target Price: ₹{target_price}...")
    try:
        res = requests.post(f"{BASE_URL}/api/subscribe", json={
            "email": user_email,
            "product_name": prod,
            "target_price": target_price
        }).json()
        if not res.get("success"):
            print("Failed to subscribe.")
            sys.exit(1)
        print("Subscribed successfully!")
    except Exception as e:
        print(f"Failed to subscribe. Error: {e}")
        sys.exit(1)

    print("\n--- Starting Live Market Simulation ---")
    
    # We will simulate a market where the price drops by 1000 every 2 seconds.
    # We will mock the backend's check_and_send_alerts function directly because 
    # the frontend doesn't push prices. Wait, the backend only checks when /api/decision is hit
    # or a scrape happens. We can't easily mock the price via API unless we inject into the DB.
    # Wait! The easiest way to simulate without messing up the DB is to just import and call check_and_send_alerts!
    
    # We need to run this script from the scrapping/ directory, so we can import backend.
    
    # Let's append the current directory to sys.path just in case
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    
    from backend.scraper.notifier import check_and_send_alerts
    
    mock_price = current_price
    
    for i in range(1, 10):
        time.sleep(2)
        mock_price -= 1000
        print(f"[Market TICK {i}] New price detected for {prod}: ₹{mock_price}")
        
        # Fire the backend check
        # Usually triggered internally when price is updated or checked
        check_and_send_alerts(
            product_name=prod,
            current_price=mock_price,
            decision_text="Simulation: Price has dropped drastically in our live tracking!"
        )
        
        if mock_price <= target_price:
            print(f"Target price of ₹{target_price} met or exceeded!")
            print("Email alert should have been triggered by backend.")
            break

    print("=== Simulation Complete ===")

if __name__ == "__main__":
    # Ensure env is loaded or assumed
    test_live_alert()
