#!/usr/bin/env python3

import asyncio
import json
from scraper import WebScraper

async def test_developmentaid_scraper():
    """Test DevelopmentAid.org Media Tenders scraper"""
    
    print("🚀 Testing DevelopmentAid.org Media Tenders scraper...")
    
    # Create scraper instance
    scraper = WebScraper("websites.json", headless=True)
    
    try:
        # Initialize scraper
        await scraper.initialize()
        print("✅ Scraper initialized")
        
        # Load config and find DevelopmentAid
        config = scraper.config
        da_config = None
        
        for website in config['websites']:
            if 'DevelopmentAid' in website['name'] or 'developmentaid.org' in website.get('url', ''):
                da_config = website
                break
        
        if not da_config:
            print("❌ DevelopmentAid configuration not found")
            return
        
        print(f"🎯 Found DevelopmentAid config: {da_config['name']}")
        print(f"🔗 URL: {da_config['url']}")
        print(f"📝 Note: {da_config.get('note', 'N/A')}")
        print(f"📅 Using 7-day date filter for recent projects")
        
        # Scrape DevelopmentAid
        projects = await scraper.scrape_website(da_config)
        
        print(f"\n📊 Results:")
        print(f"  Total relevant projects found: {len(projects)}")
        
        if projects:
            print(f"\n📋 Found {len(projects)} media-related projects:")
            for i, project in enumerate(projects[:10]):  # Show first 10
                print(f"  {i+1}. {project.get('title', 'No title')[:80]}...")
                print(f"     Organization: {project.get('organization', 'N/A')}")
                print(f"     Deadline: {project.get('deadline', 'N/A')}")
                print(f"     Published: {project.get('published', 'N/A')}")
                print(f"     Reference: {project.get('reference', 'N/A')}")
                print()
                
            if len(projects) > 10:
                print(f"  ... and {len(projects) - 10} more projects")
        else:
            print("  No media-related projects found in the current results")
        
        # Save results
        filename = 'test_developmentaid_results.json'
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
    asyncio.run(test_developmentaid_scraper())
