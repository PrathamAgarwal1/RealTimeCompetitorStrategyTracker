# 🚀 Quick Start Guide

## Setup (One-time)

1. **Install dependencies:**
   ```bash
   cd scrapping
   pip install -r requirements.txt
   ```

2. **Verify installation:**
   ```bash
   python validate.py
   ```
   You should see "✅ ALL VALIDATION TESTS PASSED!"

---

## Usage Examples

### 📊 Scrape Flipkart Price History

```bash
python flipkart_scapper.py
```

**Example URL:** `https://pricehistory.app/p/apple-iphone-15-black-256-gb-olByzcG5`

**Output:** `raw/flipkart_historical_prices.csv`

---

### 📊 Scrape Amazon Price History

```bash
python amazon_scrapper.py
```

**Example URL:** `https://pricehistoryapp.com/product/apple-iphone-15-pro-max`

**Output:** `raw/amazon_dataset.csv`

---

### 💬 Scrape Amazon Reviews

**Step 1: Save login cookies (first time only)**
```bash
python save_cookies.py
```
- Browser will open
- Log in to Amazon manually
- Press ENTER in terminal after login
- Cookies saved to `amazon_cookies.pkl`

**Step 2: Scrape reviews**
```bash
python scrape_reviews_with_cookies.py
```
- Enter ASIN (e.g., `B0CHX1W1XY`)
- Reviews saved to `amazon_reviews_{ASIN}_{timestamp}.xlsx`

**Finding ASIN:**
- Go to any Amazon product page
- Look in URL: `amazon.in/dp/B0CHX1W1XY` ← This is the ASIN
- Or scroll to "Product Information" section

---

## 📁 Output Files

All scraped data is saved in the `raw/` folder:

```
scrapping/
├── raw/
│   ├── flipkart_historical_prices.csv
│   ├── amazon_dataset.csv
│   └── amazon_reviews_B0CHX1W1XY_20260212_111500.xlsx
```

---

## ⚠️ Common Issues

### Issue: "Encrypted data not found"
**Solution:** Website structure changed. Try a different product URL.

### Issue: "403 Forbidden" (Amazon API)
**Solution:** Auth token expired. Contact developer for updated token.

### Issue: "No reviews found"
**Solution:** 
1. Re-run `save_cookies.py` to refresh login
2. Verify ASIN is correct
3. Check if product has reviews on Amazon

### Issue: ChromeDriver error
**Solution:** Update selenium: `pip install --upgrade selenium`

---

## 🎯 Tips

- **Rate limiting:** Scripts include delays to avoid being blocked
- **Fresh cookies:** Re-run `save_cookies.py` every few days
- **Large datasets:** Increase `MAX_PAGES` in `scrape_reviews_with_cookies.py`
- **Multiple products:** Run scripts in a loop with different URLs/ASINs

---

## 📞 Need Help?

Check the full documentation in `README.md`
