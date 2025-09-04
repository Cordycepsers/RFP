#!/usr/bin/env python3

import asyncio
import json
from playwright.async_api import async_playwright
from document_handler import DocumentHandler

async def test_undp_document_workflow():
    """Test UNDP document download workflow specifically"""
    
    # Load config
    with open('websites.json', 'r') as f:
        config = json.load(f)
    
    # Find UNDP config
    undp_config = None
    for website in config['websites']:
        if 'UNDP' in website['name']:
            undp_config = website
            break
    
    if not undp_config:
        print("❌ UNDP configuration not found")
        return
    
    print(f"🧪 Testing document workflow for: {undp_config['name']}")
    
    # Initialize document handler
    doc_handler = DocumentHandler(download_dir="./test_downloads")
    
    # Initialize browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)  # Non-headless to see what's happening
    context = await browser.new_context()
    page = await context.new_page()
    
    try:
        # Navigate to UNDP page
        await page.goto(undp_config['url'], wait_until="networkidle")
        print("✅ Navigated to UNDP page")
        
        # Find first procurement notice with media keywords
        container_selector = undp_config['selectors']['listItems']['container']
        elements = await page.query_selector_all(container_selector)
        
        test_project = None
        for i, element in enumerate(elements[:5]):  # Check first 5 items
            try:
                title_elem = await element.query_selector("div:nth-child(1)")
                if title_elem:
                    title_text = await title_elem.inner_text()
                    
                    # Check if it contains media keywords
                    media_keywords = ['video', 'photo', 'film', 'multimedia', 'media', 'communication', 'production']
                    if any(keyword.lower() in title_text.lower() for keyword in media_keywords):
                        print(f"🎯 Found media project: {title_text[:60]}...")
                        test_project = element
                        break
            except Exception as e:
                print(f"Error checking element {i}: {e}")
                continue
        
        if not test_project:
            print("⚠️ No media-related projects found in first 5 items, using first available project")
            test_project = elements[0] if elements else None
        
        if not test_project:
            print("❌ No projects found")
            return
        
        # Click on the project to go to detail page
        await test_project.click()
        await page.wait_for_load_state("networkidle")
        print("✅ Navigated to project detail page")
        
        # Extract project reference for ID
        try:
            ref_elem = await page.query_selector(".reference, .ref-no")
            project_id = "test_project" if not ref_elem else await ref_elem.inner_text()
            project_id = project_id.strip().replace(" ", "_")
        except:
            project_id = "test_project"
        
        print(f"📋 Using project ID: {project_id}")
        
        # Execute document workflow
        print("🔄 Starting document download workflow...")
        documents = await doc_handler.execute_document_workflow(page, undp_config, project_id)
        
        if documents:
            print(f"✅ Successfully downloaded {len(documents)} documents:")
            for doc in documents:
                print(f"  📄 {doc['filename']} ({doc['mime_type']})")
                print(f"     Source: {doc['source_url']}")
        else:
            print("⚠️ No documents were downloaded")
            
            # Try to debug what's available on the page
            print("\n🔍 Debug: Looking for authentication links...")
            auth_links = await page.query_selector_all("a")
            auth_count = 0
            for link in auth_links[:10]:  # Check first 10 links
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and ('auth' in href.lower() or 'this link' in text.lower() or 'document' in text.lower()):
                        print(f"    🔗 Found potential auth/doc link: {text[:50]} -> {href}")
                        auth_count += 1
                except:
                    continue
            
            if auth_count == 0:
                print("    ❌ No authentication or document links found")
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    finally:
        await browser.close()
        await playwright.stop()
        
        # Clean up test downloads
        doc_handler.cleanup_downloads(keep_files=False)
        print("🧹 Cleaned up test files")

async def test_document_handler_basic():
    """Test basic document handler functionality"""
    print("\n🧪 Testing basic document handler functionality...")
    
    doc_handler = DocumentHandler(download_dir="./test_downloads")
    
    # Test filename generation
    test_url = "https://example.com/documents/project_spec.pdf"
    filename = doc_handler._generate_filename(test_url, "TEST123", "undp", 0)
    print(f"📝 Generated filename: {filename}")
    
    # Test MIME type detection
    mime_type = doc_handler._get_mime_type("test_document.pdf")
    print(f"📄 MIME type for PDF: {mime_type}")
    
    # Test extension guessing
    extension = doc_handler._guess_extension_from_url("https://example.com/download?file=report.docx")
    print(f"📄 Guessed extension: {extension}")
    
    print("✅ Basic document handler tests completed")

async def main():
    """Run all tests"""
    print("🚀 Starting document handler tests...\n")
    
    # Test basic functionality first
    await test_document_handler_basic()
    
    # Test UNDP workflow
    await test_undp_document_workflow()
    
    print("\n🎉 All tests completed!")

if __name__ == '__main__':
    asyncio.run(main())
