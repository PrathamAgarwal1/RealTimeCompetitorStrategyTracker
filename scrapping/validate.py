"""
Validation script to test all scraping modules
"""
import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import requests
        print("✅ requests")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas")
    except ImportError as e:
        print(f"❌ pandas: {e}")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✅ beautifulsoup4")
    except ImportError as e:
        print(f"❌ beautifulsoup4: {e}")
        return False
    
    try:
        from selenium import webdriver
        print("✅ selenium")
    except ImportError as e:
        print(f"❌ selenium: {e}")
        return False
    
    try:
        import openpyxl
        print("✅ openpyxl")
    except ImportError as e:
        print(f"❌ openpyxl: {e}")
        return False
    
    return True

def test_directory_structure():
    """Test if required directories exist"""
    print("\n🔍 Testing directory structure...")
    
    if not os.path.exists("raw"):
        print("❌ 'raw' directory not found")
        return False
    print("✅ 'raw' directory exists")
    
    return True

def test_script_syntax():
    """Test if all Python scripts have valid syntax"""
    print("\n🔍 Testing script syntax...")
    
    scripts = [
        "flipkart_scapper.py",
        "amazon_scrapper.py",
        "save_cookies.py",
        "scrape_reviews_with_cookies.py"
    ]
    
    for script in scripts:
        if not os.path.exists(script):
            print(f"❌ {script} not found")
            return False
        
        try:
            with open(script, 'r', encoding='utf-8') as f:
                compile(f.read(), script, 'exec')
            print(f"✅ {script} - syntax valid")
        except SyntaxError as e:
            print(f"❌ {script} - syntax error: {e}")
            return False
    
    return True

def main():
    print("=" * 60)
    print("🚀 SCRAPING SCRIPTS VALIDATION")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Run tests
    all_tests_passed &= test_imports()
    all_tests_passed &= test_directory_structure()
    all_tests_passed &= test_script_syntax()
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("✅ ALL VALIDATION TESTS PASSED!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("1. For Flipkart price scraping:")
        print("   python flipkart_scapper.py")
        print("\n2. For Amazon price scraping:")
        print("   python amazon_scrapper.py")
        print("\n3. For Amazon review scraping:")
        print("   a) First save cookies: python save_cookies.py")
        print("   b) Then scrape reviews: python scrape_reviews_with_cookies.py")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please fix the issues above")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
