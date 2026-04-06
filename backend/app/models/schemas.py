from pydantic import BaseModel
from typing import Optional

class ScrapeRequest(BaseModel):
    query: Optional[str] = None
    url: Optional[str] = None

class ForecastRequest(BaseModel):
    product_name: str
    model: str = "both"
    periods: int = 30

class SentimentRequest(BaseModel):
    product_name: str

class DecisionRequest(BaseModel):
    product_name: str

class SubscribeRequest(BaseModel):
    email: str
    product_name: str
    target_price: float
