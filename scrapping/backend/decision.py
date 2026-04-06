"""
Decision engine — analyzes price + sentiment to produce Buy/Wait recommendations.
"""
import re
from .database import load_data
from .scraper.sentiment import analyze_reviews
from .scraper.notifier import check_and_send_alerts
from .forecasting.data_handler import load_product_price_data


def get_product_reviews(all_data: list[dict], target_name: str) -> list[dict]:
    """Fuzzy-match reviews for a product from the flat database."""
    reviews = []
    target_norm = re.sub(r'[^a-z0-9]', '', target_name.lower())

    for d in all_data:
        if d.get("source") != "flipkart_reviews":
            continue
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


def make_decision(product_name: str, product_prices, product_reviews: list[dict]) -> dict:
    """Combine sentiment analysis and price data into a Buy/Wait decision."""
    analyzed_reviews = analyze_reviews(product_reviews)

    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for r in analyzed_reviews:
        sentiment_counts[r.get("sentiment", "Neutral")] += 1

    total_reviews = len(analyzed_reviews)
    positive_ratio = (sentiment_counts["Positive"] / total_reviews) if total_reviews > 0 else 0

    # Price analysis
    current_price = 0
    price_status = "Unknown"

    if product_prices is not None and len(product_prices) > 0:
        current_price = product_prices.iloc[-1]["y"]
        median_price = product_prices["y"].median()

        if current_price <= median_price * 1.05:
            price_status = "Good"
        else:
            price_status = "High"

    # Decision logic
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
        "positive_ratio": float(positive_ratio),
    }
