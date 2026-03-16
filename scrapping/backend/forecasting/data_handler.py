import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "raw_data.csv")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def list_products() -> list[str]:
    """List all unique products that have price data in the database."""
    if not os.path.exists(CSV_PATH):
        return []

    try:
        df = pd.read_csv(CSV_PATH)
        # Filter for rows that actually have prices
        price_df = df.dropna(subset=['price'])
        if len(price_df) == 0:
            return []
            
        return sorted(price_df['product_name'].unique().tolist())
    except Exception:
        return []


def load_product_price_data(product_name: str) -> pd.DataFrame | None:
    """
    Load price data from the database for a specific product.
    Returns DataFrame with columns ['ds', 'y'] sorted by date, or None if no data.
    """
    if not os.path.exists(CSV_PATH):
        return None

    try:
        df = pd.read_csv(CSV_PATH)
        
        # Filter by product and ensure we have price/timestamp
        df = df[df['product_name'] == product_name]
        df = df.dropna(subset=['timestamp', 'price'])
        
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
        
    except Exception:
        return None
