#!/usr/bin/env python3
"""
Test script for ACTED and BirdLife scrapers
Tests functionality and validates OpportunityData object conversion
"""

import sys
import os
import json
from typing import List, Dict, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.acted_scraper import ACTEDScraper
from scrapers.birdlife_scraper import BirdLifeScraper
from scrapers.base_scraper import OpportunityData

def load_config() -> Dict[str, Any]:
    """Load configuration for testing"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'proposaland_config.json')
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return minimal config for testing
        return {
            'scrapers': {
                'acted': {
                    'request_delay': 2,
                    'max_pages': 3,
                    'timeout': 30
                },
                'birdlife': {
                    'request_delay': 2,
                    'timeout': 30,
                    'max_jobs': 10
                }
            }
        }

def test_acted_scraper():
    """Test ACTED scraper functionality"""
    print("\\n" + "="*60)
    print("TESTING ACTED SCRAPER")
    print("="*60)
    
    try:
        config = load_config()
        scraper = ACTEDScraper(config)
        
        print(f"✓ ACTED Scraper initialized successfully")
        print(f"  - Base URL: {scraper.base_url}")
        print(f"  - Organization: {scraper.organization}")
        print(f"  - Request delay: {scraper.request_delay}s")
        
        # Test scraping
        print("\\n🔍 Testing opportunity scraping...")
        opportunities = scraper.scrape_opportunities()
        
        print(f"✓ Scraping completed")
        print(f"  - Opportunities found: {len(opportunities)}")
        
        # Validate data structure
        if opportunities:
            first_opp = opportunities[0]
            print(f"\\n📋 First opportunity details:")
            print(f"  - Type: {type(first_opp)}")
            print(f"  - Is OpportunityData: {isinstance(first_opp, OpportunityData)}")
            
            if isinstance(first_opp, OpportunityData):
                print(f"  - Title: {first_opp.title}")
                print(f"  - Organization: {first_opp.organization}")
                print(f"  - Reference: {first_opp.reference_number}")
                print(f"  - Keywords: {first_opp.keywords_found}")
                print(f"  - Relevance Score: {first_opp.relevance_score}")
                
                # Test attribute access (this was causing the error)
                try:
                    title_access = first_opp.title
                    org_access = first_opp.organization
                    print("✓ Attribute access working correctly")
                except AttributeError as e:
                    print(f"❌ Attribute access error: {e}")
                    return False
            else:
                print(f"❌ ERROR: Expected OpportunityData, got {type(first_opp)}")
                return False
        else:
            print("ℹ️  No opportunities found (using fallback data)")
        
        print("✅ ACTED Scraper test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ ACTED Scraper test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_birdlife_scraper():
    """Test BirdLife scraper functionality"""
    print("\\n" + "="*60)
    print("TESTING BIRDLIFE SCRAPER")
    print("="*60)
    
    try:
        config = load_config()
        scraper = BirdLifeScraper(config)
        
        print(f"✓ BirdLife Scraper initialized successfully")
        print(f"  - Base URL: {scraper.base_url}")
        print(f"  - TeamTailor Base: {scraper.teamtailor_base}")
        print(f"  - Organization: {scraper.organization}")
        print(f"  - Request delay: {scraper.request_delay}s")
        
        # Test scraping
        print("\\n🔍 Testing opportunity scraping...")
        opportunities = scraper.scrape_opportunities()
        
        print(f"✓ Scraping completed")
        print(f"  - Opportunities found: {len(opportunities)}")
        
        # Validate data structure
        if opportunities:
            first_opp = opportunities[0]
            print(f"\\n📋 First opportunity details:")
            print(f"  - Type: {type(first_opp)}")
            print(f"  - Is OpportunityData: {isinstance(first_opp, OpportunityData)}")
            
            if isinstance(first_opp, OpportunityData):
                print(f"  - Title: {first_opp.title}")
                print(f"  - Organization: {first_opp.organization}")
                print(f"  - Reference: {first_opp.reference_number}")
                print(f"  - Location: {first_opp.location}")
                print(f"  - Keywords: {first_opp.keywords_found}")
                print(f"  - Relevance Score: {first_opp.relevance_score}")
                
                # Test attribute access
                try:
                    title_access = first_opp.title
                    org_access = first_opp.organization
                    print("✓ Attribute access working correctly")
                except AttributeError as e:
                    print(f"❌ Attribute access error: {e}")
                    return False
            else:
                print(f"❌ ERROR: Expected OpportunityData, got {type(first_opp)}")
                return False
        else:
            print("ℹ️  No opportunities found (using fallback data)")
        
        print("✅ BirdLife Scraper test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ BirdLife Scraper test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration with main system"""
    print("\\n" + "="*60)
    print("TESTING INTEGRATION")
    print("="*60)
    
    try:
        config = load_config()
        
        # Test both scrapers together
        acted_scraper = ACTEDScraper(config)
        birdlife_scraper = BirdLifeScraper(config)
        
        all_opportunities = []
        
        # Collect opportunities from both scrapers
        acted_opps = acted_scraper.scrape_opportunities()
        birdlife_opps = birdlife_scraper.scrape_opportunities()
        
        all_opportunities.extend(acted_opps)
        all_opportunities.extend(birdlife_opps)
        
        print(f"✓ Combined scraping completed")
        print(f"  - ACTED opportunities: {len(acted_opps)}")
        print(f"  - BirdLife opportunities: {len(birdlife_opps)}")
        print(f"  - Total opportunities: {len(all_opportunities)}")
        
        # Test processing like main system would
        for i, opp in enumerate(all_opportunities[:3]):  # Test first 3
            try:
                # This is what was causing the error in main system
                title = opp.title
                org = opp.organization
                ref = opp.reference_number
                print(f"  - Opportunity {i+1}: {title[:50]}... ({org})")
            except AttributeError as e:
                print(f"❌ Integration test failed on opportunity {i+1}: {e}")
                return False
        
        print("✅ Integration test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 PROPOSALAND SCRAPER TESTING")
    print("Testing ACTED and BirdLife scrapers")
    print("Validating OpportunityData object conversion")
    
    results = []
    
    # Test individual scrapers
    results.append(("ACTED Scraper", test_acted_scraper()))
    results.append(("BirdLife Scraper", test_birdlife_scraper()))
    results.append(("Integration", test_integration()))
    
    # Print summary
    print("\\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! Scrapers are ready for production.")
        return 0
    else:
        print("⚠️  Some tests FAILED. Please review and fix issues.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

