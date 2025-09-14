#!/usr/bin/env python3
"""
Test ChromeDriver setup and diagnose issues
"""

import os
import sys
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def test_chrome_installation():
    """Test if Chrome is properly installed"""
    print("🔍 Testing Chrome installation...")
    
    chrome_paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/usr/bin/google-chrome',
        '/usr/local/bin/google-chrome'
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"✅ Chrome found at: {path}")
                    print(f"   Version: {result.stdout.strip()}")
                    return True
            except Exception as e:
                print(f"❌ Error testing Chrome at {path}: {e}")
    
    print("❌ Chrome not found")
    return False

def test_chromedriver_download():
    """Test ChromeDriver download and setup"""
    print("\n🔍 Testing ChromeDriver download...")
    
    try:
        driver_manager = ChromeDriverManager()
        driver_path = driver_manager.install()
        print(f"✅ ChromeDriver downloaded to: {driver_path}")
        
        # Check if file exists and is executable
        if os.path.exists(driver_path):
            print(f"✅ ChromeDriver file exists")
            
            # Check permissions
            import stat
            file_stat = os.stat(driver_path)
            is_executable = bool(file_stat.st_mode & stat.S_IEXEC)
            print(f"   Executable: {is_executable}")
            
            if not is_executable:
                print("🔧 Making ChromeDriver executable...")
                os.chmod(driver_path, file_stat.st_mode | stat.S_IEXEC)
                print("✅ ChromeDriver is now executable")
            
            return driver_path
        else:
            print("❌ ChromeDriver file does not exist")
            return None
            
    except Exception as e:
        print(f"❌ Error downloading ChromeDriver: {e}")
        return None

def test_chromedriver_execution(driver_path):
    """Test if ChromeDriver can be executed"""
    print("\n🔍 Testing ChromeDriver execution...")
    
    try:
        result = subprocess.run([driver_path, '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ ChromeDriver executes successfully")
            print(f"   Version: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ ChromeDriver execution failed")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error executing ChromeDriver: {e}")
        return False

def test_selenium_driver():
    """Test Selenium with ChromeDriver"""
    print("\n🔍 Testing Selenium WebDriver...")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Try with webdriver-manager
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get("https://www.google.com")
            title = driver.title
            driver.quit()
            print(f"✅ Selenium WebDriver works with webdriver-manager")
            print(f"   Test page title: {title}")
            return True
        except Exception as e1:
            print(f"❌ Selenium with webdriver-manager failed: {e1}")
            
            # Try without service specification
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.get("https://www.google.com")
                title = driver.title
                driver.quit()
                print(f"✅ Selenium WebDriver works without service specification")
                print(f"   Test page title: {title}")
                return True
            except Exception as e2:
                print(f"❌ Selenium without service also failed: {e2}")
                return False
                
    except Exception as e:
        print(f"❌ General Selenium error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 ChromeDriver Diagnostic Test")
    print("=" * 50)
    
    # Test Chrome
    chrome_ok = test_chrome_installation()
    
    # Test ChromeDriver download
    driver_path = test_chromedriver_download()
    
    # Test ChromeDriver execution
    if driver_path:
        chromedriver_ok = test_chromedriver_execution(driver_path)
    else:
        chromedriver_ok = False
    
    # Test Selenium
    selenium_ok = test_selenium_driver()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"Chrome Installation: {'✅ PASS' if chrome_ok else '❌ FAIL'}")
    print(f"ChromeDriver Download: {'✅ PASS' if driver_path else '❌ FAIL'}")
    print(f"ChromeDriver Execution: {'✅ PASS' if chromedriver_ok else '❌ FAIL'}")
    print(f"Selenium WebDriver: {'✅ PASS' if selenium_ok else '❌ FAIL'}")
    
    if all([chrome_ok, driver_path, chromedriver_ok, selenium_ok]):
        print("\n🎉 All tests passed! ChromeDriver should work.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        
        if not chrome_ok:
            print("   → Install Google Chrome")
        if not chromedriver_ok:
            print("   → ChromeDriver may be blocked by macOS security")
            print("   → Try: System Preferences > Security & Privacy > Allow")

if __name__ == "__main__":
    main()
