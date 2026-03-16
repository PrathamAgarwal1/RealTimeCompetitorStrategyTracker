from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import io
import json
from dotenv import load_dotenv

import os
from .database import save_data, load_data

from .scraper.flipkart_price import fetch_flipkart_price_history
from .scraper.flipkart_reviews import fetch_flipkart_reviews
from .scraper.sentiment import analyze_reviews
from .scraper.notifier import subscribe_user, check_and_send_alerts

from .forecasting.data_handler import (
    list_products,
    load_product_price_data,
)
from .forecasting.prophet_model import run_prophet_forecast
from .forecasting.chronos_model import run_chronos_forecast

# Load .env from parent directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

app = FastAPI(title="Price Forecasting Dashboard")

# Ensure paths
os.makedirs("data", exist_ok=True)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
os.makedirs(FRONTEND_DIR, exist_ok=True)


class ScrapeRequest(BaseModel):
    query: Optional[str] = None
    url: Optional[str] = None


# ── Flipkart Scrapers ──────────────────────────────────────────

@app.post("/api/scrape/flipkart-price")
async def api_scrape_flipkart_price(req: ScrapeRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="Missing url")

    result = fetch_flipkart_price_history(req.url)
    if result["success"]:
        save_data(result["data"])
    return result


@app.post("/api/scrape/flipkart-reviews")
async def api_scrape_flipkart_reviews(req: ScrapeRequest):
    if not req.query:
        raise HTTPException(status_code=400, detail="Missing query")

    result = fetch_flipkart_reviews(req.query)
    if result["success"]:
        save_data(result["data"])
    return result


# ── Database ────────────────────────────────────────────────────

@app.get("/api/data")
async def get_all_data():
    data = load_data()
    return {"success": True, "count": len(data), "data": data}


# ── Forecasting Endpoints ──────────────────────────────────────

@app.get("/api/products")
async def api_list_products():
    """List all unique scraped products that have price data."""
    products = list_products()
    return {"success": True, "products": products}


@app.get("/api/historical/{product_name}")
async def api_get_historical(product_name: str):
    """Return historical price data for a product as JSON."""
    df = load_product_price_data(product_name)
    if df is None:
        raise HTTPException(status_code=404, detail="Product not found or has no price data.")

    data = []
    for _, row in df.iterrows():
        # Format the number correctly without using ndigits explicitly as it breaks typing sometimes
        price_val = float(row["y"])
        data.append({
            "date": row["ds"].strftime("%Y-%m-%d"),
            "price": float(f"{price_val:.2f}"),
        })

    return {"success": True, "count": len(data), "data": data}


class ForecastRequest(BaseModel):
    product_name: str
    model: str = "both"  # "prophet", "chronos", or "both"
    periods: int = 30


@app.post("/api/forecast")
async def api_run_forecast(req: ForecastRequest):
    """Run price forecast on a product using selected model(s)."""
    df = load_product_price_data(req.product_name)
    if df is None:
        raise HTTPException(status_code=404, detail="Product not found or has no price data.")

    if len(df) < 10:
        raise HTTPException(status_code=400, detail="Need at least 10 data points for forecasting.")

    # Build historical data for response
    historical = []
    for _, row in df.iterrows():
        price_val = float(row["y"])
        historical.append({
            "date": row["ds"].strftime("%Y-%m-%d"),
            "price": float(f"{price_val:.2f}"),
        })

    results = {"historical": historical}

    if req.model in ("prophet", "both"):
        results["prophet"] = run_prophet_forecast(df, periods=req.periods)

    if req.model in ("chronos", "both"):
        results["chronos"] = run_chronos_forecast(df, periods=req.periods)

    return {"success": True, **results}


# ── Sentiment & Custom Uploads ──────────────────────────────────

class SentimentRequest(BaseModel):
    product_name: str

import re

def get_product_reviews(all_data, target_name):
    reviews = []
    target_norm = re.sub(r'[^a-z0-9]', '', target_name.lower())
    for d in all_data:
        if d.get("source") != "flipkart_reviews": continue
        r_name = d.get("product_name", "")
        r_norm = re.sub(r'[^a-z0-9]', '', r_name.lower().replace("add to compare", ""))
        
        if target_norm in r_norm or r_norm in target_norm:
            reviews.append(d)
        else:
            target_words = set(re.findall(r'[a-z0-9]+', target_name.lower()))
            r_words = set(re.findall(r'[a-z0-9]+', r_name.lower()))
            for stop in ["add", "to", "compare"]:
                target_words.discard(stop)
                r_words.discard(stop)
            if target_words and r_words:
                overlap = len(target_words.intersection(r_words))
                if overlap >= min(len(target_words), len(r_words)) * 0.7:
                    reviews.append(d)
    return reviews

