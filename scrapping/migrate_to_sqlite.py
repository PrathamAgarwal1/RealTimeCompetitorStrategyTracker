import os
import sqlite3
import pandas as pd

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "raw_data.csv")
DB_PATH = os.path.join(DATA_DIR, "database.sqlite")

def migrate():
    print(f"Starting migration from {CSV_PATH} to {DB_PATH}...")
    
    if not os.path.exists(CSV_PATH):
        print("No raw_data.csv found. Nothing to migrate.")
        return
        
    try:
        # Read existing CSV
        df = pd.read_csv(CSV_PATH)
        print(f"Loaded {len(df)} rows from CSV.")
        
        # Connect to SQLite (creates file if not exists)
        con = sqlite3.connect(DB_PATH)
        
        # Write to SQLite table 'scraped_data'
        df.to_sql('scraped_data', con, if_exists='replace', index=False)
        
        # Verify
        count = pd.read_sql('SELECT COUNT(*) as c FROM scraped_data', con).iloc[0]['c']
        print(f"Successfully migrated {count} rows into SQLite!")
        
        con.close()
        
        # Optional: rename original CSV so it's not accidentally used again
        backup_path = CSV_PATH + ".backup"
        os.rename(CSV_PATH, backup_path)
        print(f"Original CSV renamed to {backup_path} for safekeeping.")
        
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
