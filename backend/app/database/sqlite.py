import os
import sqlite3
import pandas as pd
import json
import logging
from ..config import settings

logger = logging.getLogger(__name__)

# Reusing logic from the original database.py but with settings integration
DB_PATH = os.path.join(settings.DATA_DIR, "database.sqlite")

def ensure_data_dir():
    os.makedirs(settings.DATA_DIR, exist_ok=True)

def init_db():
    ensure_data_dir()
    logger.info(f"Initializing database at {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute('''
            CREATE TABLE IF NOT EXISTS scraped_data (
                timestamp TEXT,
                source TEXT,
                product_name TEXT,
                price REAL,
                rating TEXT,
                review_text TEXT,
                url TEXT,
                metadata TEXT
            )
        ''')
        
        # MIGRATION: Ensure all expected columns exist
        cursor = con.cursor()
        cursor.execute("PRAGMA table_info(scraped_data)")
        existing_cols = [row[1] for row in cursor.fetchall()]
        
        required_cols = [
            ('timestamp', 'TEXT'),
            ('source', 'TEXT'),
            ('product_name', 'TEXT'),
            ('price', 'REAL'),
            ('rating', 'TEXT'),
            ('review_text', 'TEXT'),
            ('url', 'TEXT'),
            ('metadata', 'TEXT')
        ]
        
        for col_name, col_type in required_cols:
            if col_name not in existing_cols:
                logger.warning(f"Adding missing '{col_name}' column to scraped_data table...")
                con.execute(f"ALTER TABLE scraped_data ADD COLUMN {col_name} {col_type}")
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise
    finally:
        con.commit()
        con.close()

def save_data(data_list: list) -> bool:
    """Appends scraped data to the SQLite database."""
    if not data_list:
        return True
        
    init_db()
    
    df_new = pd.DataFrame(data_list)
    
    for col in ["timestamp", "source", "product_name", "price", "rating", "review_text", "url", "metadata"]:
        if col not in df_new.columns:
            df_new[col] = None
        
    if "metadata" in df_new.columns:
        df_new["metadata"] = df_new["metadata"].astype(str)

    try:
        logger.info(f"Saving {len(data_list)} records to database.")
        con = sqlite3.connect(DB_PATH)
        df_new.to_sql('scraped_data', con, if_exists='append', index=False)
        con.close()
        return True
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        return False

def load_data() -> list:
    """Returns all saved scraped data as a list of dicts."""
    if not os.path.exists(DB_PATH):
        logger.debug(f"Database file not found at {DB_PATH}")
        return []
    try:
        con = sqlite3.connect(DB_PATH)
        df = pd.read_sql('SELECT * FROM scraped_data', con)
        con.close()
        return json.loads(df.to_json(orient="records"))
    except Exception as e:
        logger.error(f"Error loading database: {e}")
        return []
