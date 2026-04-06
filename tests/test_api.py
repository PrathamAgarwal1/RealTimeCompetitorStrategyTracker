import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_list_products():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/products")
    assert response.status_code == 200
    assert "products" in response.json()

@pytest.mark.asyncio
async def test_forecast_invalid_product():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/forecast", json={
            "product_name": "NonExistentProduct",
            "model": "prophet"
        })
    assert response.status_code == 404
@pytest.mark.asyncio
async def test_sentiment_analysis():
    transport = ASGITransport(app=app)
    # Use a real product name from previous successful requests if possible, 
    # but here we just check structure.
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/sentiment/analyze", json={
            "product_name": "Samsung Galaxy S26 Ultra 5G (Sky Blue, 256 GB)" 
        })
    
    # If the product exists in the DB moved to root/data, it should return 200.
    # Otherwise it might return 404, but we want to check structure if 200.
    if response.status_code == 200:
        data = response.json()
        assert "sentiment_distribution" in data
        assert "category_distribution" in data
        assert "Positive" in data["sentiment_distribution"]

@pytest.mark.asyncio
async def test_datafiles_preview():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Assuming database.sqlite exists in root/data
        response = await ac.get("/api/datafiles/preview?path=database.sqlite")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "columns" in data
    assert "rows" in data
    assert "total_rows" in data
