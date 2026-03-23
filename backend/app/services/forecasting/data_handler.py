import os
import sqlite3
import pandas as pd
import logging
from ...config import settings

logger = logging.getLogger(__name__)

# Path definition from settings
DB_PATH = os.path.join(settings.DATA_DIR, "database.sqlite")
DATA_DIR = settings.DATA_DIR

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def list_products() -> list[str]:
    """List all unique products that have price data in the database."""
    if not os.path.exists(DB_PATH):
        return []

    try:
        con = sqlite3.connect(DB_PATH)
        # Fast native SQL to get distinct non-null products
        query = "SELECT DISTINCT product_name FROM scraped_data WHERE price IS NOT NULL"
        df = pd.read_sql(query, con)
        con.close()
        
        if len(df) == 0:
            return []
            
        return sorted(df['product_name'].tolist())
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        return []

def load_product_price_data(product_name: str) -> pd.DataFrame | None:
    """
    Load price data from the database for a specific product.
    Returns DataFrame with columns ['ds', 'y'] sorted by date, or None if no data.
    """
    if not os.path.exists(DB_PATH):
        return None

    try:
        con = sqlite3.connect(DB_PATH)
        # Fast query pulling only the specific product, dropping useless rows upfront
        query = "SELECT timestamp, price FROM scraped_data WHERE product_name = ? AND price IS NOT NULL AND timestamp IS NOT NULL"
        df = pd.read_sql(query, con, params=(product_name,))
        con.close()
        
        if len(df) == 0:
            return None

        # Clean up column names for forecasting ('ds' for date, 'y' for values)
        df_forecast = pd.DataFrame()
        df_forecast["ds"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df_forecast["y"] = pd.to_numeric(df["price"], errors="coerce")
        df_forecast = df_forecast.dropna().sort_values("ds")
        
        # Keep only the last price recorded on any given day
        df_forecast["ds"] = df_forecast["ds"].dt.normalize()
        df_forecast = df_forecast.drop_duplicates(subset=["ds"], keep="last")
        
        # Resample to daily frequency and forward fill missing days
        df_forecast = df_forecast.set_index("ds").asfreq("D").ffill().reset_index()
        
        if len(df_forecast) == 0:
            return None
            
        return df_forecast
        
    except Exception as e:
        logger.error(f"Error loading price data for {product_name}: {e}")
        return None
