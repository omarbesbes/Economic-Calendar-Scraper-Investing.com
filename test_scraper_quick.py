#!/usr/bin/env python3
"""
Quick test run of the scraper with a small date range
"""

from direct_js_scraper import DirectJavaScriptScraper

def test_scraper():
    """Test scraper with small date range"""
    print("🧪 Testing scraper with small date range...")
    
    scraper = DirectJavaScriptScraper(headless=True, max_workers=1)
    
    # Test with just one small range
    result = scraper.scrape_date_range("01/01/2024", "01/31/2024", worker_id=0)
    
    print(f"📊 Scraped {result} events")
    print(f"📈 Total events in scraper: {len(scraper.all_events)}")
    
    if scraper.all_events:
        print("✅ Scraper is working!")
        # Save test results
        scraper.save_progress("test_scraper")
        return True
    else:
        print("❌ No events were scraped")
        return False

if __name__ == "__main__":
    test_scraper()
