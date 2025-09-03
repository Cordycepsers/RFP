#!/usr/bin/env python3

import asyncio
import json
from playwright.async_api import async_playwright
from scraper import WebScraper

async def test_ungm_updated():
    """Test the updated UNGM scraper with new selectors and search form submission."""
    
    print("🧪 Testing Updated UNGM Scraper")
    print("=" * 50)
    
    # Load configuration
    with open('websites.json', 'r') as f:
        config = json.load(f)
    
    # Find UNGM configuration
    ungm_config = None
    for website in config['websites']:
        if website.get('name') == 'UNGM UN Global Marketplace':
            ungm_config = website
            break
    
    if not ungm_config:
        print("❌ UNGM configuration not found")
        return
    
    print(f"✅ Found UNGM configuration (ID: {ungm_config['id']})")
    print(f"📍 URL: {ungm_config['url']}")
    
    # Initialize scraper
    scraper = WebScraper(headless=True)
    await scraper.initialize()
    
    try:
        print(f"\n🌐 Navigating to {ungm_config['url']}...")
        page = await scraper.page.goto(ungm_config['url'], wait_until='networkidle', timeout=15000)
        await scraper.page.wait_for_timeout(2000)
        
        # Check if search form submission is needed
        if ungm_config.get('searchForm', {}).get('enabled'):
            print("🔍 Submitting search form...")
            search_button = ungm_config['searchForm']['submitButton']
            
            button = await scraper.page.query_selector(search_button)
            if button:
                print(f"✅ Found search button: {search_button}")
                await button.click()
                await scraper.page.wait_for_timeout(ungm_config['searchForm']['waitAfterSubmit'])
                print("✅ Search form submitted, waiting for results...")
            else:
                print(f"❌ Search button not found: {search_button}")
        
        # Test scraping with the new selectors
        selectors = ungm_config['selectors']
        
        print(f"\n📊 Looking for results container: {selectors['listContainer']}")
        container = await scraper.page.query_selector(selectors['listContainer'])
        
        if not container:
            print(f"❌ Results container not found: {selectors['listContainer']}")
            return
        
        print("✅ Results container found!")
        
        # Get all result items
        item_selector = selectors['listItems']['container']
        print(f"🔍 Looking for result items: {item_selector}")
        
        items = await scraper.page.query_selector_all(item_selector)
        print(f"📋 Found {len(items)} result items")
        
        if len(items) == 0:
            print("❌ No result items found")
            return
        
        # Test extracting data from first few items
        print(f"\n📝 Testing data extraction from first {min(5, len(items))} items:")
        print("-" * 60)
        
        extracted_projects = []
        item_selectors = selectors['listItems']
        
        for i, item in enumerate(items[:5]):
            project_data = {}
            
            # Extract each field
            for field, selector in item_selectors.items():
                if field in ['container']:
                    continue
                
                try:
                    element = await item.query_selector(selector)
                    if element:
                        if field == 'clickTarget':
                            # For links, get href
                            href = await element.get_attribute('href')
                            if href and not href.startswith('http'):
                                # Convert relative to absolute URL
                                href = f"https://www.ungm.org{href}" if href.startswith('/') else href
                            project_data[field] = href
                        else:
                            # For text content
                            text = await element.inner_text()
                            project_data[field] = text.strip() if text else ""
                    else:
                        project_data[field] = f"[NOT FOUND: {selector}]"
                except Exception as e:
                    project_data[field] = f"[ERROR: {str(e)}]"
            
            extracted_projects.append(project_data)
            
            print(f"\\n🎯 Project {i+1}:")
            print(f"  Title: {project_data.get('title', 'N/A')}")
            print(f"  Organization: {project_data.get('organization', 'N/A')}")
            print(f"  Deadline: {project_data.get('deadline', 'N/A')}")
            print(f"  Reference: {project_data.get('reference', 'N/A')}")
            print(f"  Link: {project_data.get('clickTarget', 'N/A')}")
        
        # Test keyword filtering
        if ungm_config.get('keywordFiltering', {}).get('enabled'):
            print(f"\n🔍 Testing keyword filtering...")
            keywords = ungm_config['keywordFiltering']['keywords']
            print(f"Keywords: {', '.join(keywords[:10])}...")
            
            media_projects = []
            for project in extracted_projects:
                title = project.get('title', '').lower()
                if any(keyword.lower() in title for keyword in keywords):
                    media_projects.append(project)
            
            print(f"📊 Found {len(media_projects)} media-related projects out of {len(extracted_projects)} total")
            
            if media_projects:
                print("\\n🎬 Media-related projects:")
                for i, project in enumerate(media_projects):
                    print(f"  {i+1}. {project.get('title', 'N/A')}")
        
        print(f"\n✅ UNGM scraper test completed successfully!")
        print(f"📈 Total projects found: {len(items)}")
        print(f"📊 Sample projects extracted: {len(extracted_projects)}")
        
        # Save sample results for review
        with open('ungm_test_results.json', 'w') as f:
            json.dump({
                'total_items_found': len(items),
                'sample_projects': extracted_projects,
                'test_timestamp': asyncio.get_event_loop().time()
            }, f, indent=2)
        
        print("💾 Sample results saved to ungm_test_results.json")
        
    except Exception as e:
        print(f"❌ Error during UNGM scraping test: {str(e)}")
        # Take screenshot for debugging
        await scraper.page.screenshot(path='ungm_error_debug.png')
        print("📸 Error screenshot saved to ungm_error_debug.png")
    
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(test_ungm_updated())
