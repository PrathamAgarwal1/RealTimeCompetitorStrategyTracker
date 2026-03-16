import os
from groq import Groq
import re
import json

# ====================== CONFIG ======================
API_KEY = os.getenv("GROQ_API_KEY")

try:
    client = Groq(api_key=API_KEY) if API_KEY else None
except Exception as e:
    print(f"Warning: Failed to initialize Groq client: {e}")
    client = None

# ====================== CATEGORIES =======================
CATEGORIES = {
    "Battery": ["battery", "charging", "backup", "drain", "heat"],
    "Camera": ["camera", "photo", "picture", "clarity", "lens"],
    "Performance": ["performance", "lag", "smooth", "hang", "speed", "processor", "slow"],
    "Display": ["screen", "brightness", "resolution", "display", "color"],
    "Value": ["price", "money", "worth", "value", "cheap", "expensive"],
    "Design": ["design", "look", "build", "color", "ui", "weight", "feel"],
    "Delivery": ["delivery", "packaging", "received", "delay", "box", "shipping"]
}

def detect_category(text: str) -> str:
    if not text:
        return "General"
    txt = text.lower()
    for category, keywords in CATEGORIES.items():
        if any(k in txt for k in keywords):
            return category
    return "General"


# ====================== STRICT SENTIMENT MODEL =======================
def query_model(model_name: str, prompt: str) -> str:
    """Runs a Groq model and returns text."""
    if not client:
        return ""
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_completion_tokens=120,
            stream=False # Using non-streaming for simpler backend usage
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Groq API error with {model_name}: {e}")
        return ""

def classify_sentiment(text: str) -> tuple[str, float]:
    """Predict sentiment using cascade fallback system."""
    if not text:
        return "Neutral", 0.5

    prompt = f"""
    SYSTEM:
You are a strict sentiment classifier for English, Hindi, Hinglish, and Emojis.

Your ONLY job:
Return valid JSON with fields:
{{
  "sentiment": "Positive|Neutral|Negative",
  "confidence": 0.xx
}}

RULES (STRICT + MINIMAL):
- Judge ONLY emotional tone.
- Mixed emotions → Negative.
- Unclear/weak/ambiguous → Neutral.
- Ignore filler words (e.g., yaar, bro, pls, btw, etc.).
- Emoji sentiment rules:
  Positive: 🙂😊😄❤️✨👍  
  Negative: 😡🤬😢😭💔👎  
  Neutral: 😐🤔😶
- No explanations. No extra text. JSON ONLY.

CLASSIFY:
"{text}"
    """

    models = [
        "llama3-8b-8192", # Using standard Groq models
        "mixtral-8x7b-32768"
    ]

    if client:
        for model in models:
            response_text = query_model(model, prompt)
            match = re.search(r"\{[^{}]*\}", response_text)

            if match:
                try:
                    data = json.loads(match.group(0))
                    sentiment = data.get("sentiment", "").capitalize()
                    conf = float(data.get("confidence", 0.0))
                    if sentiment in ["Positive", "Neutral", "Negative"]:
                        return sentiment, conf
                except Exception:
                    pass

    # FINAL FALLBACK: Rule-based
    review = text.lower()
    positives = ["good", "nice", "excellent", "love", "amazing", "great", "perfect", "smooth", "best", "awesome", "superb"]
    negatives = ["bad", "slow", "refund", "poor", "worst", "terrible", "heating", "hang", "issue", "horrible", "awful", "waste"]

    score = sum(word in review for word in positives) - sum(word in review for word in negatives)

    if score > 1: return "Positive", 0.75
    if score < -1: return "Negative", 0.75
    return "Neutral", 0.50

def analyze_reviews(reviews: list[dict]) -> list[dict]:
    """
    Analyzes a list of review dictionaries. 
    Adds 'sentiment', 'confidence', and 'category' if missing.
    Returns the updated list.
    """
    updated_reviews = []
    for r in reviews:
        if "sentiment" not in r or "category" not in r:
            text = r.get("review_text", "")
            sentiment, conf = classify_sentiment(text)
            category = detect_category(text)
            
            r["sentiment"] = sentiment
            r["confidence"] = conf
            r["category"] = category
        updated_reviews.append(r)
        
    return updated_reviews
