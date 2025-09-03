#!/usr/bin/env python3

import asyncio
import json
from scraper import WebScraper

async def test_date_filtering(days_back=7):
    """Test scraper with configurable date range"""
    
    print(f"🚀 Testing UNDP scraping with {days_back}-day date filter...")
    
    # Create scraper instance
    scraper = WebScraper("websites.json", headless=True)  # Headless for speed
    
    # Temporarily modify the date filtering
    original_method = scraper._is_recently_published
    
    def custom_date_filter(project_data, **kwargs):
        # Use the days_back from the test instead of the default
        return original_method(project_data, days_back=days_back)
    
    scraper._is_recently_published = custom_date_filter
    
    try:
        # Initialize scraper
        await scraper.initialize()
        print("✅ Scraper initialized")
        
        # Load config and find UNDP
        config = scraper.config
        undp_config = None
        
        for website in config['websites']:
            if 'UNDP' in website['name']:
                undp_config = website
                break
        
        if not undp_config:
            print("❌ UNDP configuration not found")
            return
        
        print(f"🎯 Found UNDP config: {undp_config['name']}")
        print(f"📅 Filtering for projects published within last {days_back} days")
        
        # Scrape just UNDP with limited projects for testing
        projects = await scraper.scrape_website(undp_config)
        
        print(f"\n📊 Results:")
        print(f"  Total relevant projects found: {len(projects)}")
        
        if projects:
            print(f"\n📋 Found {len(projects)} media-related projects published in last {days_back} days:")
            for i, project in enumerate(projects[:5]):  # Show first 5
                print(f"  {i+1}. {project.get('title', 'No title')[:80]}...")
                print(f"     Posted: {project.get('posted', 'N/A')}")
                print(f"     Deadline: {project.get('deadline', 'N/A')}")
                print()
        
        # Save results
        filename = f'test_undp_results_{days_back}days.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Results saved to {filename}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await scraper.close()
        print("🧹 Scraper closed")

if __name__ == '__main__':
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    asyncio.run(test_date_filtering(days))
