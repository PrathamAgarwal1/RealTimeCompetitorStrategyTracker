import sys
sys.stdout.reconfigure(encoding='utf-8')

import pickle
import re
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ---------------------------
# CONFIG
# ---------------------------

MAX_PAGES = 10
DELAY_RANGE = (3, 6)

def clean_text(t):
    return ' '.join(t.strip().split()) if t else ""

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver

def load_cookies(driver, path="amazon_cookies.pkl"):
    cookies = pickle.load(open(path, "rb"))
    driver.get("https://www.amazon.in/")
    for cookie in cookies:
        if 'expiry' in cookie:
            del cookie['expiry']
        driver.add_cookie(cookie)
    print(f"✅ Loaded {len(cookies)} cookies.")
    time.sleep(2)

def extract_reviews_from_page(soup):
    reviews = []
    blocks = soup.find_all(attrs={"data-hook": "review"})

    for blk in blocks:
        title = blk.find(attrs={"data-hook": "review-title"})
        body = blk.find(attrs={"data-hook": "review-body"})
        stars_tag = blk.find(attrs={"data-hook": "review-star-rating"}) or blk.find("i", class_="a-icon-alt")
        reviewer_tag = blk.find("span", class_="a-profile-name")
        date_tag = blk.find(attrs={"data-hook": "review-date"})

        stars = ""
        if stars_tag:
            m = re.search(r"[0-9\.]+", stars_tag.get_text(strip=True))
            if m:
                stars = m.group(0)

        reviews.append({
            "Review_Title": clean_text(title.get_text()) if title else "",
            "Review_Body": clean_text(body.get_text()) if body else "",
            "Review_Stars": stars,
            "Reviewer": clean_text(reviewer_tag.get_text()) if reviewer_tag else "",
            "Review_Date": clean_text(date_tag.get_text()) if date_tag else ""
        })

    return reviews

def scrape_reviews(driver, asin, max_pages):
    url = f"https://www.amazon.in/product-reviews/{asin}/?ie=UTF8&reviewerType=all_reviews"
    driver.get(url)
    time.sleep(random.uniform(*DELAY_RANGE))

    all_reviews = []
    page = 1

    while page <= max_pages:
        print(f"\n🔍 Page {page}")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        revs = extract_reviews_from_page(soup)

        if not revs:
            print("❌ No reviews found. Stopping.")
            break

        print(f"  → Found {len(revs)} reviews.")
        all_reviews.extend(revs)

        next_btn = driver.find_elements("css selector", "li.a-last a")
        if not next_btn:
            print("✅ Reached last page.")
            break

        next_btn[0].click()
        time.sleep(random.uniform(4, 7))
        page += 1

    return all_reviews

def save_to_excel(reviews, asin):
    if not reviews:
        print("⚠️ No reviews to save.")
        return

    df = pd.DataFrame(reviews)
    filename = f"amazon_reviews_{asin}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(filename, index=False)
    print(f"✅ Saved {len(df)} reviews to {filename}")

# ---------------------------
# MAIN
# ---------------------------

if __name__ == "__main__":
    ASIN = input("Enter Amazon ASIN (10 characters): ").strip()

    if len(ASIN) != 10:
        print("❌ Invalid ASIN. Must be exactly 10 characters.")
        sys.exit(1)

    driver = setup_driver()
    try:
        load_cookies(driver)
        reviews = scrape_reviews(driver, ASIN, MAX_PAGES)
        save_to_excel(reviews, ASIN)
    finally:
        driver.quit()
