import sys
sys.stdout.reconfigure(encoding='utf-8')

import re
import time
import random
import os
from datetime import datetime
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import pandas as pd

# ---------------------------
# CONFIG
# ---------------------------

MAX_PAGES = 10          # Max review pages to scrape
DELAY_RANGE = (2, 4)    # Random delay (seconds) between requests


def create_driver():
    """Create a stealth Chrome driver that bypasses bot detection."""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=en-IN")
    # Keep headless commented out to avoid Bot Captchas!
    # options.add_argument("--headless=new") 
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    driver.implicitly_wait(10)
    return driver


# ---------------------------
# STEP 1 — Search & Click First Product
# ---------------------------

def click_first_product_and_switch(driver, query: str) -> str:
    encoded = quote_plus(query)
    search_url = f"https://www.flipkart.com/search?q={encoded}"

    print(f"🔍 Searching: '{query}' ...")
    driver.get(search_url)
    time.sleep(3) # Let search results load

    # Find all product links
    product_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
    
    if not product_links:
        return None

    first_link = product_links[0]
    title = first_link.text or "Product"

    print(f"✅ Found product. Clicking into it...")
    
    # Use JavaScript click to bypass any popups/overlays
    driver.execute_script("arguments[0].click();", first_link)
    time.sleep(3)

    # Flipkart opens products in a NEW TAB. We must switch the driver to look at the new tab.
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        
    time.sleep(2)
    return title


# ---------------------------
# STEP 2 — Scroll Product Page & Click "All Reviews"
# ---------------------------

def navigate_to_reviews_page(driver):
    print("📦 Scrolling product page to find 'All Reviews' link...")
    
    reviews_url = None
    # Scroll down 600px at a time, looking for the review link
    for _ in range(20):
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(0.5)
        
        # Search for any link containing '/product-reviews/'
        try:
            links = driver.find_elements(By.XPATH, "//a[contains(@href, '/product-reviews/')]")
            if links:
                for link in links:
                    if link.is_displayed():
                        reviews_url = link.get_attribute("href")
                        break
        except:
            pass
            
        if reviews_url:
            break

    if reviews_url:
        print(f"📄 Found Reviews link! Navigating...")
        driver.get(reviews_url)
        return True
    else:
        print("⚠️ Could not find an explicit 'All Reviews' link. Attempting URL fallback...")
        current_url = driver.current_url
        if "/p/" in current_url:
            fallback_url = current_url.replace("/p/", "/product-reviews/").split("?")[0] + "?marketplace=FLIPKART&page=1"
            driver.get(fallback_url)
            return True
            
    return False


# ---------------------------
# STEP 3 — Scrape Reviews & Click "Next"
# ---------------------------

def clean_text(t: str) -> str:
    return " ".join(t.strip().split()) if t else ""

def extract_reviews_from_page(soup: BeautifulSoup) -> list[dict]:
    reviews = []
    
    # Flipkart's CSS classes change constantly (they use atomic CSS now).
    # The most reliable anchor is the "Certified Buyer" text which appears in every review.
    cb_nodes = soup.find_all(lambda tag: tag.name in ['div', 'span', 'p'] and tag.get_text(strip=True) == 'Certified Buyer')
    
    unique_cbs = []
    for n in cb_nodes:
        # Avoid nested nodes (e.g. span inside div with same text)
        if not any(n in list(other.descendants) for other in cb_nodes if other != n):
            unique_cbs.append(n)
            
    # Keep track of blocks to avoid duplicates (desktop/mobile view duplicates)
    seen_blocks = []

    for cb in unique_cbs:
        # Walk up the tree to find the review container (typically 4-6 levels up)
        block = cb.parent
        for _ in range(5): 
            if block and block.parent:
                block = block.parent

        if block in seen_blocks:
            continue
        seen_blocks.append(block)

        # 1. RATING: look for a div/span containing "1"-"5" and having an svg/img
        rating = ""
        for tag in block.find_all(['div', 'span']):
            txt = tag.get_text(strip=True)
            if txt in ['1', '2', '3', '4', '5'] and (tag.find('svg') or tag.find('img')):
                rating = txt
                break
                
        # 2. Extract all text pieces to find Title and Body
        all_texts = []
        for el in block.find_all(['p', 'div', 'span']):
            # Only get leaf-ish nodes to avoid duplicating text of parent containers
            if not el.find_all(['p', 'div']): 
                txt = el.get_text(strip=True)
                if txt and txt not in ['READ MORE', 'Certified Buyer', rating] and "ago" not in txt and not re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', txt):
                    # Filtering out things that look like numbers (likes/dislikes count) or single characters
                    if not re.match(r'^[\d,]+$', txt) and len(txt) > 1:
                        if txt not in all_texts:
                            all_texts.append(txt)
                        
        if not all_texts:
            continue
            
        # 3. BODY & TITLE: sort text by length. The longest is the body. The shortest/first is title.
        sorted_texts = sorted(all_texts, key=len, reverse=True)
        body = sorted_texts[0]
        
        # Typically the title is the first text in the DOM order (before body)
        title = ""
        for txt in all_texts:
            if txt != body and len(txt) < 100:
                title = txt
                break
                
        # 4. REVIEWER: Name usually appears near "Certified Buyer"
        reviewer = ""
        for el in block.find_all(['p', 'span']):
            txt = el.get_text(strip=True)
            if txt and len(txt) < 40 and txt not in ['READ MORE', 'Certified Buyer', rating, title, body]:
                if "ago" not in txt and not re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', txt) and not re.match(r'^[\d,]+$', txt):
                    if txt not in all_texts or len(all_texts) <= 3:
                        reviewer = txt
                        break

        if body or title:
            # Clean up the body if READ MORE mistakenly got attached
            body = body.replace('READ MORE', '').strip()
            
            reviews.append({
                "Rating":          rating,
                "Review_Title":    title,
                "Review_Body":     body,
                "Reviewer":        reviewer,
                "Certified_Buyer": True
            })

    # Remove strict identical duplicates manually
    unique_reviews = []
    for r in reviews:
        if r not in unique_reviews:
            unique_reviews.append(r)
            
    return unique_reviews

