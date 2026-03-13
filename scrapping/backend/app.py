from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

import os
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from .database import save_data, load_data

from .scraper.amazon_price import fetch_amazon_price_history
from .scraper.flipkart_price import fetch_flipkart_price_history
from .scraper.amazon_reviews import fetch_amazon_reviews
from .scraper.flipkart_reviews import fetch_flipkart_reviews

# Load .env from parent directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

app = FastAPI(title="Scraper Dashboard")

# Global driver for interactive auth
auth_driver = None

@app.get("/api/amazon-auth/start")
async def start_amazon_auth():
    global auth_driver
    if auth_driver is not None:
        try:
            auth_driver.quit()
        except:
            pass
    try:
        options = Options()
        # Not headless so the user can easily log in
        auth_driver = webdriver.Chrome(options=options)
        auth_driver.maximize_window()
        auth_driver.get("https://www.amazon.in/")
        return {"success": True, "message": "Browser opened. Please log in, then click Save Cookies."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/amazon-auth/save")
async def save_amazon_auth():
    global auth_driver
    if auth_driver is None:
        return {"success": False, "error": "No auth browser is currently open. Start auth first."}
    try:
        cookies = auth_driver.get_cookies()
        
        # Save cookies in scrapping directory (parent of backend)
        cookie_path = os.path.join(os.path.dirname(__file__), "..", "amazon_cookies.pkl")
        with open(cookie_path, "wb") as f:
            pickle.dump(cookies, f)
            
        auth_driver.quit()
        auth_driver = None
        return {"success": True, "message": "Cookies saved successfully!"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Ensure paths
os.makedirs("data", exist_ok=True)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
os.makedirs(FRONTEND_DIR, exist_ok=True)

class ScrapeRequest(BaseModel):
    query: Optional[str] = None
    url: Optional[str] = None
    asin: Optional[str] = None

@app.post("/api/scrape/amazon-price")
async def api_scrape_amazon_price(req: ScrapeRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="Missing url")
    
    result = fetch_amazon_price_history(req.url)
    if result["success"]:
        save_data(result["data"])
    return result

@app.post("/api/scrape/flipkart-price")
async def api_scrape_flipkart_price(req: ScrapeRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="Missing url")
        
    result = fetch_flipkart_price_history(req.url)
    if result["success"]:
        save_data(result["data"])
    return result

@app.post("/api/scrape/amazon-reviews")
async def api_scrape_amazon_reviews(req: ScrapeRequest):
    if not req.asin:
        raise HTTPException(status_code=400, detail="Missing asin")
        
    result = fetch_amazon_reviews(req.asin)
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

@app.get("/api/data")
async def get_all_data():
    data = load_data()
    return {"success": True, "count": len(data), "data": data}

# Mount static files at the root
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
