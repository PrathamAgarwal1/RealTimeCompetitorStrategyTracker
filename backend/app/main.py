import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes.api import router as api_router
from .routes.health import router as health_router
from .config import settings

# ── LOGGING CONFIGURATION ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_TITLE)

# ── API ROUTES ──
app.include_router(api_router, prefix="/api")
app.include_router(health_router, prefix="/api")

# ── STATIC FILES (Frontend) ──
if os.path.exists(settings.FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=settings.FRONTEND_DIR, html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at {settings.FRONTEND_DIR}. UI will not be available.")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting ForecastPro Backend...")
    # Ensure data directory exists
    os.makedirs(settings.DATA_DIR, exist_ok=True)
