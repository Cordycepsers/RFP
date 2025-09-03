#!/usr/bin/env python3

import asyncio
import json
import sys
from playwright.async_api import async_playwright

async def test_selectors_only(site_name):
    """Ultra-fast selector testing without full page load"""
    
    sites = {
        'undp': 'UNDP Procurement Notices',
        'relief': 'ReliefWeb', 
        'ungm': 'UNGM UN Global Marketplace',
        'save': 'Save the Children',
        'global': 'The Global Fund'
    }
    
    if site_name not in sites:
        print(f"❌ Unknown site: {site_name}")
        return
    
    # Load config
    with open('websites.json', 'r') as f:
        config = json.load(f)
    
    # Find config
    target_name = sites[site_name]
    website_config = None
    for site in config['websites']:
        if target_name in site.get('name', ''):
            website_config = site
            break
    
    if not website_config:
        print(f"❌ Config not found")
        return
    
    print(f"⚡ Ultra-fast selector test: {site_name.upper()}")
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    
    try:
        # Navigate with short timeout
        await page.goto(website_config['url'], timeout=5000)
        
        # Quick search form if needed
        if website_config.get('searchForm', {}).get('enabled'):
            button = await page.query_selector(website_config['searchForm']['submitButton'])
            if button:
                await button.click()
                await page.wait_for_timeout(1500)  # Minimal wait
        
        # Test each selector
        selectors = website_config.get('selectors', {})
        
        # Container
        container_sel = selectors.get('listContainer', 'body')
        container = await page.query_selector(container_sel)
        container_status = "✅" if container else "❌"
        print(f"📦 Container: {container_status} {container_sel}")
        
        if container:
            # Items
            item_sel = selectors['listItems']['container']
            items = await page.query_selector_all(item_sel)
            print(f"📋 Items: {len(items)} found with {item_sel}")
            
            if items:
                # Test key selectors on first item
                first_item = items[0]
                
                for field, selector in selectors['listItems'].items():
                    if field == 'container':
                        continue
                    
                    elem = await first_item.query_selector(selector)
                    status = "✅" if elem else "❌"
                    print(f"  {field}: {status} {selector}")
        
        print("⚡ Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python selector_test.py [undp|relief|ungm|save|global]")
        sys.exit(1)
    
    asyncio.run(test_selectors_only(sys.argv[1]))
