#!/usr/bin/env python3

import asyncio
import json
from playwright.async_api import async_playwright
import time

async def batch_test_working_sites():
    """Test all working scrapers quickly in parallel"""
    
    # Known working sites
    working_sites = ['undp', 'relief', 'ungm']
    
    print("🚀 Batch Testing Working Scrapers")
    print("=" * 40)
    
    start_time = time.time()
    results = []
    
    # Load config
    with open('websites.json', 'r') as f:
        config = json.load(f)
    
    sites_map = {
        'undp': 'UNDP Procurement Notices',
        'relief': 'ReliefWeb', 
        'ungm': 'UNGM UN Global Marketplace'
    }
    
    async def test_single_site(site_key):
        """Test a single site and return results"""
        try:
            target_name = sites_map[site_key]
            website_config = None
            
            for site in config['websites']:
                if target_name in site.get('name', ''):
                    website_config = site
                    break
            
            if not website_config:
                return {'site': site_key, 'status': 'Config not found', 'items': 0}
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate with timeout
                await page.goto(website_config['url'], wait_until='networkidle', timeout=8000)
                
                # Handle search form if needed
                if website_config.get('searchForm', {}).get('enabled'):
                    button = await page.query_selector(website_config['searchForm']['submitButton'])
                    if button:
                        await button.click()
                        await page.wait_for_timeout(2000)  # Very short wait
                
                # Count items
                selectors = website_config.get('selectors', {})
                items = await page.query_selector_all(selectors['listItems']['container'])
                item_count = len(items)
                
                # Test first item title
                sample_title = "No items"
                if items:
                    first_item = items[0]
                    title_elem = await first_item.query_selector(selectors['listItems'].get('title', ''))
                    if title_elem:
                        title_text = await title_elem.inner_text()
                        sample_title = title_text.strip()[:40] + "..." if len(title_text) > 40 else title_text.strip()
                
                return {
                    'site': site_key,
                    'name': website_config['name'],
                    'status': '✅ Working',
                    'items': item_count,
                    'sample': sample_title
                }
                
            finally:
                await browser.close()
                await playwright.stop()
                
        except Exception as e:
            return {
                'site': site_key,
                'status': f'❌ Error: {str(e)[:30]}...',
                'items': 0,
                'sample': 'N/A'
            }
    
    # Run tests in parallel
    tasks = [test_single_site(site) for site in working_sites]
    results = await asyncio.gather(*tasks)
    
    # Display results
    print(f"\n📊 Test Results (Completed in {time.time() - start_time:.1f}s):")
    print("-" * 80)
    
    total_items = 0
    working_count = 0
    
    for result in results:
        status_icon = "✅" if "Working" in result['status'] else "❌"
        print(f"{status_icon} {result['site'].upper():5} | {result['items']:3} items | {result.get('sample', 'N/A')}")
        
        if "Working" in result['status']:
            working_count += 1
            total_items += result['items']
    
    print("-" * 80)
    print(f"🎯 Summary: {working_count}/{len(working_sites)} sites working | {total_items} total opportunities found")
    
    # Quick deployment status
    if working_count == len(working_sites):
        print("🚀 ALL SYSTEMS GO - Ready for production deployment!")
    else:
        print(f"⚠️ {len(working_sites) - working_count} site(s) need attention")

if __name__ == "__main__":
    asyncio.run(batch_test_working_sites())
