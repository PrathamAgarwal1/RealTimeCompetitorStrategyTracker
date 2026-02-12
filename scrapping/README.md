# E-Commerce Scraping Tools

This folder contains web scraping scripts for collecting price history and review data from e-commerce platforms.

## 📁 Files Overview

### 1. **flipkart_scapper.py**
Scrapes historical price data for Flipkart products from pricehistory.app.

**Usage:**
```bash
python flipkart_scapper.py
```
- Prompts for a pricehistory.app product URL
- Decrypts and extracts price history data
- Saves to `raw/flipkart_historical_prices.csv`

**Output Format:**
- Date (datetime)
- Price (float)

---

### 2. **amazon_scrapper.py**
Scrapes historical price data for Amazon products from pricehistoryapp.com.

**Usage:**
```bash
python amazon_scrapper.py
```
- Prompts for a pricehistoryapp.com product URL
- Uses API to fetch price history
- Saves to `raw/amazon_dataset.csv`

**Output Format:**
- date (datetime)
- price (float)
- brand (string - "Amazon")

**Note:** Uses authentication token. May need updates if the API changes.

---

### 3. **save_cookies.py**
Saves Amazon login cookies for authenticated scraping (required for review scraping).

**Usage:**
```bash
python save_cookies.py
```
- Opens Amazon.in in a browser window
- Prompts you to log in manually
- Saves cookies to `amazon_cookies.pkl` after login

**Important:** Run this BEFORE using `scrape_reviews_with_cookies.py`

---

### 4. **scrape_reviews_with_cookies.py**
Scrapes Amazon product reviews using saved authentication cookies.

**Usage:**
```bash
python scrape_reviews_with_cookies.py
```
- Prompts for Amazon ASIN (10-character product ID)
- Scrapes up to 10 pages of reviews (configurable)
- Saves to Excel file: `amazon_reviews_{ASIN}_{timestamp}.xlsx`

**Output Format:**
- Review_Title
- Review_Body
- Review_Stars
- Reviewer
- Review_Date

**Configuration:**
- `MAX_PAGES = 10` - Maximum pages to scrape
- `DELAY_RANGE = (3, 6)` - Random delay between requests (seconds)

---

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Chrome WebDriver (for Selenium)
The scripts use Selenium with Chrome. Ensure you have:
- Google Chrome installed
- ChromeDriver (automatically managed by selenium 4.15+)

### 3. For Amazon Review Scraping
```bash
# Step 1: Save cookies first
python save_cookies.py

# Step 2: Scrape reviews
python scrape_reviews_with_cookies.py
```

---

## 📊 Output Directory Structure

```
scrapping/
├── raw/                                    # Output data folder
│   ├── flipkart_historical_prices.csv
│   ├── amazon_dataset.csv
│   └── amazon_reviews_*.xlsx
├── amazon_cookies.pkl                      # Saved login cookies
└── ...
```

---

## ⚠️ Important Notes

### Rate Limiting & Ethics
- All scripts include delays to avoid overwhelming servers
- Respect robots.txt and terms of service
- Use responsibly and for educational/research purposes only

### Troubleshooting

**Issue:** "Encrypted data not found" (Flipkart)
- **Solution:** The website structure may have changed. Check if pricehistory.app is accessible.

**Issue:** "403 Forbidden" (Amazon API)
- **Solution:** The auth token may be expired. You may need to update the `AUTH_TOKEN` in `amazon_scrapper.py`.

**Issue:** "No reviews found" (Amazon Reviews)
- **Solution:** 
  1. Ensure cookies are fresh (re-run `save_cookies.py`)
  2. Check if the ASIN is valid
  3. Amazon may have detected automation - try increasing delays

**Issue:** Selenium/ChromeDriver errors
- **Solution:** Update selenium: `pip install --upgrade selenium`

---

## 🔧 Customization

### Change Review Scraping Limits
Edit `scrape_reviews_with_cookies.py`:
```python
MAX_PAGES = 20  # Increase to scrape more pages
DELAY_RANGE = (5, 10)  # Increase delays for more safety
```

### Change Output Format
All scripts use pandas DataFrames, making it easy to change output formats:
```python
# Instead of CSV
df.to_json("output.json", orient="records")
# Instead of Excel
df.to_csv("output.csv", index=False)
```

---

## 📈 Integration with Main Project

These scrapers collect raw data that feeds into the AI-driven Decision Support Dashboard:
- Price data → Time-frame analysis & trend visualization
- Review data → LLM-based sentiment analysis & aspect extraction

---

## 🛠️ Future Enhancements
- [ ] Add support for more e-commerce platforms (Myntra, Snapdeal, etc.)
- [ ] Implement proxy rotation for large-scale scraping
- [ ] Add data validation and cleaning pipelines
- [ ] Create scheduled scraping with cron jobs
- [ ] Add database integration (MongoDB/PostgreSQL)

---

**Last Updated:** February 2026
