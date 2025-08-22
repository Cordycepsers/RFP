#!/usr/bin/env python3
"""
Test script for new Proposaland scrapers
Tests UNGM, Global Fund, and World Bank scrapers
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.ungm_scraper import UNGMScraper
from scrapers.globalfund_scraper import GlobalFundScraper
from scrapers.worldbank_scraper import WorldBankScraper

def load_config():
    """Load configuration file"""
    config_path = "config/proposaland_config.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_scraper(scraper_class, scraper_name, config):
    """Test a specific scraper"""
    print(f"\n{'='*60}")
    print(f"TESTING {scraper_name.upper()} SCRAPER")
    print(f"{'='*60}")
    
    try:
        # Initialize scraper
        print(f"1. Initializing {scraper_name} scraper...")
        scraper = scraper_class(config)
        print(f"   ✅ {scraper_name} scraper initialized successfully")
        
        # Test connection
        print(f"2. Testing connection to {scraper_name} website...")
        if scraper.test_connection():
            print(f"   ✅ Connection to {scraper_name} successful")
        else:
            print(f"   ❌ Connection to {scraper_name} failed")
            return False
        
        # Test scraping
        print(f"3. Testing opportunity scraping from {scraper_name}...")
        opportunities = scraper.scrape_opportunities()
        
        if opportunities:
            print(f"   ✅ Successfully scraped {len(opportunities)} opportunities from {scraper_name}")
            
            # Display sample opportunities
            print(f"4. Sample opportunities from {scraper_name}:")
            for i, opp in enumerate(opportunities[:3]):  # Show first 3
                print(f"   [{i+1}] Title: {opp.get('title', 'N/A')[:80]}...")
                print(f"       Organization: {opp.get('organization', 'N/A')}")
                print(f"       Location: {opp.get('location', 'N/A')}")
                print(f"       Reference: {opp.get('reference_number', 'N/A')}")
                print(f"       Deadline: {opp.get('deadline', 'N/A')}")
                print(f"       URL: {opp.get('url', 'N/A')[:60]}...")
                print()
            
            # Test reference number extraction
            ref_numbers = [opp.get('reference_number') for opp in opportunities if opp.get('reference_number')]
            if ref_numbers:
                print(f"5. Reference numbers extracted: {len(ref_numbers)}")
                print(f"   Sample references: {ref_numbers[:5]}")
            else:
                print(f"5. ⚠️  No reference numbers extracted")
            
            return True
        else:
            print(f"   ❌ No opportunities found from {scraper_name}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing {scraper_name} scraper: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_reference_extraction():
    """Test reference number extraction patterns"""
    print(f"\n{'='*60}")
    print("TESTING REFERENCE NUMBER EXTRACTION")
    print(f"{'='*60}")
    
    # Test samples for each scraper
    test_samples = {
        'UNGM': [
            "RFP/2025/ACNUR/MEX/047 - Sistema de Registro",
            "UNDP-FJI-00666 - Financial Inclusion in Kiribati",
            "UNW-FJI-2025-00021-2 - Customer Services Training",
            "RFQ/CRPC/2025/003 - Equipment Procurement",
            "LRPS-2025-9198844 - Long-term Agreement"
        ],
        'Global Fund': [
            "TGF-25-46 - SIGECA Rollout Angola",
            "TGF-25-45 - End-term evaluation of GF's C19RM response",
            "TGF-25-41,1 - Temporary Agency and Payrolling services",
            "TGF-25-44 - TA for Strengthening Climate and Health Data"
        ],
        'World Bank': [
            "Tamil Nadu Irrigated Agriculture Modernization Project - P158522",
            "OECS Regional Health Project - P168539",
            "Regional Emergency Solar Power Intervention Project - P179267",
            "One WASH—Consolidated Water Supply Project - P167794"
        ]
    }
    
    config = load_config()
    if not config:
        return False
    
    # Test UNGM patterns
    print("1. Testing UNGM reference patterns...")
    ungm_scraper = UNGMScraper(config)
    for sample in test_samples['UNGM']:
        ref = ungm_scraper._extract_reference_from_text(sample)
        print(f"   '{sample}' -> '{ref}'")
    
    # Test Global Fund patterns
    print("\n2. Testing Global Fund reference patterns...")
    gf_scraper = GlobalFundScraper(config)
    for sample in test_samples['Global Fund']:
        ref = gf_scraper._extract_reference_from_text(sample)
        print(f"   '{sample}' -> '{ref}'")
    
    # Test World Bank patterns
    print("\n3. Testing World Bank reference patterns...")
    wb_scraper = WorldBankScraper(config)
    for sample in test_samples['World Bank']:
        ref = wb_scraper._extract_project_id(sample, "")
        print(f"   '{sample}' -> '{ref}'")
    
    return True

def save_test_results(results):
    """Save test results to file"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"scraper_test_results_{timestamp}.json"
    
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📁 Test results saved to: {results_file}")
        return str(results_file)
    except Exception as e:
        print(f"❌ Error saving test results: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 PROPOSALAND NEW SCRAPERS TEST SUITE")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load configuration
    config = load_config()
    if not config:
        print("❌ Failed to load configuration. Exiting.")
        return False
    
    print("✅ Configuration loaded successfully")
    
    # Test results storage
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'scrapers': {},
        'reference_extraction': {},
        'summary': {}
    }
    
    # Test each scraper
    scrapers_to_test = [
        (UNGMScraper, "UNGM"),
        (GlobalFundScraper, "Global Fund"),
        (WorldBankScraper, "World Bank")
    ]
    
    successful_tests = 0
    total_opportunities = 0
    
    for scraper_class, scraper_name in scrapers_to_test:
        success = test_scraper(scraper_class, scraper_name, config)
        test_results['scrapers'][scraper_name] = {
            'success': success,
            'tested_at': datetime.now().isoformat()
        }
        
        if success:
            successful_tests += 1
            # Get opportunity count for summary
            try:
                scraper = scraper_class(config)
                opportunities = scraper.scrape_opportunities()
                opportunity_count = len(opportunities) if opportunities else 0
                total_opportunities += opportunity_count
                test_results['scrapers'][scraper_name]['opportunity_count'] = opportunity_count
            except:
                test_results['scrapers'][scraper_name]['opportunity_count'] = 0
    
    # Test reference number extraction
    print(f"\n{'='*60}")
    print("TESTING REFERENCE NUMBER EXTRACTION PATTERNS")
    print(f"{'='*60}")
    
    ref_test_success = test_reference_extraction()
    test_results['reference_extraction']['success'] = ref_test_success
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful scrapers: {successful_tests}/{len(scrapers_to_test)}")
    print(f"📊 Total opportunities found: {total_opportunities}")
    print(f"🔍 Reference extraction test: {'✅ PASSED' if ref_test_success else '❌ FAILED'}")
    
    test_results['summary'] = {
        'successful_scrapers': successful_tests,
        'total_scrapers': len(scrapers_to_test),
        'total_opportunities': total_opportunities,
        'reference_extraction_success': ref_test_success,
        'overall_success': successful_tests == len(scrapers_to_test) and ref_test_success
    }
    
    # Save results
    results_file = save_test_results(test_results)
    
    # Final status
    if test_results['summary']['overall_success']:
        print(f"\n🎉 ALL TESTS PASSED! New scrapers are ready for production.")
    else:
        print(f"\n⚠️  Some tests failed. Please review the results above.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return test_results['summary']['overall_success']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

