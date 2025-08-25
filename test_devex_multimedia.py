#!/usr/bin/env python3
"""
Test script for the enhanced Devex Playwright scraper with multimedia keywords.
Validates all specified keywords: video, photo, film, multimedia, design, visual, campaign, 
podcasts, virtual event, media, animation, animated video, promotion, communication, audiovisual
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.devex_playwright_scraper import DevexPlaywrightScraper
from loguru import logger

def test_devex_multimedia_keywords():
    """Test the Devex scraper with all multimedia keywords."""
    
    # Load configuration
    config_path = "config/proposaland_config.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return
    
    # Website configuration for Devex
    website_config = {
        "name": "Devex",
        "url": "https://www.devex.com/funding/r",
        "type": "devex_playwright",
        "priority": 1.0
    }
    
    # Initialize scraper
    logger.info("Initializing Devex Playwright scraper")
    scraper = DevexPlaywrightScraper(config, website_config)
    
    # Test keywords from user specification
    test_keywords = [
        "video", "photo", "film", "multimedia", "design", "visual",
        "campaign", "podcasts", "virtual event", "media", "animation", 
        "animated video", "promotion", "communication", "audiovisual"
    ]
    
    logger.info(f"Testing scraper with {len(test_keywords)} multimedia keywords")
    
    # Run scraping
    try:
        opportunities = scraper.scrape_opportunities()
        
        # Analyze results
        logger.info(f"Total opportunities found: {len(opportunities)}")
        
        # Group by keyword
        keyword_stats = {}
        for opp in opportunities:
            keyword = getattr(opp, 'source_keyword', 'unknown')
            if keyword not in keyword_stats:
                keyword_stats[keyword] = []
            keyword_stats[keyword].append(opp)
        
        # Print summary
        print("\n" + "="*60)
        print("DEVEX MULTIMEDIA KEYWORD SEARCH RESULTS")
        print("="*60)
        
        for keyword in test_keywords:
            count = len(keyword_stats.get(keyword, []))
            print(f"{keyword:20} | {count:3} opportunities")
        
        print(f"\nTotal unique opportunities: {len(opportunities)}")
        
        # Show sample opportunities
        if opportunities:
            print("\nSample Opportunities Found:")
            print("-" * 40)
            for i, opp in enumerate(opportunities[:5]):
                print(f"{i+1}. {opp.title}")
                print(f"   Organization: {opp.funding_organization}")
                print(f"   Location: {opp.location}")
                print(f"   Keywords: {opp.keywords_found}")
                print(f"   URL: {opp.source_url}")
                print()
        
        # Save results
        output_file = f"output/devex_multimedia_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("output", exist_ok=True)
        
        results = {
            "test_date": datetime.now().isoformat(),
            "keywords_tested": test_keywords,
            "total_opportunities": len(opportunities),
            "keyword_breakdown": {k: len(v) for k, v in keyword_stats.items()},
            "opportunities": [
                {
                    "title": opp.title,
                    "organization": opp.funding_organization,
                    "location": opp.location,
                    "deadline": opp.deadline.isoformat() if opp.deadline else None,
                    "keywords_found": opp.keywords_found,
                    "source_keyword": getattr(opp, 'source_keyword', None),
                    "source_url": opp.source_url,
                    "description": opp.description[:200] if opp.description else None
                }
                for opp in opportunities
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during scraping test: {e}")
        return False

def test_single_keyword(keyword: str):
    """Test scraping with a single keyword for debugging."""
    
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
        "url": "https://www.devex.com/",
        "type": "devex_playwright",
        "priority": 1.0
    }
    
    # Initialize scraper with single keyword
    scraper = DevexPlaywrightScraper(config, website_config)
    scraper.keywords = [keyword]  # Override keywords for single test
    
    logger.info(f"Testing single keyword: '{keyword}'")
    
    try:
        opportunities = scraper.scrape_opportunities()
        
        print(f"\nResults for keyword '{keyword}':")
        print(f"Found {len(opportunities)} opportunities")
        
        for i, opp in enumerate(opportunities[:3]):
            print(f"\n{i+1}. {opp.title}")
            print(f"   Organization: {opp.funding_organization}")
            print(f"   Location: {opp.location}")
            print(f"   Type: {getattr(opp, 'opportunity_type', 'N/A')}")
            if opp.deadline:
                print(f"   Deadline: {opp.deadline.strftime('%Y-%m-%d')}")
            print(f"   Keywords found: {opp.keywords_found}")
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Error testing keyword '{keyword}': {e}")
        return []

if __name__ == "__main__":
    logger.add("logs/devex_test.log", rotation="10 MB")
    
    if len(sys.argv) > 1:
        # Test single keyword
        keyword = sys.argv[1]
        test_single_keyword(keyword)
    else:
        # Test all keywords
        success = test_devex_multimedia_keywords()
        if success:
            print("\n✅ Devex multimedia keyword test completed successfully!")
        else:
            print("\n❌ Devex multimedia keyword test failed!")
            sys.exit(1)
