import re
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from urllib.parse import quote_plus
from .utils import create_stealth_driver, clean_text

MAX_PAGES = 10
DELAY_RANGE = (2, 4)

def click_first_product_and_switch(driver, query: str) -> str:
    encoded = quote_plus(query)
    search_url = f"https://www.flipkart.com/search?q={encoded}"
    driver.get(search_url)
    time.sleep(3)

    product_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
    if not product_links:
        return None

    first_link = product_links[0]
    title = first_link.text or "Product"
    driver.execute_script("arguments[0].click();", first_link)
    time.sleep(3)

    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        
    time.sleep(2)
    return title

def navigate_to_reviews_page(driver):
    reviews_url = None
    for _ in range(20):
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(0.5)
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
        driver.get(reviews_url)
        return True
    else:
        current_url = driver.current_url
        if "/p/" in current_url:
            fallback_url = current_url.replace("/p/", "/product-reviews/").split("?")[0] + "?marketplace=FLIPKART&page=1"
            driver.get(fallback_url)
            return True
    return False

def extract_reviews_from_page(soup: BeautifulSoup) -> list[dict]:
    reviews = []
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

        rating = ""
        for tag in block.find_all(['div', 'span']):
            txt = tag.get_text(strip=True)
            if txt in ['1', '2', '3', '4', '5'] and (tag.find('svg') or tag.find('img')):
                rating = txt
                break
                
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
            
        sorted_texts = sorted(all_texts, key=len, reverse=True)
        body = sorted_texts[0]
        
        title = ""
        for txt in all_texts:
            if txt != body and len(txt) < 100:
                title = txt
                break
                
        reviewer = ""
        for el in block.find_all(['p', 'span']):
            txt = el.get_text(strip=True)
            if txt and len(txt) < 40 and txt not in ['READ MORE', 'Certified Buyer', rating, title, body]:
                if "ago" not in txt and not re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', txt) and not re.match(r'^[\d,]+$', txt):
                    if txt not in all_texts or len(all_texts) <= 3:
                        reviewer = txt
                        break

        if body or title:
            body = body.replace('READ MORE', '').strip()
            reviews.append({
                "rating": rating,
                "title": title,
                "text": body,
                "reviewer": reviewer,
            })

    unique_reviews = []
    for r in reviews:
        if r not in unique_reviews:
            unique_reviews.append(r)
            
    return unique_reviews

def fetch_flipkart_reviews(query: str, max_pages: int = MAX_PAGES) -> dict:
    driver = create_stealth_driver()
    all_reviews = []
    product_title = ""
    target_url = ""
    timestamp = datetime.now().isoformat()
    
    try:
        product_title = click_first_product_and_switch(driver, query)
        if not product_title:
            return {"success": False, "error": "No products found on search page."}

        target_url = driver.current_url
        success = navigate_to_reviews_page(driver)
        if not success:
            return {"success": False, "error": "Could not reach the dedicated reviews page."}

        current_url = driver.current_url
        base_url = re.sub(r"&page=\d+", "", current_url)

        for page in range(1, max_pages + 1):
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
                break

            all_reviews.extend(page_reviews)
            time.sleep(random.uniform(*DELAY_RANGE))

        # Format output
        formatted_data = []
        for r in all_reviews:
            formatted_data.append({
                "product_name": product_title,
                "url": target_url,
                "price": None, # Price usually not in review
                "rating": r["rating"],
                "review_text": r["title"] + " - " + r["text"],
                "timestamp": timestamp,
                "source": "flipkart_reviews"
            })

        return {"success": True, "product_name": product_title, "url": target_url, "data": formatted_data}
        
    except Exception as e:
         return {"success": False, "error": str(e)}
    finally:
        driver.quit()
