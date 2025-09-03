#!/usr/bin/env python3

import asyncio
import json
import os
from datetime import datetime
import re
from playwright.async_api import async_playwright
import time
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
import dateutil.parser

# Placeholder Google Services class for testing
class GoogleServices:
    def __init__(self):
        self.initialized = False
        print("⚠️ Google Services disabled for testing")
    
    def upload_file_to_drive(self, file_path, file_name, mime_type, description=""):
        print(f"📄 Mock upload: {file_name}")
        return None
    
    def append_to_sheet(self, spreadsheet_id, sheet_name, data):
        print(f"📊 Mock sheet append: {len(data)} rows")
        return None
from document_handler import DocumentHandler

load_dotenv()

class WebScraper:
    def __init__(self, config_path="websites.json", config=None, headless=True):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless
        self.config = config if config else self._load_config(config_path)
        self.google_services = None
        self.document_handler = DocumentHandler(download_dir="./downloads")
        
    def _load_config(self, config_path):
        """Load website configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Config file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            sys.exit(1)

    async def initialize(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            self.page = await self.context.new_page()
            
            # Initialize Google Services (disabled for testing)
            # self.google_services = GoogleServices()
            self.google_services = None
            
            print("✅ Browser initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            raise

    def _contains_media_keywords(self, text, keywords):
        """Check if text contains any media-related keywords"""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _is_recently_published(self, project_data, days_back=2):
        """Check if project was published within the last N days"""
        posted_date_str = project_data.get('posted', '')
        if not posted_date_str:
            # If no date available, include it to be safe
            return True
        
        try:
            # Try to parse the date string
            # Handle common formats like '03-Sep-25', '2025-09-03', etc.
            posted_date_str = posted_date_str.strip()
            
            # Try different date parsing approaches
            posted_date = None
            
            # Try parsing with dateutil (handles many formats)
            try:
                posted_date = dateutil.parser.parse(posted_date_str)
            except:
                # Try manual parsing for UNDP format like '03-Sep-25'
                try:
                    posted_date = datetime.strptime(posted_date_str, '%d-%b-%y')
                except:
                    # Try other common formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%Y']:
                        try:
                            posted_date = datetime.strptime(posted_date_str, fmt)
                            break
                        except:
                            continue
            
            if posted_date:
                # Convert to UTC if timezone-aware
                if posted_date.tzinfo is not None:
                    posted_date = posted_date.replace(tzinfo=None)
                
                # Calculate cutoff date
                cutoff_date = datetime.now() - timedelta(days=days_back)
                
                is_recent = posted_date >= cutoff_date
                if is_recent:
                    print(f"📅 Recent project: {posted_date.strftime('%Y-%m-%d')} (within {days_back} days)")
                else:
                    print(f"📅 Old project: {posted_date.strftime('%Y-%m-%d')} (older than {days_back} days)")
                
                return is_recent
            else:
                print(f"⚠️ Could not parse date: {posted_date_str}")
                return True  # Include if we can't parse the date
                
        except Exception as e:
            print(f"⚠️ Error parsing date '{posted_date_str}': {e}")
            return True  # Include if there's an error
    
    def _should_process_project(self, project_data, website_config):
        """Determine if a project should be processed based on keyword filtering and date"""
        # First check if it's recently published
        if not self._is_recently_published(project_data, days_back=2):
            return False
        
        # Then check keyword filtering
        keyword_config = website_config.get('keywordFiltering', {})
        if not keyword_config.get('enabled', False):
            return True
        
        keywords = keyword_config.get('keywords', [])
        search_fields = keyword_config.get('searchFields', ['title'])
        match_type = keyword_config.get('matchType', 'any')
        
        matches = []
        for field in search_fields:
            field_value = project_data.get(field, '')
            if field_value and self._contains_media_keywords(field_value, keywords):
                matches.append(field)
        
        if match_type == 'any':
            return len(matches) > 0
        else:  # 'all'
            return len(matches) == len(search_fields)

    async def scrape_website(self, website_config):
        """Scrape a single website based on its configuration"""
        website_name = website_config.get('name', 'Unknown')
        website_url = website_config.get('url', '')
        
        print(f"\n🌐 Starting to scrape: {website_name}")
        print(f"🔗 URL: {website_url}")
        
        if not website_url:
            print(f"❌ No URL provided for {website_name}")
            return []
        
        try:
            # Navigate to the website
            await self.page.goto(website_url, wait_until="networkidle", timeout=30000)
            print(f"✅ Successfully navigated to {website_name}")
            
            # Handle login if required
            if website_config.get('requiresLogin', False):
                await self._handle_login(website_config)
            
            # Extract projects from listing page
            projects = await self._extract_projects_from_listing(website_config)
            
            if not projects:
                print(f"⚠️ No projects found on {website_name}")
                return []
            
            print(f"📋 Found {len(projects)} projects on {website_name}")
            
            # Process each project
            processed_projects = []
            for i, project in enumerate(projects):
                try:
                    if self._should_process_project(project, website_config):
                        print(f"\n📄 Processing project {i+1}/{len(projects)}: {project.get('title', 'Unknown Title')[:60]}...")
                        
                        # Get detailed information and documents if needed
                        detailed_project = await self._get_project_details(project, website_config)
                        processed_projects.append(detailed_project)
                        
                        # Add delay between projects to be respectful
                        await asyncio.sleep(2)
                    else:
                        print(f"⏭️ Skipping project {i+1} (doesn't match keywords): {project.get('title', 'Unknown')[:60]}...")
                        
                except Exception as e:
                    print(f"❌ Error processing project {i+1}: {e}")
                    continue
            
            print(f"✅ Completed scraping {website_name}. Processed {len(processed_projects)} relevant projects.")
            return processed_projects
            
        except Exception as e:
            print(f"❌ Error scraping {website_name}: {e}")
            return []

    async def _handle_login(self, website_config):
        """Handle login if required (placeholder for manual login)"""
        print("⚠️ Login required - please log in manually if needed")
        print("Press Enter when ready to continue...")
        input()  # Wait for user to manually log in

    async def _extract_projects_from_listing(self, website_config):
        """Extract projects from the main listing page"""
        projects = []
        selectors = website_config.get('selectors', {})
        list_items_config = selectors.get('listItems', {})
        
        # Find the container for all projects
        container_selector = list_items_config.get('container', '')
        if not container_selector:
            print("❌ No container selector defined")
            return projects
            
        # Handle infinite scroll if this is UNDP or similar
        if 'undp' in website_config.get('url', '').lower() or 'procurement-notices.undp.org' in website_config.get('url', ''):
            await self._handle_infinite_scroll(container_selector)
        
        # Get all project elements after scrolling
        project_elements = await self.page.query_selector_all(container_selector)
        
        if not project_elements:
            print(f"⚠️ No project elements found with selector: {container_selector}")
            return projects
            
        print(f"📋 Found {len(project_elements)} project elements after scrolling")
        
        for element in project_elements:
            try:
                project_data = {}
                
                # Extract each field based on selectors
                for field_name, field_selector in list_items_config.items():
                    if field_name in ['container', 'clickTarget']:  # Skip these special fields
                        continue
                        
                    if field_selector:
                        try:
                            field_element = await element.query_selector(field_selector)
                            if field_element:
                                field_value = await field_element.inner_text()
                                project_data[field_name] = field_value.strip()
                        except Exception:
                            project_data[field_name] = ''
                
                # Store click target for later use
                click_target_selector = list_items_config.get('clickTarget', '')
                if click_target_selector:
                    try:
                        click_element = await element.query_selector(click_target_selector)
                        if click_element:
                            href = await click_element.get_attribute('href')
                            if href:
                                project_data['_click_target'] = href
                    except Exception:
                        pass
                
                # Add source information
                project_data['_source'] = website_config.get('name', '')
                project_data['_scraped_at'] = datetime.now().isoformat()
                
                projects.append(project_data)
                
            except Exception as e:
                print(f"❌ Error extracting project: {e}")
                continue
                
        return projects

    async def _handle_infinite_scroll(self, container_selector, max_scrolls=50):
        """Handle infinite scroll to load all projects"""
        print("🔄 Handling infinite scroll to load all projects...")
        
        previous_count = 0
        no_change_count = 0
        scroll_count = 0
        
        while scroll_count < max_scrolls and no_change_count < 3:
            # Get current count of elements
            current_elements = await self.page.query_selector_all(container_selector)
            current_count = len(current_elements)
            
            print(f"🔍 Scroll {scroll_count + 1}: Found {current_count} elements")
            
            # Check if we've reached the end (no new elements loaded)
            if current_count == previous_count:
                no_change_count += 1
                print(f"⚠️ No new elements loaded (attempt {no_change_count}/3)")
            else:
                no_change_count = 0
                
            previous_count = current_count
            
            # Scroll to bottom of page
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Wait for new content to load
            try:
                # Wait for either new elements to appear or timeout
                await self.page.wait_for_function(
                    f"document.querySelectorAll('{container_selector}').length > {current_count}",
                    timeout=5000
                )
                print("✨ New content loaded")
            except:
                print("⏳ Timeout waiting for new content")
                
            scroll_count += 1
            
            # Small delay between scrolls
            await asyncio.sleep(1)
            
        final_count = len(await self.page.query_selector_all(container_selector))
        print(f"✅ Infinite scroll complete: {final_count} total elements loaded")

    async def _get_project_details(self, project_data, website_config):
        """Get detailed project information by clicking through to detail page"""
        click_target = project_data.get('_click_target', '')
        
        if not click_target:
            print("⚠️ No click target found, using basic data only")
            return project_data
        
        try:
            # Navigate to detail page
            if click_target.startswith('http'):
                await self.page.goto(click_target, wait_until="networkidle")
            else:
                # Relative URL - construct full URL
                current_url = self.page.url
                from urllib.parse import urljoin
                full_url = urljoin(current_url, click_target)
                await self.page.goto(full_url, wait_until="networkidle")
            
            # Extract additional details from detail page
            detail_selectors = website_config.get('selectors', {}).get('detailPanel', {})
            detail_data = {}
            
            for field_name, field_selector in detail_selectors.items():
                if field_selector:
                    try:
                        field_element = await self.page.query_selector(field_selector)
                        if field_element:
                            field_value = await field_element.inner_text()
                            detail_data[field_name] = field_value.strip()
                    except Exception:
                        detail_data[field_name] = ''
            
            # Add detail data to project
            project_data['detail'] = detail_data
            
            # Generate a unique project ID for document naming
            project_id = project_data.get("reference", str(int(time.time())))
            project_id = re.sub(r'[^\w\-]', '_', project_id)  # Sanitize for filenames
            
            # Process any found documents
            documents = await self.document_handler.execute_document_workflow(self.page, website_config, project_id)
            
            # If documents were found, upload them to Google Drive and add URLs to project data
            if documents and self.google_services:
                document_urls = []
                for doc in documents:
                    drive_file = self.google_services.upload_file_to_drive(
                        file_path=doc['local_path'],
                        file_name=doc['filename'],
                        mime_type=doc['mime_type'],
                        description=f"Document for {project_id} from {website_config['name']}"
                    )
                    if drive_file and 'webViewLink' in drive_file:
                        document_urls.append({
                            'url': drive_file['webViewLink'],
                            'name': doc['filename'],
                            'type': doc.get('type', 'document')
                        })
                
                # Add document URLs to project data
                if document_urls:
                    project_data["documents"] = document_urls
            
            # Cleanup downloaded files after processing this project
            self.document_handler.cleanup_downloads(keep_files=False)
            
            return project_data
            
        except Exception as e:
            print(f"❌ Error getting project details: {e}")
            return project_data

    async def scrape_all_websites(self, max_websites=None):
        """Scrape all configured websites"""
        websites = self.config.get('websites', [])
        if max_websites:
            websites = websites[:max_websites]
            
        print(f"🚀 Starting to scrape {len(websites)} websites")
        
        all_projects = []
        
        for i, website_config in enumerate(websites):
            try:
                print(f"\n📍 Website {i+1}/{len(websites)}")
                projects = await self.scrape_website(website_config)
                
                if projects:
                    # Upload to Google Sheets if configured
                    if self.google_services:
                        await self._upload_projects_to_sheets(projects, website_config)
                    
                    all_projects.extend(projects)
                    
                # Add delay between websites to be respectful
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"❌ Error processing website {website_config.get('name', 'Unknown')}: {e}")
                continue
        
        print(f"\n🎉 Scraping complete! Total projects found: {len(all_projects)}")
        return all_projects

    async def _upload_projects_to_sheets(self, projects, website_config):
        """Upload projects to Google Sheets"""
        try:
            # Prepare data for sheets
            sheet_data = []
            for project in projects:
                row_data = [
                    project.get('title', ''),
                    project.get('reference', ''),
                    project.get('organization', ''),
                    project.get('deadline', ''),
                    project.get('published', ''),
                    project.get('_source', ''),
                    project.get('_scraped_at', ''),
                ]
                
                # Add document URLs if present
                doc_urls = []
                if 'documents' in project:
                    doc_urls = [doc['url'] for doc in project['documents']]
                row_data.append(', '.join(doc_urls))
                
                sheet_data.append(row_data)
            
            if sheet_data:
                # Use your Google Sheets service to append data
                spreadsheet_id = '1oCIum685cKVr6ZGKPk8aSe3ZPAWAg9NPWT7C2YL6ezw'  # Your sheet ID
                self.google_services.append_to_sheet(
                    spreadsheet_id=spreadsheet_id,
                    sheet_name='Sheet1',
                    data=sheet_data
                )
                print(f"✅ Uploaded {len(sheet_data)} projects to Google Sheets")
                
        except Exception as e:
            print(f"❌ Error uploading to Google Sheets: {e}")

    async def close(self):
        """Close browser and playwright instance"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
        # Final cleanup of any remaining downloaded files
        self.document_handler.cleanup_downloads(keep_files=False)

async def main():
    """Main function to run the scraper"""
    scraper = WebScraper("websites.json", headless=False)  # Set to True for headless mode
    
    try:
        await scraper.initialize()
        
        # You can limit to specific websites for testing:
        # all_projects = await scraper.scrape_all_websites(max_websites=2)
        
        # Or scrape all websites:
        all_projects = await scraper.scrape_all_websites()
        
        # Save results to file for review
        with open('scraped_projects.json', 'w', encoding='utf-8') as f:
            json.dump(all_projects, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Results saved to scraped_projects.json")
        
    except Exception as e:
        print(f"❌ Error in main: {e}")
    finally:
        await scraper.close()

if __name__ == '__main__':
    asyncio.run(main())