def scrape_all_reviews(driver) -> list[dict]:
    all_reviews = []
    
    # Get the base URL from the first page and strip any existing page parameter
    current_url = driver.current_url
    base_url = re.sub(r"&page=\d+", "", current_url)

    for page in range(1, MAX_PAGES + 1):
        print(f"  → Loading and scrolling Page {page} ...")
        
        # Navigate directly to the page number
        page_url = f"{base_url}&page={page}"
        if current_url != page_url:
            driver.get(page_url)
            # Short wait for initial load before scrolling
            time.sleep(2)

        # Scroll down blindly to ensure all reviews load before scraping
        for _ in range(8):
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(0.4)
            
        time.sleep(1) # Final JS render pause

        soup = BeautifulSoup(driver.page_source, "html.parser")
        page_reviews = extract_reviews_from_page(soup)

        if not page_reviews:
            print(f"  ⚠️  No reviews found on page {page}. Stopping.")
            break

        print(f"  ✅ {len(page_reviews)} reviews found.")
        all_reviews.extend(page_reviews)

        # Optional delay between pages
        time.sleep(random.uniform(*DELAY_RANGE))

    return all_reviews


# ---------------------------
# STEP 4 — Save output
# ---------------------------

def save_reviews(reviews: list[dict], product_title: str) -> str:
    if not reviews:
        print("⚠️  No reviews to save.")
        return ""

    df = pd.DataFrame(reviews)
    # Make absolutely sure there are no invalid characters for Windows paths
    safe_title = re.sub(r"[^a-zA-Z0-9_-]", "_", product_title)[:40].strip("_")
    # Replace multiple spaces/underscores with a single underscore
    safe_title = re.sub(r"_+", "_", safe_title)
    
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = f"flipkart_reviews_{safe_title}_{timestamp}.xlsx"

    os.makedirs("raw", exist_ok=True)
    filepath = os.path.join("raw", filename)
    df.to_excel(filepath, index=False)
    print(f"\n✅ Saved {len(df)} reviews → {filepath}")
    return filepath


# ---------------------------
# MAIN
# ---------------------------

if __name__ == "__main__":
    query = input("Enter product name: ").strip()
    if not query:
        print("❌ No query entered.")
        sys.exit(1)

    print("🚀 Launching browser ...")
    driver = create_driver()

    try:
        product_title = click_first_product_and_switch(driver, query)
        
        if not product_title:
            print("❌ No products found on search page.")
            sys.exit(1)

        success = navigate_to_reviews_page(driver)
        if not success:
            print("❌ Could not reach the dedicated reviews page.")
            sys.exit(1)

        print(f"🚀 Scraping up to {MAX_PAGES} pages ...\n")
        reviews = scrape_all_reviews(driver)
        
        save_reviews(reviews, product_title)
        print(f"📊 Total: {len(reviews)} reviews collected.")
        
    finally:
        driver.quit()
        print("🛑 Browser closed.")