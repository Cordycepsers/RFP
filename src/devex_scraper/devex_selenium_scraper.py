#!/usr/bin/env python3
"""
Devex Video Tenders/Grants Selenium Scraper with Google Sheets Export
Scrapes video-related funding opportunities from Devex and exports to Google Sheets
"""

import time
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path

class DevexVideoScraper:
    """Selenium scraper for Devex video-related tenders and grants"""
    
    def __init__(self, google_credentials_path: str = None):
        self.base_url = "https://www.devex.com"
        self.video_search_url = "https://www.devex.com/funding/r?report=tender-812898&query%5B%5D=video&filter%5Btype%5D%5B%5D=grant&filter%5Btype%5D%5B%5D=tender&filter%5Bstatuses%5D%5B%5D=forecast&filter%5Bstatuses%5D%5B%5D=open&filter%5Bupdated_since%5D=2025-08-17T17%3A57%3A37.879Z&sorting%5Border%5D=desc&sorting%5Bfield%5D=updated_at#"
        
        # Setup Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        # Remove headless for debugging - uncomment for production
        # self.chrome_options.add_argument("--headless")
        
        self.driver = None
        self.wait = None
        
        # Google Sheets setup
        self.google_credentials_path = google_credentials_path
        self.gc = None
        self.sheet = None
        
        # Data storage
        self.scraped_opportunities = []
    
    def setup_driver(self):
        """Initialize the Chrome driver"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            print("✓ Chrome driver initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            return False
    
    def setup_google_sheets(self, spreadsheet_name: str = "Devex Video Opportunities"):
        """Setup Google Sheets connection"""
        try:
            if not self.google_credentials_path:
                print("⚠️ No Google credentials provided. Will save to JSON instead.")
                return False
            
            # Define the scope
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Load credentials
            creds = Credentials.from_service_account_file(
                self.google_credentials_path, 
                scopes=scope
            )
            
            # Initialize gspread client
            self.gc = gspread.authorize(creds)
            
            # Try to open existing spreadsheet or create new one
            try:
                self.sheet = self.gc.open(spreadsheet_name).sheet1
                print(f"✓ Connected to existing spreadsheet: {spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                # Create new spreadsheet
                spreadsheet = self.gc.create(spreadsheet_name)
                self.sheet = spreadsheet.sheet1
                
                # Share with your email (optional)
                # spreadsheet.share('your-email@gmail.com', perm_type='user', role='writer')
                
                print(f"✓ Created new spreadsheet: {spreadsheet_name}")
            
            # Setup headers
            headers = [
                'Title', 'Type', 'Status', 'Location', 'Deadline', 
                'Updated', 'Description', 'URL', 'Reference', 'Scraped At'
            ]
            
            # Check if headers exist, if not add them
            try:
                existing_headers = self.sheet.row_values(1)
                if not existing_headers or existing_headers != headers:
                    self.sheet.insert_row(headers, 1)
                    print("✓ Headers added to spreadsheet")
            except:
                self.sheet.insert_row(headers, 1)
                print("✓ Headers added to spreadsheet")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup Google Sheets: {e}")
            return False
    
    def navigate_to_search(self):
        """Navigate to the Devex video search page"""
        try:
            print("🔍 Navigating to Devex video search...")
            self.driver.get(self.video_search_url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Handle any popups or alerts
            self._handle_popups()
            
            # Wait for search results to load
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "funding-item"))
            )
            
            print("✓ Successfully navigated to search page")
            return True
            
        except TimeoutException:
            print("⚠️ Timeout waiting for search results. Continuing anyway...")
            return True
        except Exception as e:
            print(f"❌ Failed to navigate to search page: {e}")
            return False
    
    def _handle_popups(self):
        """Handle any popups or alert messages"""
        try:
            # Close session alert if present
            close_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Close']")
            if close_button.is_displayed():
                close_button.click()
                time.sleep(2)
                print("✓ Closed session alert")
        except NoSuchElementException:
            pass
        
        try:
            # Accept cookies if present
            cookie_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'OK')]")
            if cookie_button.is_displayed():
                cookie_button.click()
                time.sleep(2)
                print("✓ Accepted cookies")
        except NoSuchElementException:
            pass
    
    def scrape_opportunities(self, max_pages: int = 5):
        """Scrape video-related opportunities from Devex"""
        try:
            print(f"📋 Starting to scrape opportunities (max {max_pages} pages)...")
            
            page_count = 0
            
            while page_count < max_pages:
                print(f"📄 Scraping page {page_count + 1}...")
                
                # Get opportunities on current page
                opportunities = self._scrape_current_page()
                
                if opportunities:
                    self.scraped_opportunities.extend(opportunities)
                    print(f"✓ Found {len(opportunities)} opportunities on page {page_count + 1}")
                else:
                    print(f"⚠️ No opportunities found on page {page_count + 1}")
                
                # Try to go to next page
                if not self._go_to_next_page():
                    print("📄 No more pages available")
                    break
                
                page_count += 1
                time.sleep(3)  # Be respectful to the server
            
            print(f"✅ Scraping completed! Found {len(self.scraped_opportunities)} total opportunities")
            return True
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            return False
    
    def _scrape_current_page(self) -> List[Dict]:
        """Scrape opportunities from the current page"""
        opportunities = []
        
        try:
            # Find all opportunity items
            opportunity_elements = self.driver.find_elements(By.CSS_SELECTOR, ".funding-item, .tender-item, .grant-item, [class*='opportunity'], [class*='tender'], [class*='grant']")
            
            if not opportunity_elements:
                # Fallback: look for any clickable items in the results area
                opportunity_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/funding/'], .result-item, .search-result")
            
            print(f"🔍 Found {len(opportunity_elements)} opportunity elements")
            
            for i, element in enumerate(opportunity_elements):
                try:
                    opportunity = self._extract_opportunity_data(element, i)
                    if opportunity:
                        opportunities.append(opportunity)
                except Exception as e:
                    print(f"⚠️ Error extracting opportunity {i}: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Error scraping current page: {e}")
        
        return opportunities
    
    def _extract_opportunity_data(self, element, index: int) -> Optional[Dict]:
        """Extract data from a single opportunity element"""
        try:
            opportunity = {
                'title': '',
                'type': '',
                'status': '',
                'location': '',
                'deadline': '',
                'updated': '',
                'description': '',
                'url': '',
                'reference': '',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract title
            title_selectors = [
                'h3', 'h4', 'h5', '.title', '.name', 
                'a[href*="/funding/"]', '.opportunity-title'
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, selector)
                    opportunity['title'] = title_elem.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            # Extract URL
            try:
                link_elem = element.find_element(By.CSS_SELECTOR, 'a[href*="/funding/"]')
                href = link_elem.get_attribute('href')
                if href:
                    opportunity['url'] = href if href.startswith('http') else self.base_url + href
            except NoSuchElementException:
                pass
            
            # Extract type (Tender/Grant)
            type_indicators = ['tender', 'grant', 'rfp', 'rfi', 'solicitation']
            element_text = element.text.lower()
            
            for indicator in type_indicators:
                if indicator in element_text:
                    opportunity['type'] = indicator.title()
                    break
            
            # Extract status
            status_selectors = ['.status', '.badge', '[class*="status"]']
            for selector in status_selectors:
                try:
                    status_elem = element.find_element(By.CSS_SELECTOR, selector)
                    opportunity['status'] = status_elem.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            # Extract location
            location_selectors = ['.location', '.country', '[class*="location"]']
            for selector in location_selectors:
                try:
                    location_elem = element.find_element(By.CSS_SELECTOR, selector)
                    opportunity['location'] = location_elem.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            # Extract deadline
            deadline_patterns = [
                r'deadline[:\s]*([^\\n]+)',
                r'due[:\s]*([^\\n]+)',
                r'closes?[:\s]*([^\\n]+)',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                r'(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})'
            ]
            
            for pattern in deadline_patterns:
                matches = re.findall(pattern, element_text, re.IGNORECASE)
                if matches:
                    opportunity['deadline'] = matches[0].strip()
                    break
            
            # Extract description (first 200 chars)
            opportunity['description'] = element.text.strip()[:200] + "..." if len(element.text) > 200 else element.text.strip()
            
            # Extract reference number
            ref_patterns = [
                r'([A-Z]{2,5}[-/]\d{4,6})',
                r'(RFP[-/]\d{4,6})',
                r'(Tender[-/]\d{4,6})',
                r'(Grant[-/]\d{4,6})'
            ]
            
            for pattern in ref_patterns:
                matches = re.findall(pattern, element.text)
                if matches:
                    opportunity['reference'] = matches[0]
                    break
            
            # Only return if we have at least a title
            if opportunity['title']:
                print(f"✓ Extracted: {opportunity['title'][:50]}...")
                return opportunity
            
        except Exception as e:
            print(f"⚠️ Error extracting opportunity data: {e}")
        
        return None
    
    def _go_to_next_page(self) -> bool:
        """Navigate to the next page of results"""
        try:
            # Look for next page button
            next_selectors = [
                'a[aria-label="Next"]',
                '.next',
                '.pagination-next',
                'a[href*="page="]',
                'button[aria-label*="next"]'
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled() and next_button.is_displayed():
                        next_button.click()
                        time.sleep(3)
                        return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error navigating to next page: {e}")
            return False
    
    def export_to_google_sheets(self) -> bool:
        """Export scraped opportunities to Google Sheets"""
        try:
            if not self.sheet:
                print("❌ Google Sheets not configured. Cannot export.")
                return False
            
            if not self.scraped_opportunities:
                print("⚠️ No opportunities to export")
                return False
            
            print(f"📤 Exporting {len(self.scraped_opportunities)} opportunities to Google Sheets...")
            
            # Prepare data for batch update
            rows_to_add = []
            
            for opp in self.scraped_opportunities:
                row = [
                    opp.get('title', ''),
                    opp.get('type', ''),
                    opp.get('status', ''),
                    opp.get('location', ''),
                    opp.get('deadline', ''),
                    opp.get('updated', ''),
                    opp.get('description', ''),
                    opp.get('url', ''),
                    opp.get('reference', ''),
                    opp.get('scraped_at', '')
                ]
                rows_to_add.append(row)
            
            # Add all rows at once (more efficient)
            if rows_to_add:
                self.sheet.append_rows(rows_to_add)
                print(f"✅ Successfully exported {len(rows_to_add)} opportunities to Google Sheets")
                
                # Get the spreadsheet URL
                spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{self.sheet.spreadsheet.id}"
                print(f"🔗 Spreadsheet URL: {spreadsheet_url}")
                
                return True
            
        except Exception as e:
            print(f"❌ Error exporting to Google Sheets: {e}")
            return False
    
    def save_to_json(self, filename: str = None) -> str:
        """Save scraped opportunities to JSON file as backup"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"devex_video_opportunities_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'scraped_at': datetime.now().isoformat(),
                    'total_opportunities': len(self.scraped_opportunities),
                    'opportunities': self.scraped_opportunities
                }, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved {len(self.scraped_opportunities)} opportunities to {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error saving to JSON: {e}")
            return ""
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")

def main():
    """Main function to run the scraper"""
    print("🚀 DEVEX VIDEO OPPORTUNITIES SCRAPER")
    print("=" * 50)
    
    # Configuration
    # Load credentials file relative to this script location
    GOOGLE_CREDENTIALS_PATH = str((Path(__file__).resolve().parent / "google-credentials.json"))
    SPREADSHEET_NAME = "Devex Video Opportunities"
    MAX_PAGES = 3
    
    # Initialize scraper
    scraper = DevexVideoScraper(GOOGLE_CREDENTIALS_PATH)
    
    try:
        # Setup driver
        if not scraper.setup_driver():
            print("❌ Failed to setup driver. Exiting.")
            return
        
        # Setup Google Sheets (optional)
        sheets_configured = scraper.setup_google_sheets(SPREADSHEET_NAME)
        
        # Navigate to search page
        if not scraper.navigate_to_search():
            print("❌ Failed to navigate to search page. Exiting.")
            return
        
        # Scrape opportunities
        if scraper.scrape_opportunities(MAX_PAGES):
            print(f"✅ Successfully scraped {len(scraper.scraped_opportunities)} opportunities")
            
            # Export to Google Sheets
            if sheets_configured:
                scraper.export_to_google_sheets()
            
            # Save to JSON as backup
            json_file = scraper.save_to_json()
            
            # Print summary
            print(f"\n📊 SCRAPING SUMMARY:")
            print(f"Total opportunities: {len(scraper.scraped_opportunities)}")
            print(f"Google Sheets: {'✅ Exported' if sheets_configured else '❌ Not configured'}")
            print(f"JSON backup: {json_file}")
            
            # Show sample data
            if scraper.scraped_opportunities:
                print(f"\n📋 SAMPLE OPPORTUNITY:")
                sample = scraper.scraped_opportunities[0]
                for key, value in sample.items():
                    print(f"  {key}: {value}")
        
        else:
            print("❌ Scraping failed")
    
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        # Clean up
        scraper.close()
        print("\n✅ Scraping completed!")

if __name__ == "__main__":
    main()

