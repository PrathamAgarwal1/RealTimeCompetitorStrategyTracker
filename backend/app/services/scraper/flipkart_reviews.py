import sys
import re
import time
import random
import os
from datetime import datetime
from urllib.parse import quote_plus

from .utils import create_stealth_driver, clean_text
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# ---------------------------
# CONFIG
# ---------------------------

MAX_PAGES = 10          # Max review pages to scrape
DELAY_RANGE = (2, 4)    # Random delay (seconds) between requests


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

def extract_reviews_from_page(soup: BeautifulSoup) -> list[dict]:
    reviews = []
    
    # Flipkart's CSS classes change constantly (they use atomic CSS now).
    # The most reliable anchor is the "Certified Buyer" text which appears in every review.
    cb_nodes = soup.find_all(lambda tag: tag.name in ['div', 'span', 'p'] and tag.get_text(strip=True) == 'Certified Buyer')
    
    unique_cbs = []
    for n in cb_nodes:
        if not any(n in list(other.descendants) for other in cb_nodes if other != n):
            unique_cbs.append(n)
            
    seen_blocks = []

    for cb in unique_cbs:
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
            if not el.find_all(['p', 'div']): 
                txt = el.get_text(strip=True)
                if txt and txt not in ['READ MORE', 'Certified Buyer', rating] and "ago" not in txt and not re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', txt):
                    if not re.match(r'^[\d,]+$', txt) and len(txt) > 1:
                        if txt not in all_texts:
                            all_texts.append(txt)
                        
        if not all_texts:
            continue
            
        # 3. BODY & TITLE: sort text by length. The longest is the body. The shortest/first is title.
        sorted_texts = sorted(all_texts, key=len, reverse=True)
        body = sorted_texts[0]
        
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

def scrape_all_reviews(driver, max_pages: int = MAX_PAGES) -> list[dict]:
    all_reviews = []
    current_url = driver.current_url
    base_url = re.sub(r"&page=\d+", "", current_url)

    for page in range(1, max_pages + 1):
        print(f"  → Loading and scrolling Page {page} ...")
        page_url = f"{base_url}&page={page}"
        if driver.current_url != page_url:
            driver.get(page_url)
            time.sleep(2)

        for _ in range(8):
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(0.4)
            
        time.sleep(1) 

        soup = BeautifulSoup(driver.page_source, "html.parser")
        page_reviews = extract_reviews_from_page(soup)

        if not page_reviews:
            print(f"  ⚠️  No reviews found on page {page}. Stopping.")
            break

        print(f"  ✅ {len(page_reviews)} reviews found.")
        all_reviews.extend(page_reviews)
        time.sleep(random.uniform(*DELAY_RANGE))

    return all_reviews


# ---------------------------
# BACKEND ENTRY POINT
# ---------------------------

def fetch_flipkart_reviews(query: str, max_pages: int = MAX_PAGES) -> dict:
    """Wrapper to make the user's scraper compatible with the backend API."""
    driver = create_stealth_driver()
    timestamp = datetime.now().isoformat()
    
    try:
        product_title = click_first_product_and_switch(driver, query)
        if not product_title:
            return {"success": False, "error": "No products found on search page."}

        target_url = driver.current_url
        success = navigate_to_reviews_page(driver)
        if not success:
            return {"success": False, "error": "Could not reach the dedicated reviews page."}

        print(f"🚀 Scraping up to {max_pages} pages ...\n")
        raw_reviews = scrape_all_reviews(driver, max_pages)
        
        # Map user's keys to standardized backend format for SQLite
        formatted_data = []
        for r in raw_reviews:
            formatted_data.append({
                "product_name": product_title,
                "url": target_url,
                "price": None,
                "rating": r["Rating"],
                "review_text": f"{r['Review_Title']} - {r['Review_Body']}" if r['Review_Title'] else r['Review_Body'],
                "timestamp": timestamp,
                "source": "flipkart_reviews",
                "metadata": str({"reviewer": r["Reviewer"], "certified": r["Certified_Buyer"]})
            })

        return {
            "success": True, 
            "product_name": product_title, 
            "url": target_url, 
            "data": formatted_data
        }
        
    except Exception as e:
         print(f"❌ Scraper error: {e}")
         return {"success": False, "error": str(e)}
    finally:
        driver.quit()
        print("🛑 Browser closed.")

if __name__ == "__main__":
    # Support for CLI usage if needed
    query = "iphone 15"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    print(f"Starting CLI scrape for: {query}")
    res = fetch_flipkart_reviews(query, max_pages=1)
    if res["success"]:
        print(f"Scraped {len(res['data'])} reviews successfully.")
    else:
        print(f"Failed: {res['error']}")