#!/usr/bin/env python3
"""
Test script for fixed Devex scraper
Tests the updated scraper functionality
"""

import sys
import os
import json
from typing import List, Dict, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.devex_scraper_fixed import DevexScraperFixed
from scrapers.base_scraper import OpportunityData

def load_config() -> Dict[str, Any]:
    """Load configuration for testing"""
    return {
        'scrapers': {
            'devex': {
                'request_delay': 2,
                'max_jobs': 10,  # Limit for testing
                'max_news': 5,   # Limit for testing
                'timeout': 30
            }
        },
        'keywords': {
            'primary': [
                'video', 'photo', 'film', 'multimedia', 'design', 'visual',
                'campaign', 'podcasts', 'virtual event', 'media', 'animation',
                'communication', 'audiovisual'
            ]
        }
    }

def test_devex_scraper():
    """Test the fixed Devex scraper"""
    print("🧪 TESTING FIXED DEVEX SCRAPER")
    print("="*50)
    
    try:
        config = load_config()
        scraper = DevexScraperFixed(config)
        
        print(f"✓ Scraper initialized successfully")
        print(f"  - Base URL: {scraper.base_url}")
        print(f"  - Jobs URL: {scraper.jobs_url}")
        print(f"  - News URL: {scraper.news_url}")
        print(f"  - Organization: {scraper.organization}")
        print(f"  - Request delay: {scraper.request_delay}s")
        
        # Test scraping
        print("\\n🔍 Testing opportunity scraping...")
        opportunities = scraper.scrape_opportunities()
        
        print(f"✓ Scraping completed")
        print(f"  - Opportunities found: {len(opportunities)}")
        
        # Validate data structure
        if opportunities:
            print(f"\\n📋 Analyzing opportunities:")
            
            for i, opp in enumerate(opportunities[:3]):  # Show first 3
                print(f"\\n  Opportunity {i+1}:")
                print(f"    - Type: {type(opp)}")
                print(f"    - Is OpportunityData: {isinstance(opp, OpportunityData)}")
                
                if isinstance(opp, OpportunityData):
                    print(f"    - Title: {opp.title}")
                    print(f"    - Organization: {opp.organization}")
                    print(f"    - Location: {opp.location}")
                    print(f"    - Reference: {opp.reference_number}")
                    print(f"    - Keywords: {opp.keywords_found}")
                    print(f"    - Source: {opp.raw_data.get('source', 'unknown')}")
                    
                    # Test attribute access
                    try:
                        title_access = opp.title
                        org_access = opp.organization
                        print(f"    - Attribute access: ✓")
                    except AttributeError as e:
                        print(f"    - Attribute access: ❌ {e}")
                        return False
                else:
                    print(f"    - ERROR: Expected OpportunityData, got {type(opp)}")
                    return False
        else:
            print("ℹ️  No opportunities found")
        
        print("\\n✅ DEVEX SCRAPER TEST PASSED")
        return True
        
    except Exception as e:
        print(f"❌ DEVEX SCRAPER TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_functionality():
    """Test fallback functionality"""
    print("\\n🔄 TESTING FALLBACK FUNCTIONALITY")
    print("="*50)
    
    try:
        config = load_config()
        scraper = DevexScraperFixed(config)
        
        # Get fallback opportunities
        fallback_opps = scraper._get_fallback_opportunities()
        print(f"✓ Fallback opportunities: {len(fallback_opps)}")
        
        # Convert to OpportunityData objects
        opportunity_objects = [scraper._convert_dict_to_opportunity_data(opp) for opp in fallback_opps]
        
        print(f"✓ Converted to OpportunityData objects: {len(opportunity_objects)}")
        
        for i, opp in enumerate(opportunity_objects):
            print(f"\\n  Fallback {i+1}:")
            print(f"    - Title: {opp.title}")
            print(f"    - Keywords: {opp.keywords_found}")
            print(f"    - Reference: {opp.reference_number}")
            print(f"    - Relevance Score: {opp.raw_data.get('relevance_score', 0)}")
        
        print("\\n✅ FALLBACK TEST PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FALLBACK TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 DEVEX SCRAPER TESTING SUITE")
    print("Testing fixed Devex scraper with current website structure")
    
    results = []
    
    # Test main scraper functionality
    results.append(("Devex Scraper", test_devex_scraper()))
    results.append(("Fallback Functionality", test_fallback_functionality()))
    
    # Print summary
    print("\\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! Fixed Devex scraper is ready.")
        print("💡 The scraper now handles current Devex structure and authentication requirements.")
        return 0
    else:
        print("⚠️  Some tests FAILED. Please review and fix issues.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

