import os
import json
import smtplib
from email.message import EmailMessage
from pathlib import Path

import logging
from ...config import settings

logger = logging.getLogger(__name__)

# ====================== CONFIG ======================
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Use environment variable to control if emails should actually be sent
# Default to true only if credentials exist
ENABLE_EMAILS = bool(EMAIL_SENDER and EMAIL_PASSWORD)

DATA_DIR = settings.DATA_DIR
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


def subscribe_user(email: str, product_name: str, target_price: float) -> bool:
    """Subscribe a user to a specific product's deal alerts."""
    alerts = _load_alerts()
    
    # Check if already subscribed
    for a in alerts:
        if a.get("email") == email and a.get("product_name") == product_name:
            a["target_price"] = target_price
            a["active"] = True
            _save_alerts(alerts)
            return True # already subscribed, update target
            
    alerts.append({
        "email": email,
        "product_name": product_name,
        "target_price": target_price,
        "active": True
    })
    
    _save_alerts(alerts)
    return True

def check_and_send_alerts(product_name: str, current_price: float, decision_text: str):
    """Check active subscriptions and send alerts if target price is met."""
    if not current_price:
        return
        
    alerts = _load_alerts()
    updated = False
    
    for a in alerts:
        if a.get("product_name") == product_name and a.get("active", False):
            target_price = a.get("target_price")
            if target_price is not None and current_price <= target_price:
                # Target price met, trigger alert
                success = send_deal_alert(a["email"], product_name, current_price, decision_text)
                if success:
                    a["active"] = False
                    updated = True
                    
    if updated:
        _save_alerts(alerts)

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
        
        dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:8000")
        content = f"""
Hello,

Good news! The product '{product_name}' that you are tracking is currently in a great position to buy.

Current Stats:
- Price: {price}
- AI Decision Insight: {decision_text}

Visit the dashboard to see more details and purchase link: {dashboard_url}

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

