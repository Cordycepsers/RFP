#!/usr/bin/env python3

import asyncio
import json
import sys
from playwright.async_api import async_playwright

async def quick_test_site(site_name=None):
    """Quick test of a single scraper site"""
    
    # Load config
    with open('websites.json', 'r') as f:
        config = json.load(f)
    
    # Site mapping for quick access
    sites = {
        'undp': 'UNDP Procurement Notices',
        'relief': 'ReliefWeb', 
        'ungm': 'UNGM UN Global Marketplace',
        'save': 'Save the Children',
        'global': 'The Global Fund',
        'dev': 'DevelopmentAid.org'
    }
    
    if not site_name:
        print("🚀 Quick Site Tester")
        print("Available sites:")
        for key, name in sites.items():
            print(f"  {key} -> {name}")
        print(f"\nUsage: python quick_test.py [site_key]")
        return
    
    # Find the website config
    target_name = sites.get(site_name)
    if not target_name:
        print(f"❌ Unknown site: {site_name}")
        return
    
    website_config = None
    for site in config['websites']:
        if target_name in site.get('name', ''):
            website_config = site
            break
    
    if not website_config:
        print(f"❌ Config not found for: {target_name}")
        return
    
    print(f"🧪 Quick testing: {website_config['name']}")
    print(f"📍 URL: {website_config['url']}")
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    
    try:
        # Navigate
        print("🌐 Loading page...", end=" ")
        await page.goto(website_config['url'], wait_until='networkidle', timeout=10000)
        print("✅")
        
        # Handle search form if needed
        if website_config.get('searchForm', {}).get('enabled'):
            print("🔍 Submitting search...", end=" ")
            button = await page.query_selector(website_config['searchForm']['submitButton'])
            if button:
                await button.click()
                await page.wait_for_timeout(3000)  # Shorter wait
                print("✅")
            else:
                print("❌")
        
        # Test selectors quickly
        selectors = website_config.get('selectors', {})
        container = await page.query_selector(selectors.get('listContainer', 'body'))
        
        if container:
            items = await page.query_selector_all(selectors['listItems']['container'])
            print(f"📋 Found: {len(items)} items")
            
            if len(items) > 0:
                # Test first item extraction
                first_item = items[0]
                title_elem = await first_item.query_selector(selectors['listItems'].get('title', ''))
                if title_elem:
                    title = await title_elem.inner_text()
                    print(f"📝 Sample: {title[:50]}...")
                    print("✅ WORKING")
                else:
                    print("❌ Title selector failed")
            else:
                print("⚠️ No items found")
        else:
            print("❌ Container not found")
            
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    site = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(quick_test_site(site))
