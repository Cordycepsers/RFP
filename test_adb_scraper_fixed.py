#!/usr/bin/env python3
"""
Test script for fixed ADB scraper
Tests the updated ADB scraper with improved error handling
"""

import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.adb_scraper import ADBScraper

def load_config():
    """Load configuration"""
    try:
        with open('config/proposaland_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def test_adb_scraper():
    """Test ADB scraper with improved error handling"""
    print("🚀 Testing Fixed ADB Scraper")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Load configuration
    config = load_config()
    if not config:
        print("❌ Failed to load configuration")
        return
    
    try:
        # Initialize scraper
        scraper = ADBScraper(config)
        print("✅ ADB scraper initialized successfully")
        
        # Test connection
        print("🔗 Testing connection to ADB...")
        connection_ok = scraper.test_connection()
        if connection_ok:
            print("✅ ADB connection successful (or fallback working)")
        else:
            print("⚠️  ADB connection failed")
        
        # Test scraping
        print("🔍 Testing opportunity scraping...")
        opportunities = scraper.scrape_opportunities()
        
        print(f"📊 Found {len(opportunities)} opportunities from ADB")
        
        # Display opportunities
        if opportunities:
            print("\n📋 ADB Opportunities Found:")
            for i, opp in enumerate(opportunities, 1):
                print(f"\n  {i}. {opp.get('title', 'No title')}")
                print(f"     Organization: {opp.get('organization', 'N/A')}")
                print(f"     Location: {opp.get('location', 'N/A')}")
                print(f"     Deadline: {opp.get('deadline_text', 'N/A')}")
                print(f"     Budget: {opp.get('budget_text', 'N/A')}")
                print(f"     Reference: {opp.get('reference_number', 'N/A')} (confidence: {opp.get('reference_confidence', 0):.2f})")
                print(f"     Priority: {opp.get('priority', 'N/A')}")
                print(f"     Score: {opp.get('relevance_score', 0):.2f}")
                
                keywords = opp.get('keywords_found', [])
                if keywords:
                    print(f"     Keywords: {', '.join(keywords)}")
                
                description = opp.get('description', '')
                if description and len(description) > 100:
                    print(f"     Description: {description[:100]}...")
                elif description:
                    print(f"     Description: {description}")
        
        # Test summary
        print("\n" + "="*60)
        print("📊 ADB SCRAPER TEST SUMMARY")
        print("="*60)
        
        if opportunities:
            print(f"✅ Status: WORKING")
            print(f"📈 Opportunities found: {len(opportunities)}")
            print(f"🎯 Relevant opportunities: {len([o for o in opportunities if o.get('relevance_score', 0) > 0.3])}")
            print(f"⭐ High priority opportunities: {len([o for o in opportunities if o.get('priority') in ['Critical', 'High']])}")
            
            # Check for reference numbers
            with_refs = len([o for o in opportunities if o.get('reference_number')])
            print(f"🔢 Opportunities with reference numbers: {with_refs}/{len(opportunities)}")
            
        else:
            print("⚠️  Status: NO OPPORTUNITIES FOUND")
        
        print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return len(opportunities) > 0
        
    except Exception as e:
        print(f"❌ Error testing ADB scraper: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_adb_scraper()
    if success:
        print("\n🎉 ADB scraper is working correctly!")
    else:
        print("\n❌ ADB scraper test failed")

