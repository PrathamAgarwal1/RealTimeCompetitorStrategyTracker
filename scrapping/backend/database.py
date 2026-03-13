import os
import pandas as pd

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw_data.csv")

def save_data(data_list: list) -> bool:
    """Appends scraped data to the central CSV file."""
    if not data_list:
        return True
        
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    
    df_new = pd.DataFrame(data_list)
    
    if os.path.exists(CSV_PATH):
        df_existing = pd.read_csv(CSV_PATH)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        # Optional: simple deduplication based on text or timestamp
    else:
        df_combined = df_new
        
    try:
        df_combined.to_csv(CSV_PATH, index=False)
        return True
    except Exception as e:
        print(f"Error saving to database: {e}")
        return False

import json

def load_data() -> list:
    """Returns all saved scraped data as a list of dicts."""
    if not os.path.exists(CSV_PATH):
        return []
        
    try:
        df = pd.read_csv(CSV_PATH)
        # Use pandas native to_json to handle all NaN, NaT, and float serialization safely
        return json.loads(df.to_json(orient="records"))
    except Exception as e:
        print(f"Error loading database: {e}")
        return []
