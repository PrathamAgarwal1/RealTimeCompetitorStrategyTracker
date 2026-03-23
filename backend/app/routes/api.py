import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import glob
import os
import sqlite3
import pandas as pd
import json
from fastapi.responses import FileResponse

from ..models.schemas import ScrapeRequest, ForecastRequest, SentimentRequest, DecisionRequest, SubscribeRequest
from ..database.sqlite import save_data, load_data
from ..services.decision_service import get_product_reviews, make_decision
from ..services.scraper.flipkart_price import fetch_flipkart_price_history
from ..services.scraper.flipkart_reviews import fetch_flipkart_reviews
from ..services.scraper.sentiment import analyze_reviews
from ..services.scraper.notifier import subscribe_user
from ..services.forecasting.data_handler import list_products, load_product_price_data
from ..services.forecasting.prophet_model import run_prophet_forecast
from ..services.forecasting.chronos_model import run_chronos_forecast
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ── API ROUTES ────────────────────────────────────────────────

# ── Flipkart Scrapers ─────────────────────────────────────────
@router.post("/scrape/flipkart-price")
async def api_scrape_flipkart_price(req: ScrapeRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="Missing url")
    logger.info(f"Scraping Flipkart price history from: {req.url}")
    result = fetch_flipkart_price_history(req.url)
    if result["success"]:
        save_data(result["data"])
    return result

@router.post("/scrape/flipkart-reviews")
async def api_scrape_flipkart_reviews(req: ScrapeRequest):
    if not req.query:
        raise HTTPException(status_code=400, detail="Missing query")
    logger.info(f"Scraping Flipkart reviews for query: {req.query}")
    result = fetch_flipkart_reviews(req.query)
    if result["success"]:
        save_data(result["data"])
    return result

# ── Database ───────────────────────────────────────────────────
@router.get("/data")
async def get_all_data():
    data = load_data()
    return {"success": True, "count": len(data), "data": data}

@router.get("/datafiles")
async def list_data_files():
    files = []
    for ext in ("*.csv", "*.xlsx", "*.json", "*.sqlite", "*.db"):
        for fpath in glob.glob(os.path.join(settings.DATA_DIR, "**", ext), recursive=True):
            stat = os.stat(fpath)
            files.append({
                "name": os.path.basename(fpath),
                "path": os.path.relpath(fpath, settings.DATA_DIR).replace("\\", "/"),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
    files.sort(key=lambda f: f["modified"], reverse=True)
    return {"success": True, "files": files}

@router.get("/datafiles/preview")
async def preview_data_file(path: str, page: int = 1, page_size: int = 50, search: str = ""):
    """Preview contents of a data file with pagination and search."""
    full_path = os.path.normpath(os.path.join(settings.DATA_DIR, path))
    logger.info(f"Previewing file: {full_path}")

    if not full_path.startswith(os.path.normpath(settings.DATA_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(full_path):
        logger.error(f"File not found: {full_path}")
        raise HTTPException(status_code=404, detail="File not found")

    try:
        ext = os.path.splitext(full_path)[1].lower()
        
        # Native SQLite fast path
        if ext in (".sqlite", ".db"):
            con = sqlite3.connect(full_path)
            
            # Find the first user table dynamically
            table_df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' LIMIT 1", con)
            if len(table_df) == 0:
                con.close()
                return {"success": True, "columns": [], "rows": [], "total_rows": 0, "page": 1, "page_size": page_size, "total_pages": 1}
            table_name = table_df.iloc[0]["name"]
            logger.info(f"Previewing table: {table_name}")
            
            # Search filter
            where_clause = ""
            params = []
            if search:
                # Basic search across known columns
                where_clause = " WHERE product_name LIKE ? OR review_text LIKE ? OR source LIKE ?"
                search_term = f"%{search}%"
                params = [search_term, search_term, search_term]
            
            # Pagination
            count_query = f"SELECT COUNT(*) as c FROM {table_name}{where_clause}"
            total_rows = int(pd.read_sql(count_query, con, params=params).iloc[0]["c"])
            
            total_pages = int(max(1, (total_rows + page_size - 1) // page_size))
            page = max(1, min(page, total_pages))
            offset = (page - 1) * page_size
            
            query = f"SELECT * FROM {table_name}{where_clause} LIMIT ? OFFSET ?"
            params.extend([page_size, offset])
            df = pd.read_sql(query, con, params=params)
            con.close()
            
            # JSON serialization fix for numpy types
            records = json.loads(df.to_json(orient="records"))
            
        else:
            # Slower path for flat files
            if ext == ".csv":
                df = pd.read_csv(full_path)
            elif ext == ".xlsx":
                df = pd.read_excel(full_path)
            elif ext == ".json":
                df = pd.read_json(full_path)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
                
            if search:
                mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False, na=False).any(), axis=1)
                df = df[mask]
                
            total_rows = len(df)
            total_pages = max(1, (total_rows + page_size - 1) // page_size)
            page = max(1, min(page, total_pages))
            
            start = (page - 1) * page_size
            end = start + page_size
            page_df = df.iloc[start:end]
            records = json.loads(page_df.to_json(orient="records"))

        logger.info(f"Successfully fetched {len(records)} rows from {full_path} (Total rows: {total_rows})")
        return {
            "success": True,
            "columns": list(df.columns),
            "rows": records,
            "total_rows": total_rows,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    except Exception as e:
        logger.error(f"Failed to read file {full_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

@router.get("/datafiles/download")
async def download_data_file(path: str):
    """Download a data file."""
    full_path = os.path.normpath(os.path.join(settings.DATA_DIR, path))
    if not full_path.startswith(os.path.normpath(settings.DATA_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full_path, filename=os.path.basename(full_path))

# ── Forecasting ────────────────────────────────────────────────
@router.get("/products")
async def api_list_products():
    products = list_products()
    return {"success": True, "products": products}

@router.post("/forecast")
async def api_run_forecast(req: ForecastRequest):
    logger.info(f"Running {req.model} forecast for {req.product_name}")
    df = load_product_price_data(req.product_name)
    if df is None:
        raise HTTPException(status_code=404, detail="Product not found or has no price data.")
    if len(df) < 10:
        raise HTTPException(status_code=400, detail="Need at least 10 data points for forecasting.")

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

# ── Sentiment & Decision ───────────────────────────────────────
@router.post("/sentiment/analyze")
async def api_analyze_sentiment(req: SentimentRequest):
    logger.info(f"Analyzing sentiment for product: {req.product_name}")
    all_data = load_data()
    product_reviews = get_product_reviews(all_data, req.product_name)

    if not product_reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this product.")

    results = analyze_reviews(product_reviews[:100])
    return {
        "success": True,
        "total_analyzed": results["total_analyzed"],
        "sentiment_distribution": results["sentiment_distribution"],
        "category_distribution": results["category_distribution"],
        "sample_reviews": results["reviews"][:10],
    }

@router.post("/decision")
async def api_get_decision(req: DecisionRequest):
    logger.info(f"Getting purchase decision for product: {req.product_name}")
    all_data = load_data()
    product_reviews = get_product_reviews(all_data, req.product_name)
    product_prices = load_product_price_data(req.product_name)

    if not product_reviews and product_prices is None:
        raise HTTPException(status_code=404, detail="No data found for this product.")

    return make_decision(req.product_name, product_prices, product_reviews[:100])