@app.post("/api/sentiment/analyze")
async def api_analyze_sentiment(req: SentimentRequest):
    """Analyze sentiment for a specific product from the database."""
    all_data = load_data()
    product_reviews = get_product_reviews(all_data, req.product_name)
    
    if not product_reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this product in the database.")
        
    # Only process up to 100 to avoid extremely long timeouts
    product_reviews = product_reviews[:100]
    
    analyzed = analyze_reviews(product_reviews)
    
    # Calculate stats
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    category_counts = {}
    for r in analyzed:
        sentiment_counts[r.get("sentiment", "Neutral")] += 1
        cat = r.get("category", "General")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        
    return {
        "success": True,
        "total_analyzed": len(analyzed),
        "sentiment_distribution": sentiment_counts,
        "category_distribution": category_counts,
        "sample_reviews": analyzed[:10]  # Return just a few samples for the UI
    }


# ── Decision & Alerts ───────────────────────────────────────────

class DecisionRequest(BaseModel):
    product_name: str

@app.post("/api/decision")
async def api_get_decision(req: DecisionRequest):
    """Analyze reviews and price to provide a Buy/Wait decision."""
    all_data = load_data()
    
    # Filter reviews and prices for this product
    product_reviews = get_product_reviews(all_data, req.product_name)
    product_prices = load_product_price_data(req.product_name)
    
    if not product_reviews and product_prices is None:
        raise HTTPException(status_code=404, detail="No data found for this product.")

    
    # Cap to 100 reviews to avoid extreme delays
    product_reviews = product_reviews[:100]

    return make_decision(
        req.product_name, 
        product_prices, 
        product_reviews
    )



def make_decision(product_name, product_prices, product_reviews):
    # 1. Analyze Sentiment
    analyzed_reviews = analyze_reviews(product_reviews)
    
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for r in analyzed_reviews:
        sentiment_counts[r.get("sentiment", "Neutral")] += 1
        
    total_reviews = len(analyzed_reviews)
    positive_ratio = (sentiment_counts["Positive"] / total_reviews) if total_reviews > 0 else 0

    # 2. Analyze Price
    current_price = 0
    price_status = "Unknown"
    
    if product_prices is not None and len(product_prices) > 0:
        current_price = product_prices.iloc[-1]["y"]
        median_price = product_prices["y"].median()
        
        if current_price <= median_price * 1.05: # Within 5% of median or lower
            price_status = "Good"
        else:
            price_status = "High"

    # 3. Make Decision
    decision = "Wait"
    reason = "Not enough data to make a confident decision."
    
    if total_reviews >= 5 and product_prices is not None:
        if price_status == "Good" and positive_ratio >= 0.5:
            decision = "Buy Now"
            reason = "Price is currently at or below the historical average, and user sentiment is strongly positive."
        elif price_status == "High" and positive_ratio >= 0.5:
            decision = "Wait"
            reason = "User sentiment is positive, but the price is currently higher than the historical average. Consider waiting for a drop."
        elif price_status == "Good" and positive_ratio < 0.5:
            decision = "Wait"
            reason = "Price is good, but user reviews are predominantly negative or mixed. Proceed with caution."
        else:
            decision = "Wait"
            reason = "Price is high and reviews are poor. Not recommended to buy right now."

    
    if current_price and price_status != "Unknown":
        check_and_send_alerts(product_name, current_price, reason)

    return {
        "success": True, 
        "decision": decision, 
        "reason": reason,
        "sentiment_distribution": sentiment_counts,
        "current_price": float(current_price) if current_price else None,
        "positive_ratio": float(positive_ratio)
    }

class SubscribeRequest(BaseModel):
    email: str
    product_name: str
    target_price: float

@app.post("/api/subscribe")
async def api_subscribe_alerts(req: SubscribeRequest):
    """Subscribe a user to deal alerts for a product."""
    success = subscribe_user(req.email, req.product_name, req.target_price)
    if success:
         return {"success": True, "message": "Successfully subscribed to alerts."}
    raise HTTPException(status_code=500, detail="Failed to subscribe.")


# Mount static files at the root (MUST be last)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
