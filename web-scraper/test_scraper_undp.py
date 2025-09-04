#!/usr/bin/env python3

import asyncio
import json
from scraper import WebScraper

async def test_undp_scraping():
    """Test complete scraping workflow on UNDP site"""
    
    print("🚀 Starting UNDP scraping test...")
    
    # Create scraper instance
    scraper = WebScraper("websites.json", headless=False)  # Non-headless to see what happens
    
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
        
        # Scrape just UNDP
        projects = await scraper.scrape_website(undp_config)
        
        print(f"\\n📊 Results:")
        print(f"  Total projects found: {len(projects)}")
        
        if projects:
            print("\\n📋 Sample projects:")
            for i, project in enumerate(projects[:3]):  # Show first 3
                print(f"  {i+1}. {project.get('title', 'No title')[:80]}...")
                print(f"     Reference: {project.get('reference', 'N/A')}")
                print(f"     Office: {project.get('office', 'N/A')}")
                print(f"     Deadline: {project.get('deadline', 'N/A')}")
                if 'documents' in project:
                    print(f"     Documents: {len(project['documents'])} files")
                print()
        
        # Save results
        with open('test_undp_results.json', 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Results saved to test_undp_results.json")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await scraper.close()
        print("🧹 Scraper closed")

if __name__ == '__main__':
    asyncio.run(test_undp_scraping())
