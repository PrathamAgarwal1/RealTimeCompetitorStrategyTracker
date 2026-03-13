import pickle
import re
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from .utils import create_stealth_driver, clean_text
import os

MAX_PAGES = 10
DELAY_RANGE = (3, 6)

def load_cookies(driver, path="amazon_cookies.pkl"):
    if not os.path.exists(path):
        return False
        
    try:
        cookies = pickle.load(open(path, "rb"))
        driver.get("https://www.amazon.in/")
        for cookie in cookies:
            if 'expiry' in cookie:
                del cookie['expiry']
            driver.add_cookie(cookie)
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Cookie load failed: {e}")
        return False

def extract_reviews_from_page(soup: BeautifulSoup) -> list[dict]:
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
            "title": clean_text(title.get_text()) if title else "",
            "body": clean_text(body.get_text()) if body else "",
            "rating": stars,
            "reviewer": clean_text(reviewer_tag.get_text()) if reviewer_tag else "",
            "date": clean_text(date_tag.get_text()) if date_tag else ""
        })

    return reviews

def fetch_amazon_reviews(asin: str, max_pages: int = MAX_PAGES) -> dict:
    if len(asin) != 10:
        return {"success": False, "error": "Invalid ASIN. Must be exactly 10 characters."}

    driver = create_stealth_driver()
    all_reviews = []
    timestamp = datetime.now().isoformat()
    url = f"https://www.amazon.in/product-reviews/{asin}/?ie=UTF8&reviewerType=all_reviews"
    
    try:
        # Load local cookies if present (expecting them in the backend directory root, or project root)
        cookie_paths = ["amazon_cookies.pkl", "../amazon_cookies.pkl", "../../amazon_cookies.pkl"]
        for p in cookie_paths:
            if load_cookies(driver, path=p):
                break
                
        driver.get(url)
        time.sleep(random.uniform(*DELAY_RANGE))

        page = 1
        while page <= max_pages:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            revs = extract_reviews_from_page(soup)

            if not revs:
                break

            all_reviews.extend(revs)

            next_btn = driver.find_elements("css selector", "li.a-last a")
            if not next_btn:
                break

            driver.execute_script("arguments[0].click();", next_btn[0])
            time.sleep(random.uniform(4, 7))
            page += 1

        formatted_data = []
        for r in all_reviews:
             formatted_data.append({
                 "product_name": asin,
                 "url": url,
                 "price": None,
                 "rating": r["rating"],
                 "review_text": r["title"] + " - " + r["body"],
                 "timestamp": r["date"] or timestamp,
                 "source": "amazon_reviews"
             })

        return {"success": True, "product_name": asin, "url": url, "data": formatted_data}

    except Exception as e:
         return {"success": False, "error": str(e)}
    finally:
        driver.quit()
