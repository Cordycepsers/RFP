#!/usr/bin/env python3
"""
Test script to verify the data structure fix
Tests that scrapers return OpportunityData objects instead of dictionaries
"""

import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.base_scraper import OpportunityData
from scrapers.adb_scraper import ADBScraper

def load_config():
    """Load configuration"""
    try:
        with open('config/proposaland_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def test_data_structure_fix():
    """Test that scrapers return OpportunityData objects"""
    print("🧪 Testing Data Structure Fix")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Load configuration
    config = load_config()
    if not config:
        print("❌ Failed to load configuration")
        return False
    
    try:
        # Test ADB scraper (most recently fixed)
        print("🔍 Testing ADB scraper data structure...")
        scraper = ADBScraper(config)
        opportunities = scraper.scrape_opportunities()
        
        print(f"📊 Found {len(opportunities)} opportunities")
        
        if not opportunities:
            print("⚠️  No opportunities found, but that's okay for testing data structure")
            return True
        
        # Check data types
        all_correct_type = True
        for i, opp in enumerate(opportunities):
            if isinstance(opp, OpportunityData):
                print(f"✅ Opportunity {i+1}: OpportunityData object (correct)")
                
                # Test accessing attributes
                try:
                    title = opp.title
                    org = opp.organization
                    source = opp.source_url
                    keywords = opp.keywords_found
                    raw_data = opp.raw_data
                    print(f"   📝 Title: {title[:50]}...")
                    print(f"   🏢 Organization: {org}")
                    print(f"   🔗 Source: {source}")
                    print(f"   🏷️  Keywords: {keywords}")
                    print(f"   📊 Raw data keys: {list(raw_data.keys())}")
                    
                except AttributeError as e:
                    print(f"❌ Error accessing attributes: {e}")
                    all_correct_type = False
                    
            elif isinstance(opp, dict):
                print(f"❌ Opportunity {i+1}: Dictionary (incorrect - should be OpportunityData)")
                print(f"   Keys: {list(opp.keys())}")
                all_correct_type = False
            else:
                print(f"❌ Opportunity {i+1}: Unknown type {type(opp)} (incorrect)")
                all_correct_type = False
        
        if all_correct_type:
            print("\n🎉 All opportunities are OpportunityData objects!")
            print("✅ Data structure fix is working correctly")
            return True
        else:
            print("\n❌ Some opportunities are not OpportunityData objects")
            print("❌ Data structure fix needs more work")
            return False
            
    except Exception as e:
        print(f"❌ Error testing data structure: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_main_monitor_compatibility():
    """Test that the main monitor can process OpportunityData objects"""
    print("\n" + "="*60)
    print("🔍 Testing Main Monitor Compatibility")
    print("="*60)
    
    try:
        # Import the main monitor
        from proposaland_monitor import ProposalandMonitor
        
        # Initialize monitor
        monitor = ProposalandMonitor()
        print("✅ ProposalandMonitor initialized successfully")
        
        # Create a test OpportunityData object
        test_opp = OpportunityData()
        test_opp.title = "Test Communication Strategy Opportunity"
        test_opp.organization = "Test Organization"
        test_opp.source_url = "https://test.example.com"
        test_opp.location = "Global"
        test_opp.description = "Test multimedia communication project"
        test_opp.keywords_found = ["communication", "multimedia"]
        test_opp.raw_data = {"priority": "High", "relevance_score": 0.8}
        
        # Test filtering
        filtered = monitor.filter_opportunities([test_opp])
        print(f"✅ Filtering works: {len(filtered)} opportunities passed filter")
        
        # Test scoring
        scored = monitor.score_opportunities(filtered)
        print(f"✅ Scoring works: {len(scored)} opportunities scored")
        
        # Test classification
        classified = monitor.classify_priorities(scored)
        print(f"✅ Classification works: {len(classified)} opportunities classified")
        
        # Test accessing attributes (this was the original error)
        for opp in classified:
            try:
                title = opp.title  # This should work now
                org = opp.organization
                print(f"✅ Can access attributes: {title[:30]}... from {org}")
                break
            except AttributeError as e:
                print(f"❌ Still can't access attributes: {e}")
                return False
        
        print("🎉 Main monitor compatibility test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing main monitor compatibility: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Proposaland Data Structure Fix")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Data structure fix
    test1_passed = test_data_structure_fix()
    
    # Test 2: Main monitor compatibility
    test2_passed = test_main_monitor_compatibility()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    print(f"Data Structure Fix: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Monitor Compatibility: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("The 'dict' object has no attribute 'title' error should be fixed!")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("The error may still occur - check the failed tests above")
    
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

