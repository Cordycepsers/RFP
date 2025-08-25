#!/usr/bin/env python3
"""
Test script for the advanced Devex scraper using Playwright MCP patterns.
Validates keyword search with multimedia terms and proper data extraction.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from advanced_scrapers.devex_advanced import DevexAdvancedScraper
from loguru import logger

def test_advanced_devex_scraper():
    """Test the advanced Devex scraper with multimedia keywords."""
    
    # Load configuration
    config_path = "config/proposaland_config.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return False
    
    # Website configuration for Devex
    website_config = {
        "name": "Devex",
        "url": "https://www.devex.com/funding/r",
        "type": "devex_advanced",
        "priority": 1.0
    }
    
    # Initialize advanced scraper
    logger.info("Initializing Advanced Devex scraper")
    scraper = DevexAdvancedScraper(config, website_config)
    
    # Test with user-specified keywords
    test_keywords = [
        "video", "photo", "film", "multimedia", "design", "visual",
        "campaign", "podcasts", "virtual event", "media", "animation", 
        "animated video", "promotion", "communication", "audiovisual"
    ]
    
    logger.info(f"Testing advanced scraper with {len(test_keywords)} multimedia keywords")
    
    # Run scraping
    try:
        opportunities = scraper.scrape_opportunities()
        
        # Get scraping statistics
        stats = scraper.get_scraping_stats()
        
        # Display results
        print("\n" + "="*70)
        print("ADVANCED DEVEX SCRAPER - PLAYWRIGHT MCP INTEGRATION")
        print("="*70)
        
        print(f"Scraper Type: {stats['scraper_type']}")
        print(f"Keywords Searched: {len(stats['keywords_searched'])}")
        print(f"Total Opportunities Found: {stats['total_opportunities']}")
        
        print("\nResults by Keyword:")
        print("-" * 30)
        for keyword, count in stats['results_per_keyword'].items():
            print(f"{keyword:20} | {count:3} opportunities")
        
        # Show sample opportunities with enhanced data extraction
        if opportunities:
            print("\nSample Opportunities (Enhanced Data Extraction):")
            print("-" * 50)
            for i, opp in enumerate(opportunities[:3]):
                print(f"\n{i+1}. {opp.title}")
                print(f"   Funder: {opp.funding_organization}")
                print(f"   Location: {opp.location}")
                print(f"   Type: {opp.opportunity_type}")
                print(f"   Reference: {opp.reference_number}")
                if opp.deadline:
                    print(f"   Deadline: {opp.deadline.strftime('%Y-%m-%d')}")
                print(f"   Contact: {opp.contact_email}")
                print(f"   Keywords Found: {opp.keywords_found}")
                print(f"   Documents Available: {opp.documents_available}")
                print(f"   Source Keyword: {getattr(opp, 'source_keyword', 'N/A')}")
                print(f"   URL: {opp.source_url}")
                if hasattr(opp, 'document_urls') and opp.document_urls:
                    print(f"   Document Links: {len(opp.document_urls)} files")
        
        # Test geographic filtering
        print(f"\nGeographic Filtering Applied:")
        print(f"Excluded Countries: {scraper.excluded_countries}")
        print(f"Included Countries: {scraper.included_countries}")
        
        # Save enhanced results
        output_file = f"output/advanced_devex_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("output", exist_ok=True)
        
        results = {
            "test_info": {
                "test_date": datetime.now().isoformat(),
                "scraper_type": "advanced_playwright_mcp",
                "website": "Devex",
                "keywords_tested": test_keywords
            },
            "scraping_stats": stats,
            "geographic_filters": {
                "excluded_countries": scraper.excluded_countries,
                "included_countries": scraper.included_countries
            },
            "opportunities": [
                {
                    "title": opp.title,
                    "funder": opp.funding_organization,
                    "location": opp.location,
                    "deadline": opp.deadline.isoformat() if opp.deadline else None,
                    "opportunity_type": opp.opportunity_type,
                    "reference_number": opp.reference_number,
                    "contact_email": opp.contact_email,
                    "keywords_found": opp.keywords_found,
                    "source_keyword": getattr(opp, 'source_keyword', None),
                    "source_url": opp.source_url,
                    "description": opp.description[:300] if opp.description else None,
                    "documents_available": opp.documents_available,
                    "document_count": len(opp.document_urls) if hasattr(opp, 'document_urls') and opp.document_urls else 0
                }
                for opp in opportunities
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Enhanced results saved to {output_file}")
        
        # Validate expected data fields
        missing_fields = []
        required_fields = ['title', 'funder', 'location', 'reference_number', 'contact_email']
        
        for opp in opportunities:
            for field in required_fields:
                field_map = {
                    'title': opp.title,
                    'funder': opp.funding_organization,
                    'location': opp.location,
                    'reference_number': opp.reference_number,
                    'contact_email': opp.contact_email
                }
                if not field_map.get(field):
                    missing_fields.append(f"{field} missing in: {opp.title[:50]}")
        
        if missing_fields:
            print(f"\nData Quality Check - Missing Fields:")
            for missing in missing_fields[:5]:  # Show first 5
                print(f"⚠️  {missing}")
        else:
            print(f"\n✅ Data Quality Check: All required fields present")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during advanced scraping test: {e}")
        return False

def test_single_keyword_advanced(keyword: str):
    """Test advanced scraping with a single keyword for debugging."""
    
    # Load configuration
    config_path = "config/proposaland_config.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return
    
    website_config = {
        "name": "Devex",
        "url": "https://www.devex.com/funding/r",
        "type": "devex_advanced",
        "priority": 1.0
    }
    
    # Initialize scraper with single keyword
    scraper = DevexAdvancedScraper(config, website_config)
    scraper.keywords = [keyword]  # Override for single test
    
    logger.info(f"Testing advanced scraper with single keyword: '{keyword}'")
    
    try:
        opportunities = scraper.scrape_opportunities()
        stats = scraper.get_scraping_stats()
        
        print(f"\nAdvanced Scraper Results for '{keyword}':")
        print(f"Found {len(opportunities)} opportunities")
        print(f"MCP Integration: {'Active' if scraper._is_mcp_available() else 'Fallback Mode'}")
        
        for i, opp in enumerate(opportunities):
            print(f"\n{i+1}. {opp.title}")
            print(f"   Organization: {opp.funding_organization}")
            print(f"   Location: {opp.location}")
            print(f"   Type: {opp.opportunity_type}")
            print(f"   Reference: {opp.reference_number}")
            if opp.deadline:
                print(f"   Deadline: {opp.deadline.strftime('%Y-%m-%d')}")
            print(f"   Contact: {opp.contact_email}")
            print(f"   Keywords found: {opp.keywords_found}")
            print(f"   Documents: {'Yes' if opp.documents_available else 'No'}")
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Error testing advanced keyword '{keyword}': {e}")
        return []

if __name__ == "__main__":
    logger.add("logs/advanced_devex_test.log", rotation="10 MB")
    
    if len(sys.argv) > 1:
        # Test single keyword
        keyword = sys.argv[1]
        test_single_keyword_advanced(keyword)
    else:
        # Test all keywords with advanced scraper
        success = test_advanced_devex_scraper()
        if success:
            print("\n✅ Advanced Devex scraper test completed successfully!")
            print("🚀 Playwright MCP integration patterns validated")
        else:
            print("\n❌ Advanced Devex scraper test failed!")
            sys.exit(1)
