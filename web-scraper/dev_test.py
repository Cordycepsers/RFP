#!/usr/bin/env python3

import asyncio
import json
import sys
from playwright.async_api import async_playwright

async def dev_test_site(site_name, headless=False, slow=False):
    """Development mode testing with visual browser and optional slow mode"""
    
    sites = {
        'undp': 'UNDP Procurement Notices',
        'relief': 'ReliefWeb', 
        'ungm': 'UNGM UN Global Marketplace',
        'save': 'Save the Children',
        'global': 'The Global Fund',
        'dev': 'DevelopmentAid.org'
    }
    
    if not site_name:
        print("🛠 Development Mode Tester")
        print("Available sites:")
        for key, name in sites.items():
            print(f"  {key} -> {name}")
        print(f"\nUsage:")
        print(f"  python dev_test.py [site] --visual    # Visual browser")
        print(f"  python dev_test.py [site] --slow      # Slow motion")
        print(f"  python dev_test.py [site] --debug     # Visual + slow")
        return
    
    # Parse options
    visual = '--visual' in sys.argv or '--debug' in sys.argv
    slow_motion = '--slow' in sys.argv or '--debug' in sys.argv
    
    # Load config
    with open('websites.json', 'r') as f:
        config = json.load(f)
    
    # Find website config
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
    
    print(f"🛠 DEV MODE: {website_config['name']}")
    print(f"📍 URL: {website_config['url']}")
    print(f"👁 Visual: {'Yes' if visual else 'No'}")
    print(f"🐌 Slow: {'Yes' if slow_motion else 'No'}")
    
    playwright = await async_playwright().start()
    
    # Browser options
    browser_options = {
        'headless': not visual,
        'slow_mo': 2000 if slow_motion else 0
    }
    
    browser = await playwright.chromium.launch(**browser_options)
    context = await browser.new_context(viewport={'width': 1280, 'height': 720})
    page = await context.new_page()
    
    try:
        print(f"\n🌐 Navigating to site...")
        await page.goto(website_config['url'], wait_until='networkidle', timeout=15000)
        print("✅ Page loaded")
        
        # Handle search form if needed
        if website_config.get('searchForm', {}).get('enabled'):
            print("🔍 Submitting search form...")
            search_selector = website_config['searchForm']['submitButton']
            
            # Highlight the search button if visual
            if visual:
                button = await page.query_selector(search_selector)
                if button:
                    await button.scroll_into_view_if_needed()
                    await page.evaluate("""(element) => {
                        element.style.border = '3px solid red';
                        element.style.backgroundColor = 'yellow';
                    }""", button)
                    await page.wait_for_timeout(1000)
            
            button = await page.query_selector(search_selector)
            if button:
                await button.click()
                wait_time = website_config['searchForm'].get('waitAfterSubmit', 5000)
                print(f"⏰ Waiting {wait_time/1000}s for results...")
                await page.wait_for_timeout(wait_time)
                print("✅ Search completed")
            else:
                print(f"❌ Search button not found: {search_selector}")
        
        # Test selectors
        selectors = website_config.get('selectors', {})
        
        print(f"\n📊 Testing selectors...")
        
        # Container
        container_selector = selectors.get('listContainer', 'body')
        print(f"🔍 Container: {container_selector}")
        container = await page.query_selector(container_selector)
        
        if not container:
            print("❌ Container not found!")
            if visual:
                await page.wait_for_timeout(3000)
            return
        
        print("✅ Container found")
        
        # Highlight container if visual
        if visual:
            await page.evaluate("""(element) => {
                element.style.border = '2px solid blue';
                element.style.backgroundColor = 'rgba(0, 100, 255, 0.1)';
            }""", container)
        
        # Items
        item_selector = selectors['listItems']['container']
        print(f"🔍 Items: {item_selector}")
        items = await page.query_selector_all(item_selector)
        
        if not items:
            print("❌ No items found!")
            if visual:
                await page.wait_for_timeout(5000)
            return
        
        print(f"✅ Found {len(items)} items")
        
        # Highlight first few items if visual
        if visual:
            for i, item in enumerate(items[:3]):
                await page.evaluate(f"""(element) => {{
                    element.style.border = '1px solid green';
                    element.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';
                    
                    // Add item number
                    const label = document.createElement('div');
                    label.textContent = 'ITEM {i+1}';
                    label.style.cssText = 'position: absolute; top: -20px; left: 0; background: green; color: white; padding: 2px 5px; font-size: 12px; z-index: 1000;';
                    element.style.position = 'relative';
                    element.appendChild(label);
                }}""", item)
        
        # Test field extraction on first item
        if items:
            print(f"\n📝 Testing field extraction on first item:")
            first_item = items[0]
            
            for field, selector in selectors['listItems'].items():
                if field == 'container':
                    continue
                
                element = await first_item.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    truncated = text.strip()[:50] + "..." if len(text.strip()) > 50 else text.strip()
                    print(f"  ✅ {field}: {truncated}")
                    
                    # Highlight field if visual
                    if visual:
                        await page.evaluate(f"""(element) => {{
                            element.style.border = '1px solid orange';
                            element.style.backgroundColor = 'rgba(255, 165, 0, 0.2)';
                            
                            const label = document.createElement('span');
                            label.textContent = '{field.upper()}';
                            label.style.cssText = 'background: orange; color: white; padding: 1px 3px; font-size: 10px; position: absolute; top: -15px; left: 0; z-index: 1001;';
                            element.style.position = 'relative';
                            element.appendChild(label);
                        }}""", element)
                else:
                    print(f"  ❌ {field}: Not found with selector '{selector}'")
        
        print(f"\n🎯 Dev test completed!")
        
        if visual:
            print("👁 Visual browser will stay open for 10 seconds for inspection...")
            await page.wait_for_timeout(10000)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if visual:
            await page.screenshot(path=f'{site_name}_dev_error.png')
            print(f"📸 Error screenshot saved to {site_name}_dev_error.png")
            await page.wait_for_timeout(5000)
    
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    site = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(dev_test_site(site))
