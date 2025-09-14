#!/usr/bin/env python3
"""
Direct JavaScript manipulation approach for investing.com economic calendar
Bypasses the UI and directly sets dates via JavaScript
"""

import os
import sys
import stat
import time
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class DirectJavaScriptScraper:
    def __init__(self, headless=True, max_workers=2):
        self.headless = headless
        self.max_workers = max_workers
        self.all_events = []
        self.scraped_ranges = []
        self.failed_ranges = []
        self.lock = threading.Lock()
        
    def check_chrome_installation(self):
        """Check if Chrome is properly installed"""
        try:
            import subprocess
            result = subprocess.run(['google-chrome', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Chrome found: {result.stdout.strip()}")
                return True
        except:
            pass
            
        try:
            result = subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Chrome found: {result.stdout.strip()}")
                return True
        except:
            pass
        
        print("❌ Chrome not found. Please install Google Chrome.")
        return False
        
    def create_driver(self):
        """Create optimized Chrome driver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Optimization flags
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--remote-debugging-port=0")  # Use random port
        
        # Try multiple approaches to create the driver
        attempts = [
            ("System ChromeDriver", lambda: webdriver.Chrome(options=chrome_options)),
            ("Homebrew ChromeDriver", lambda: webdriver.Chrome(
                service=Service("/opt/homebrew/bin/chromedriver"), 
                options=chrome_options
            )),
            ("WebDriver Manager", lambda: webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=chrome_options
            ))
        ]
        
        for attempt_name, create_func in attempts:
            try:
                print(f"🔄 Trying {attempt_name}...")
                driver = create_func()
                driver.implicitly_wait(10)
                print(f"✅ Successfully created driver using {attempt_name}")
                return driver
            except Exception as e:
                print(f"❌ {attempt_name} failed: {e}")
                continue
        
        raise Exception("All ChromeDriver creation methods failed")
    
    def wait_for_page_load(self, driver, timeout=30):
        """Wait for page to fully load"""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(3)  # Additional wait for JavaScript
            return True
        except TimeoutException:
            return False
    
    def set_date_range_direct(self, driver, start_date, end_date):
        """Directly set date range using JavaScript without UI interaction"""
        try:
            print(f"📅 Setting date range directly: {start_date} to {end_date}")
            
            # Convert MM/DD/YYYY to YYYY-MM-DD format
            start_parts = start_date.split('/')
            end_parts = end_date.split('/')
            
            start_iso = f"{start_parts[2]}-{start_parts[0].zfill(2)}-{start_parts[1].zfill(2)}"
            end_iso = f"{end_parts[2]}-{end_parts[0].zfill(2)}-{end_parts[1].zfill(2)}"
            
            # JavaScript to directly manipulate the calendar
            js_script = f"""
            function updateCalendar() {{
                try {{
                    // Set hidden date inputs
                    var dateFromEl = document.getElementById('dateFrom');
                    var dateToEl = document.getElementById('dateTo');
                    
                    if (dateFromEl) dateFromEl.value = '{start_iso}';
                    if (dateToEl) dateToEl.value = '{end_iso}';
                    
                    // Update display
                    var displayEl = document.getElementById('widgetFieldDateRange');
                    if (displayEl) {{
                        displayEl.innerText = '{start_date} - {end_date}';
                    }}
                    
                    // Set picker value
                    var pickerEl = document.getElementById('picker');
                    if (pickerEl) {{
                        pickerEl.value = '{start_date} - {end_date}';
                    }}
                    
                    // Try to trigger calendar reload using various methods
                    
                    // Method 1: Direct AJAX call if function exists
                    if (typeof bindCalendarEvents === 'function') {{
                        bindCalendarEvents();
                    }}
                    
                    // Method 2: Trigger form submission if form exists
                    var form = document.querySelector('form[name="economicCalendarForm"]') || 
                              document.querySelector('form[id*="calendar"]') ||
                              document.querySelector('form');
                    if (form) {{
                        var submitEvent = new Event('submit');
                        form.dispatchEvent(submitEvent);
                    }}
                    
                    // Method 3: Look for reload/update functions
                    var possibleFunctions = ['reloadCalendar', 'updateCalendar', 'loadEconomicCalendar', 
                                           'refreshCalendar', 'updateEconomicCalendar', 'filterCalendar'];
                    
                    for (var funcName of possibleFunctions) {{
                        if (typeof window[funcName] === 'function') {{
                            window[funcName]();
                            return 'Updated via ' + funcName;
                        }}
                    }}
                    
                    // Method 4: Trigger change events on date inputs
                    if (dateFromEl) {{
                        var changeEvent = new Event('change', {{ bubbles: true }});
                        dateFromEl.dispatchEvent(changeEvent);
                    }}
                    
                    // Method 5: Force page reload with new parameters
                    var currentUrl = window.location.href;
                    var baseUrl = currentUrl.split('?')[0];
                    var newUrl = baseUrl + '?dateFrom=' + '{start_iso}' + '&dateTo=' + '{end_iso}';
                    
                    // Store the URL change intention
                    window.pendingUrlChange = newUrl;
                    
                    return 'Date inputs set, pending reload';
                    
                }} catch (e) {{
                    return 'Error: ' + e.message;
                }}
            }}
            
            return updateCalendar();
            """
            
            result = driver.execute_script(js_script)
            print(f"   JavaScript execution result: {result}")
            
            # If we need to reload the page with parameters
            if 'pending reload' in str(result).lower():
                new_url = driver.execute_script("return window.pendingUrlChange;")
                if new_url:
                    print(f"   🔄 Reloading page with new URL: {new_url}")
                    driver.get(new_url)
                    self.wait_for_page_load(driver)
            
            # Wait for events to load
            time.sleep(5)
            
            # Check if events are present
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "tr.js-event-item"))
                )
                print("✅ Events found after date setting")
                return True
            except TimeoutException:
                print("⚠️  No events found, trying alternative reload...")
                
                # Try reloading the page with URL parameters
                base_url = "https://www.investing.com/economic-calendar/"
                params_url = f"{base_url}?dateFrom={start_iso}&dateTo={end_iso}"
                
                print(f"   🔄 Trying URL with parameters: {params_url}")
                driver.get(params_url)
                self.wait_for_page_load(driver)
                
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "tr.js-event-item"))
                    )
                    print("✅ Events found after URL reload")
                    return True
                except TimeoutException:
                    print("❌ No events found even after URL reload")
                    return False
                
        except Exception as e:
            print(f"❌ Failed to set date range: {e}")
            return False
    
    def scroll_to_load_all_events(self, driver, max_scrolls=50):
        """Scroll down to load all events for the selected period"""
        print("📜 Loading all events by scrolling...")
        
        previous_event_count = 0
        stable_count = 0
        
        for scroll in range(max_scrolls):
            # Scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Count current events
            events = driver.find_elements(By.CSS_SELECTOR, "tr.js-event-item")
            current_count = len(events)
            
            if scroll % 10 == 0:  # Report every 10 scrolls
                print(f"   Scroll {scroll + 1}: {current_count} events loaded")
            
            # Check if no new events loaded
            if current_count == previous_event_count:
                stable_count += 1
                if stable_count >= 3:  # Stop if count stable for 3 scrolls
                    print(f"✅ All events loaded: {current_count} total")
                    break
            else:
                stable_count = 0
            
            previous_event_count = current_count
            
            # Safety check
            if current_count > 10000:
                print(f"⚠️  Large number of events ({current_count}), stopping scroll")
                break
        
        return driver.find_elements(By.CSS_SELECTOR, "tr.js-event-item")
    
    def extract_event_data(self, event_element):
        """Extract data from a single event row"""
        try:
            # Extract datetime from data attribute
            datetime_str = event_element.get_attribute("data-event-datetime")
            
            # Extract time
            time_cell = event_element.find_element(By.CSS_SELECTOR, "td.time")
            time_text = time_cell.text.strip()
            
            # Extract currency
            currency_cell = event_element.find_element(By.CSS_SELECTOR, "td.flagCur")
            currency_text = currency_cell.text.strip()
            currency = currency_text[-3:] if len(currency_text) >= 3 else currency_text
            
            # Extract importance
            importance_cell = event_element.find_element(By.CSS_SELECTOR, "td.sentiment")
            importance_title = importance_cell.get_attribute("title")
            
            importance_map = {
                "Low Volatility Expected": "Low",
                "Moderate Volatility Expected": "Medium", 
                "High Volatility Expected": "High"
            }
            importance = importance_map.get(importance_title, "Unknown")
            
            # Extract event name
            event_cell = event_element.find_element(By.CSS_SELECTOR, "td.event")
            event_link = event_cell.find_element(By.TAG_NAME, "a")
            event_name = event_link.text.strip()
            
            # Extract values (with error handling)
            actual = ""
            forecast = ""
            previous = ""
            
            try:
                actual_cell = event_element.find_element(By.CSS_SELECTOR, "td.act")
                actual = actual_cell.text.strip()
            except:
                pass
            
            try:
                forecast_cell = event_element.find_element(By.CSS_SELECTOR, "td.fore")
                forecast = forecast_cell.text.strip()
            except:
                pass
            
            try:
                previous_cell = event_element.find_element(By.CSS_SELECTOR, "td.prev")
                previous = previous_cell.text.strip()
            except:
                pass
            
            return {
                "DateTime": datetime_str,
                "Time": time_text,
                "Currency": currency,
                "Importance": importance,
                "Event": event_name,
                "Actual": actual,
                "Forecast": forecast,
                "Previous": previous
            }
            
        except Exception as e:
            return None
    
    def scrape_date_range(self, start_date, end_date, worker_id=0):
        """Scrape events for a specific date range"""
        driver = None
        range_events = []
        max_retries = 3
        
        try:
            for attempt in range(max_retries):
                try:
                    print(f"🚀 Worker {worker_id}: Starting range {start_date} to {end_date} (attempt {attempt + 1})")
                    
                    # Add delay between attempts
                    if attempt > 0:
                        delay = attempt * 2
                        print(f"⏳ Worker {worker_id}: Waiting {delay}s before retry...")
                        time.sleep(delay)
                    
                    driver = self.create_driver()
                    
                    # Load investing.com economic calendar
                    print(f"🌐 Worker {worker_id}: Loading investing.com...")
                    driver.get("https://www.investing.com/economic-calendar/")
                    
                    # Wait for page to load
                    if not self.wait_for_page_load(driver):
                        raise Exception("Page failed to load")
                    
                    # Set date range directly
                    if not self.set_date_range_direct(driver, start_date, end_date):
                        raise Exception("Failed to set date range")
                    
                    # Scroll to load all events
                    event_elements = self.scroll_to_load_all_events(driver)
                    
                    print(f"📊 Worker {worker_id}: Extracting {len(event_elements)} events...")
                    
                    # Extract data from all events
                    for i, event_element in enumerate(event_elements):
                        try:
                            event_data = self.extract_event_data(event_element)
                            if event_data:
                                range_events.append(event_data)
                                
                                if (i + 1) % 100 == 0:
                                    print(f"   Worker {worker_id}: Processed {i + 1}/{len(event_elements)} events")
                            
                        except StaleElementReferenceException:
                            continue
                        except Exception as e:
                            continue
                    
                    print(f"✅ Worker {worker_id}: Successfully extracted {len(range_events)} events")
                    
                    # Thread-safe addition to main list
                    with self.lock:
                        self.all_events.extend(range_events)
                        self.scraped_ranges.append(f"{start_date} to {end_date}")
                    
                    # Success - break the retry loop
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Worker {worker_id}: Attempt {attempt + 1} failed for range {start_date} to {end_date}: {error_msg}")
                    
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                        driver = None
                    
                    # If this was the last attempt, record the failure
                    if attempt == max_retries - 1:
                        with self.lock:
                            self.failed_ranges.append(f"{start_date} to {end_date}: {error_msg}")
                    else:
                        print(f"🔄 Worker {worker_id}: Will retry in {(attempt + 1) * 2} seconds...")
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        return len(range_events)
    
    def generate_date_ranges(self, start_year=2015, end_year=2025, months_per_range=3):
        """Generate date ranges for scraping"""
        ranges = []
        
        current_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        
        while current_date < end_date:
            range_end = current_date + timedelta(days=90)
            
            if range_end > end_date:
                range_end = end_date
            
            start_str = current_date.strftime("%m/%d/%Y")
            end_str = range_end.strftime("%m/%d/%Y")
            
            ranges.append((start_str, end_str))
            current_date = range_end + timedelta(days=1)
        
        return ranges
    
    def save_progress(self, filename_prefix="direct_js_scraper"):
        """Save current progress to CSV"""
        if self.all_events:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{len(self.all_events)}_events_{timestamp}.csv"
            
            df = pd.DataFrame(self.all_events)
            df.to_csv(filename, index=False)
            
            print(f"💾 Saved {len(self.all_events)} events to {filename}")
            return filename
        
        return None
    
    def run_scraper(self, start_year=2015, end_year=2025):
        """Main scraper execution"""
        print("=" * 80)
        print("🚀 DIRECT JAVASCRIPT ECONOMIC CALENDAR SCRAPER STARTED")
        print("=" * 80)
        
        # Check Chrome installation first
        if not self.check_chrome_installation():
            print("❌ Chrome installation check failed. Please install Google Chrome and try again.")
            return None
        
        start_time = time.time()
        
        # Generate date ranges
        date_ranges = self.generate_date_ranges(start_year, end_year)
        print(f"📅 Generated {len(date_ranges)} date ranges (3-month chunks)")
        
        # Process ranges with threading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_range = {
                executor.submit(self.scrape_date_range, start, end, i): (start, end) 
                for i, (start, end) in enumerate(date_ranges)
            }
            
            completed = 0
            for future in as_completed(future_to_range):
                start, end = future_to_range[future]
                completed += 1
                
                try:
                    events_count = future.result()
                    print(f"✅ Completed {completed}/{len(date_ranges)}: {start} to {end} ({events_count} events)")
                except Exception as e:
                    print(f"❌ Failed {completed}/{len(date_ranges)}: {start} to {end} - {e}")
                
                # Save progress every 5 completed ranges
                if completed % 5 == 0:
                    self.save_progress(f"checkpoint_direct_js")
        
        # Final results
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("📊 SCRAPING COMPLETED")
        print("=" * 80)
        print(f"⏱️  Total time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        print(f"📈 Total events: {len(self.all_events)}")
        print(f"✅ Successful ranges: {len(self.scraped_ranges)}")
        print(f"❌ Failed ranges: {len(self.failed_ranges)}")
        
        if self.all_events:
            events_per_second = len(self.all_events) / elapsed_time
            print(f"🚀 Performance: {events_per_second:.1f} events/second")
        
        # Save final results
        final_file = self.save_progress("complete_direct_js_scraper")
        
        return final_file

def main():
    """Main execution function"""
    print("🎯 Direct JavaScript Economic Calendar Scraper")
    print("=" * 50)
    
    # Create scraper
    scraper = DirectJavaScriptScraper(
        headless=True,
        max_workers=4  # Optimal number for stability
    )
    
    # Run scraper
    result_file = scraper.run_scraper(start_year=2025, end_year=2025)
    
    if result_file:
        print(f"\n🎉 Success! Data saved to: {result_file}")
    else:
        print(f"\n❌ No data was collected")

if __name__ == "__main__":
    main()
