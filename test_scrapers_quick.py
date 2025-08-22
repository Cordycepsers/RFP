#!/usr/bin/env python3
"""
Quick test script for ACTED and BirdLife scrapers
Tests basic functionality without extensive scraping
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
    return {
        'scrapers': {
            'acted': {
                'request_delay': 1,
                'max_pages': 1,  # Limit to 1 page for quick test
                'timeout': 15
            },
            'birdlife': {
                'request_delay': 1,
                'timeout': 15,
                'max_jobs': 5  # Limit jobs for quick test
            }
        }
    }

def test_scraper_initialization():
    """Test that scrapers can be initialized properly"""
    print("🔧 Testing scraper initialization...")
    
    config = load_config()
    
    try:
        # Test ACTED scraper
        acted_scraper = ACTEDScraper(config)
        print(f"✓ ACTED Scraper initialized: {acted_scraper.organization}")
        
        # Test BirdLife scraper
        birdlife_scraper = BirdLifeScraper(config)
        print(f"✓ BirdLife Scraper initialized: {birdlife_scraper.organization}")
        
        return True, acted_scraper, birdlife_scraper
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False, None, None

def test_fallback_opportunities():
    """Test fallback opportunity generation"""
    print("\\n🔄 Testing fallback opportunities...")
    
    config = load_config()
    
    try:
        # Test ACTED fallback
        acted_scraper = ACTEDScraper(config)
        acted_fallback = acted_scraper._get_fallback_opportunities()
        
        print(f"✓ ACTED fallback opportunities: {len(acted_fallback)}")
        
        if acted_fallback:
            # Convert to OpportunityData and test
            opp_data = acted_scraper._convert_dict_to_opportunity_data(acted_fallback[0])
            print(f"  - First opportunity: {opp_data.title}")
            print(f"  - Type: {type(opp_data)}")
            print(f"  - Is OpportunityData: {isinstance(opp_data, OpportunityData)}")
            
            # Test attribute access
            title = opp_data.title
            org = opp_data.organization
            ref = opp_data.reference_number
            print(f"  - Attributes accessible: ✓")
        
        # Test BirdLife fallback
        birdlife_scraper = BirdLifeScraper(config)
        birdlife_fallback = birdlife_scraper._get_fallback_opportunities()
        
        print(f"✓ BirdLife fallback opportunities: {len(birdlife_fallback)}")
        
        if birdlife_fallback:
            # Convert to OpportunityData and test
            opp_data = birdlife_scraper._convert_dict_to_opportunity_data(birdlife_fallback[0])
            print(f"  - First opportunity: {opp_data.title}")
            print(f"  - Type: {type(opp_data)}")
            print(f"  - Is OpportunityData: {isinstance(opp_data, OpportunityData)}")
            
            # Test attribute access
            title = opp_data.title
            org = opp_data.organization
            ref = opp_data.reference_number
            print(f"  - Attributes accessible: ✓")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_structure():
    """Test that scrapers return proper OpportunityData objects"""
    print("\\n📋 Testing data structure...")
    
    config = load_config()
    
    try:
        acted_scraper = ACTEDScraper(config)
        
        # Get fallback opportunities (guaranteed to work)
        fallback_opps = acted_scraper._get_fallback_opportunities()
        
        # Convert to OpportunityData objects
        opportunity_objects = [acted_scraper._convert_dict_to_opportunity_data(opp) for opp in fallback_opps]
        
        print(f"✓ Converted {len(opportunity_objects)} opportunities to OpportunityData objects")
        
        # Test each object
        for i, opp in enumerate(opportunity_objects):
            if not isinstance(opp, OpportunityData):
                print(f"❌ Object {i} is not OpportunityData: {type(opp)}")
                return False
                
            # Test attribute access (this was the original error)
            try:
                title = opp.title
                org = opp.organization
                source = opp.source_url
                ref = opp.reference_number
                keywords = opp.keywords_found
                raw_data = opp.raw_data  # relevance_score is stored here
                
                print(f"  - Object {i}: All attributes accessible ✓")
                
            except AttributeError as e:
                print(f"❌ Attribute access failed on object {i}: {e}")
                return False
        
        print("✅ All data structure tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Data structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run quick tests"""
    print("⚡ QUICK SCRAPER TESTING")
    print("Testing ACTED and BirdLife scrapers (basic functionality)")
    
    results = []
    
    # Test initialization
    init_success, acted_scraper, birdlife_scraper = test_scraper_initialization()
    results.append(("Initialization", init_success))
    
    if not init_success:
        print("❌ Cannot continue - initialization failed")
        return 1
    
    # Test fallback opportunities
    fallback_success = test_fallback_opportunities()
    results.append(("Fallback Opportunities", fallback_success))
    
    # Test data structure
    structure_success = test_data_structure()
    results.append(("Data Structure", structure_success))
    
    # Print summary
    print("\\n" + "="*50)
    print("QUICK TEST SUMMARY")
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
        print("🎉 Quick tests PASSED! Scrapers basic functionality working.")
        print("💡 The scrapers should resolve the 'dict' object has no attribute 'title' error.")
        return 0
    else:
        print("⚠️  Some tests FAILED. Please review and fix issues.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

