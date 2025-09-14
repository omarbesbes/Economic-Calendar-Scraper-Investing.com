#!/usr/bin/env python3
"""
Quick test to verify ChromeDriver setup works
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def test_driver_creation():
    """Test if we can create a driver successfully"""
    print("🧪 Testing driver creation...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Try Homebrew ChromeDriver
        print("🔄 Trying Homebrew ChromeDriver...")
        service = Service("/opt/homebrew/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test navigation
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ Success! Page title: {title}")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    test_driver_creation()
