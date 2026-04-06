import uvicorn
import os
import sys

# Ensure we are in the scrapping directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

if __name__ == "__main__":
    print("🚀 Starting the Price Forecasting Dashboard...")
    print("🔗 Access the UI at: http://localhost:8000")
    
    # Run the FastAPI app using uvicorn
    # backend.app:app refers to the 'app' object in scrapping/backend/app.py
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
