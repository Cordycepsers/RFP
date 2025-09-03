#!/usr/bin/env python3

import json
import sys
from playwright.sync_api import sync_playwright
import time

def test_website_selectors(website_config, headless=False):
    """Test selectors for a specific website configuration"""
    
    print(f"\n🧪 Testing selectors for: {website_config['name']}")
    print(f"🌐 URL: {website_config['url']}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        
        try:
            # Navigate to the website
            print("📍 Navigating to website...")
            page.goto(website_config['url'], timeout=30000)
            page.wait_for_load_state('networkidle', timeout=10000)
            
            print(f"✅ Page loaded: {page.title()}")
            
            # Test list container selector
            selectors = website_config.get('selectors', {})
            list_container_selector = selectors.get('listContainer', '')
            
            print(f"\n🔍 Testing list container selector: {list_container_selector}")
            
            if list_container_selector:
                containers = page.query_selector_all(list_container_selector)
                print(f"📦 Found {len(containers)} list containers")
                
                if containers:
                    # Test list items within the first container
                    list_items_config = selectors.get('listItems', {})
                    container_selector = list_items_config.get('container', '')
                    
                    if container_selector:
                        print(f"🔍 Testing list items selector: {container_selector}")
                        items = page.query_selector_all(container_selector)
                        print(f"📋 Found {len(items)} list items")
                        
                        # Test extracting data from first few items
                        max_items_to_test = min(3, len(items))
                        for i in range(max_items_to_test):
                            print(f"\n📄 Testing item {i+1}:")
                            item = items[i]
                            
                            # Test each field selector
                            for field_name, field_selector in list_items_config.items():
                                if field_name == 'container':
                                    continue
                                    
                                try:
                                    element = item.query_selector(field_selector)
                                    if element:
                                        text = element.inner_text().strip()
                                        if text:
                                            print(f"  ✅ {field_name}: {text[:100]}{'...' if len(text) > 100 else ''}")
                                        else:
                                            print(f"  ⚠️  {field_name}: (element found but no text)")
                                    else:
                                        print(f"  ❌ {field_name}: selector not found - {field_selector}")
                                except Exception as e:
                                    print(f"  ❌ {field_name}: error - {str(e)}")
                    else:
                        print("❌ No list items container selector found in config")
                else:
                    print("❌ No list containers found on page")
                    
                    # Try alternative approach - look at page structure
                    print("\n🔧 Analyzing page structure...")
                    # Get some common list-like elements
                    common_selectors = [
                        'table tbody tr',
                        '.list-item', '.item', '.entry',
                        '[class*="item"]', '[class*="row"]', '[class*="entry"]',
                        'ul li', 'ol li',
                        '.opportunity', '.tender', '.notice'
                    ]
                    
                    for selector in common_selectors:
                        elements = page.query_selector_all(selector)
                        if len(elements) > 0:
                            print(f"  💡 Found {len(elements)} elements with selector: {selector}")
                            
            else:
                print("❌ No list container selector found in config")
            
            # Test keyword filtering if enabled
            keyword_config = website_config.get('keywordFiltering', {})
            if keyword_config.get('enabled', False):
                keywords = keyword_config.get('keywords', [])
                print(f"\n🔑 Keywords to match: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
                
                # Look for keywords in page content
                page_content = page.content().lower()
                found_keywords = [kw for kw in keywords if kw.lower() in page_content]
                print(f"📝 Keywords found on page: {', '.join(found_keywords[:10])}{'...' if len(found_keywords) > 10 else ''}")
            
            print(f"\n✅ Test completed for {website_config['name']}")
            
        except Exception as e:
            print(f"❌ Error testing {website_config['name']}: {str(e)}")
            
        finally:
            browser.close()

def main():
    # Load website configurations
    try:
        with open('../chrome-extension/config/websites.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ websites.json not found!")
        return
    
    websites = config.get('websites', [])
    if not websites:
        print("❌ No websites found in configuration!")
        return
    
    print(f"🚀 Starting selector validation for {len(websites)} websites")
    
    # Test specific website if provided as argument
    if len(sys.argv) > 1:
        website_name = sys.argv[1].lower()
        target_website = None
        for website in websites:
            if website_name in website['name'].lower():
                target_website = website
                break
        
        if target_website:
            test_website_selectors(target_website, headless=False)
        else:
            print(f"❌ Website containing '{website_name}' not found!")
            print("Available websites:")
            for i, website in enumerate(websites, 1):
                print(f"  {i}. {website['name']}")
    else:
        # Test first few websites
        print("🧪 Testing first 3 websites (run with website name to test specific site)")
        for i, website in enumerate(websites[:3]):
            test_website_selectors(website, headless=True)
            if i < 2:  # Small delay between tests
                time.sleep(2)

if __name__ == "__main__":
    main()
