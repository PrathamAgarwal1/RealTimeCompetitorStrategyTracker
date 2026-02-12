import sys
sys.stdout.reconfigure(encoding='utf-8')

import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def setup_driver():
    options = Options()
    # headless disabled so you can log in manually
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

if __name__ == "__main__":
    driver = setup_driver()
    driver.get("https://www.amazon.in/")

    print("🔓 Please log in manually (enter OTP if asked).")
    print("After you’re fully logged in and your name/profile shows up, press ENTER here.")
    input("➡️ Press ENTER to save cookies once logged in... ")

    pickle.dump(driver.get_cookies(), open("amazon_cookies.pkl", "wb"))
    print("✅ Cookies saved to amazon_cookies.pkl")

    driver.quit()

