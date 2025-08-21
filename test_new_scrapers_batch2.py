#!/usr/bin/env python3
"""
Test script for new Proposaland scrapers (Batch 2)
Tests Development Aid, IUCN, and ADB scrapers
"""

import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.developmentaid_scraper import DevelopmentAidScraper
from scrapers.iucn_scraper import IUCNScraper
from scrapers.adb_scraper import ADBScraper

def load_config():
    """Load configuration"""
    try:
        with open('config/proposaland_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def test_scraper(scraper_class, scraper_name, config):
    """Test individual scraper"""
    print(f"\n{'='*60}")
    print(f"Testing {scraper_name} Scraper")
    print(f"{'='*60}")
    
    try:
        # Initialize scraper
        scraper = scraper_class(config)
        print(f"✅ {scraper_name} scraper initialized successfully")
        
        # Test connection
        print(f"🔗 Testing connection to {scraper_name}...")
        connection_ok = scraper.test_connection()
        if connection_ok:
            print(f"✅ {scraper_name} connection successful")
        else:
            print(f"⚠️  {scraper_name} connection failed or protected")
        
        # Test basic scraping (limited)
        print(f"🔍 Testing basic scraping from {scraper_name}...")
        opportunities = scraper.scrape_opportunities()
        
        print(f"📊 Found {len(opportunities)} opportunities from {scraper_name}")
        
        # Display sample opportunities
        if opportunities:
            print(f"\n📋 Sample opportunities from {scraper_name}:")
            for i, opp in enumerate(opportunities[:3]):  # Show first 3
                print(f"\n  {i+1}. {opp.get('title', 'No title')}")
                print(f"     Organization: {opp.get('organization', 'N/A')}")
                print(f"     Location: {opp.get('location', 'N/A')}")
                print(f"     Reference: {opp.get('reference_number', 'N/A')} (confidence: {opp.get('reference_confidence', 0):.2f})")
                print(f"     Priority: {opp.get('priority', 'N/A')}")
                print(f"     Score: {opp.get('relevance_score', 0):.2f}")
                
                keywords = opp.get('keywords_found', [])
                if keywords:
                    print(f"     Keywords: {', '.join(keywords[:5])}")
        
        return True, len(opportunities)
        
    except Exception as e:
        print(f"❌ Error testing {scraper_name}: {str(e)}")
        return False, 0

def main():
    """Main test function"""
    print("🚀 Testing New Proposaland Scrapers (Batch 2)")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    config = load_config()
    if not config:
        print("❌ Failed to load configuration")
        return
    
    # Test scrapers
    scrapers_to_test = [
        (DevelopmentAidScraper, "Development Aid"),
        (IUCNScraper, "IUCN"),
        (ADBScraper, "ADB")
    ]
    
    results = {}
    total_opportunities = 0
    
    for scraper_class, scraper_name in scrapers_to_test:
        success, count = test_scraper(scraper_class, scraper_name, config)
        results[scraper_name] = {
            'success': success,
            'opportunities_found': count
        }
        total_opportunities += count
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    successful_scrapers = 0
    for scraper_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{scraper_name:20} | {status} | {result['opportunities_found']:3d} opportunities")
        if result['success']:
            successful_scrapers += 1
    
    print(f"\n📈 Overall Results:")
    print(f"   • Successful scrapers: {successful_scrapers}/{len(scrapers_to_test)}")
    print(f"   • Total opportunities found: {total_opportunities}")
    print(f"   • Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if successful_scrapers == len(scrapers_to_test):
        print("\n🎉 All new scrapers are working correctly!")
    elif successful_scrapers > 0:
        print(f"\n⚠️  {successful_scrapers} out of {len(scrapers_to_test)} scrapers working")
    else:
        print("\n❌ No scrapers are working - check configuration and network")

if __name__ == "__main__":
    main()

