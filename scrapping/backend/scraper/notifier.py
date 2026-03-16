import os
import json
import smtplib
from email.message import EmailMessage
from pathlib import Path

# ====================== CONFIG ======================
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Use environment variable to control if emails should actually be sent
# Default to true only if credentials exist
ENABLE_EMAILS = bool(EMAIL_SENDER and EMAIL_PASSWORD)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")


def _load_alerts() -> list[dict]:
    if not os.path.exists(ALERTS_FILE):
        return []
    try:
        with open(ALERTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def _save_alerts(alerts: list[dict]):
    os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=4)


def subscribe_user(email: str, product_name: str) -> bool:
    """Subscribe a user to a specific product's deal alerts."""
    alerts = _load_alerts()
    
    # Check if already subscribed
    for a in alerts:
        if a.get("email") == email and a.get("product_name") == product_name:
            return True # already subscribed
            
    alerts.append({
        "email": email,
        "product_name": product_name,
        "active": True
    })
    
    _save_alerts(alerts)
    return True

def get_subscriptions_for_product(product_name: str) -> list[str]:
    """Get all active emails subscribed to a product."""
    alerts = _load_alerts()
    return [a["email"] for a in alerts if a.get("product_name") == product_name and a.get("active")]

def send_deal_alert(to_email: str, product_name: str, price: float, decision_text: str) -> bool:
    """Send an email alert to the user."""
    if not ENABLE_EMAILS:
        print(f"📧 [Mock Email]: Sent to {to_email} for {product_name} at {price}. Reason: {decision_text}")
        return True
        
    try:
        msg = EmailMessage()
        msg['Subject'] = f"🚨 Price Drop Alert: {product_name} is a Good Buy!"
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        
        content = f"""
Hello,

Good news! The product '{product_name}' that you are tracking is currently in a great position to buy.

Current Stats:
- Price: {price}
- AI Decision Insight: {decision_text}

Visit the dashboard to see more details and purchase link: http://localhost:8000/

Happy shopping!
- ForecastPro Automation
        """
        msg.set_content(content.strip())
        
        # Connect to Gmail SMTP (change if using another provider)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
            
        print(f"Email successfully sent to {to_email} for {product_name}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False

