import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    APP_TITLE: str = "Price Forecasting Dashboard"
    PORT: int = 8000
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./data/database.sqlite"
    GROQ_API_KEY: Optional[str] = None
    
    # Path settings
    # BASE_DIR is backend/
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # ROOT_DIR is the project root
    ROOT_DIR: str = os.path.dirname(BASE_DIR)
    
    DATA_DIR: str = os.path.join(ROOT_DIR, "data")
    FRONTEND_DIR: str = os.path.join(ROOT_DIR, "scrapping", "frontend")

    class Config:
        env_file = ".env"

settings = Settings()
