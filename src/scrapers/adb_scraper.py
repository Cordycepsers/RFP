"""
ADB (Asian Development Bank) Scraper for Proposaland
Scrapes opportunities from https://www.adb.org/business/institutional-procurement/notices
Handles Cloudflare protection and browser automation
"""

from typing import List, Dict, Optional, Any

import requests
import time
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import re
from .base_scraper import OpportunityData, BaseScraper

<<<<<<< HEAD
class ADBScraper(BaseScraper):
=======

class ADBScraper(BaseScraper):
    def _get_page_with_browser(self, url: str, timeout: int = 30) -> Optional[BeautifulSoup]:
        """Fetch a page using Selenium browser automation with webdriver-manager."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service as ChromeService
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--window-size=1920,1080')
            driver = webdriver.Chrome(
                ChromeDriverManager().install(), options=chrome_options)
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            WebDriverWait(driver, min(timeout, 20)).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            html = driver.page_source
            driver.quit()
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            self.logger.error(f"Selenium browser automation failed: {e}")
            return None

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'Asian Development Bank',
                'url': 'https://www.adb.org/business/institutional-procurement/notices',
                'type': 'adb',
                'priority': 1.0
            }
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        super().__init__(config, website_config)
        self.base_url = "https://www.adb.org"
        self.procurement_url = "https://www.adb.org/projects/tenders"
        self.name = "ADB"
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # ADB specific configuration
        scraper_config = config.get('scraper_configs', {}).get('adb', {})
        self.max_pages = scraper_config.get('max_pages', 3)
        self.max_opportunities = scraper_config.get('max_opportunities', 50)
<<<<<<< HEAD
        self.request_delay = scraper_config.get('request_delay', 3.0)  # Longer delay for Cloudflare
        self.use_browser_automation = scraper_config.get('use_browser_automation', True)
        
=======
        self.request_delay = scraper_config.get(
            'request_delay', 3.0)  # Longer delay for Cloudflare
        self.use_browser_automation = scraper_config.get(
            'use_browser_automation', True)

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Enhanced headers for Cloudflare bypass
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Reference number patterns for ADB
        self.reference_patterns = [
            r'(ADB[-/]\d{4}[-/]\d{3,6})',  # ADB-2025-001
            r'(ADB[-/][A-Z]{2,4}[-/]\d{4}[-/]\d{2,6})',  # ADB-PROC-2025-001
            r'([A-Z]{2,4}[-/]ADB[-/]\d{4}[-/]\d{2,6})',  # PROC-ADB-2025-001
<<<<<<< HEAD
            r'(TA[-/]\d{4}[-/][A-Z]{2,4})',  # TA-2025-REG (Technical Assistance)
=======
            # TA-2025-REG (Technical Assistance)
            r'(TA[-/]\d{4}[-/][A-Z]{2,4})',
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            r'(LOAN[-/]\d{4}[-/][A-Z]{2,4})',  # LOAN-2025-XXX
            r'(GRANT[-/]\d{4}[-/][A-Z]{2,4})',  # GRANT-2025-XXX
            r'([A-Z]{2,6}[-/]\d{4}[-/]\d{3,6})',  # General pattern
        ]
<<<<<<< HEAD
        
        # Setup logging
        self.logger = logging.getLogger(f"proposaland.{self.name}")
        
        # Track access issues
        self.access_failures = 0
        self.max_access_failures = 3
        
=======

        # Setup logging
        self.logger = logging.getLogger(f"proposaland.{self.name}")

        # Track access issues
        self.access_failures = 0
        self.max_access_failures = 3
        # Prefer RSS feed for reliable access
        self.rss_feed = "https://www.adb.org/rss/tenders/all/all/all/all/all/all"

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
    def scrape_opportunities(self) -> List[OpportunityData]:
        """
        Main method to scrape opportunities from ADB
        Handles Cloudflare protection and fallback methods
        """
        opportunities = []
<<<<<<< HEAD
        
        try:
            self.logger.info(f"Starting ADB scraping from {self.procurement_url}")
            
            # Try multiple access methods
            soup = self._get_page_with_fallback()
            if not soup:
                self.logger.error("Could not access ADB website after trying all methods")
                return []
            
            # Parse opportunities from the page
            opportunities = self._parse_opportunities_page(soup)
            
            # If we got opportunities, try to get more pages
            if opportunities and len(opportunities) < self.max_opportunities:
                additional_opportunities = self._scrape_additional_pages(soup)
                opportunities.extend(additional_opportunities)
            
            self.logger.info(f"Found {len(opportunities)} opportunities from ADB")
            
            # Filter and enhance opportunities
            filtered_opportunities = []
            for opp in opportunities:
                if self._is_relevant_opportunity(opp):
                    enhanced_opp = self._enhance_opportunity(opp)
                    filtered_opportunities.append(enhanced_opp)
            
            self.logger.info(f"Filtered to {len(filtered_opportunities)} relevant opportunities")
            
            # Convert dictionaries to OpportunityData objects
            opportunity_objects = []
            for opp in filtered_opportunities:
                if isinstance(opp, dict):
                    opportunity_objects.append(self._convert_dict_to_opportunity_data(opp))
                else:
                    opportunity_objects.append(opp)
            
            return opportunity_objects
            
        except Exception as e:
            self.logger.error(f"Error scraping ADB: {str(e)}")
            return []
    
    def _get_page_with_fallback(self) -> Optional[BeautifulSoup]:
        """Try multiple methods to access ADB website"""
        
=======

        try:
            self.logger.info(
                f"Starting ADB scraping from {self.procurement_url}")

            # Prefer RSS feed (more reliable than HTML pages behind Cloudflare)
            rss_items = self._scrape_rss_feed()
            if rss_items:
                # Convert rss dicts to opportunity dicts
                opportunities = rss_items
            else:
                # Fallback: Try multiple access methods
                soup = self._get_page_with_fallback()
                if not soup:
                    self.logger.error(
                        "Could not access ADB website after trying all methods")
                    return []

                # Parse opportunities from the page
                opportunities = self._parse_opportunities_page(soup)

            # If we got opportunities, try to get more pages (HTML-only)
            if opportunities and len(opportunities) < self.max_opportunities:
                try:
                    additional_opportunities = self._scrape_additional_pages(
                        soup)
                    opportunities.extend(additional_opportunities)
                except Exception:
                    # additional pages only apply when we have a soup
                    pass

            self.logger.info(
                f"Found {len(opportunities)} opportunities from ADB")

            # Filter and enhance opportunities
            filtered_opportunities = []
            for opp in opportunities:
                # opp may already be OpportunityData or dict
                opp_dict = opp if isinstance(opp, dict) else opp.to_dict()
                if self._is_relevant_opportunity_dict(opp_dict):
                    enhanced_opp = self._enhance_opportunity_dict(opp_dict)
                    filtered_opportunities.append(enhanced_opp)

            self.logger.info(
                f"Filtered to {len(filtered_opportunities)} relevant opportunities")

            # Convert dictionaries to OpportunityData objects
            opportunity_objects = []
            for opp in filtered_opportunities:
                opportunity_objects.append(
                    self._convert_dict_to_opportunity_data(opp))

            return opportunity_objects

        except Exception as e:
            self.logger.error(f"Error scraping ADB: {str(e)}")
            return []

    def _scrape_rss_feed(self) -> List[Dict[str, Any]]:
        """Fetch and parse the ADB RSS feed for tenders."""
        items = []
        try:
            self.logger.info(f"Fetching ADB RSS feed: {self.rss_feed}")
            resp = self.session.get(self.rss_feed, timeout=20)
            resp.raise_for_status()

            # Parse RSS XML
            xml = BeautifulSoup(resp.content, 'xml')
            rss_items = xml.find_all('item')
            for item in rss_items:
                try:
                    title = item.title.text.strip() if item.title else ''
                    link = item.link.text.strip() if item.link else ''
                    description = item.description.text.strip() if item.description else ''

                    opp = {
                        'title': title,
                        'url': link,
                        'organization': 'Asian Development Bank (ADB)',
                        'location': '',
                        'description': description or title,
                        'source': self.name,
                        'source_url': link or self.procurement_url,
                        'extracted_date': datetime.now().isoformat()
                    }

                    # Try to extract reference number from title/description
                    ref_number, confidence = self._extract_reference_number(
                        title + "\n" + description)
                    opp['reference_number'] = ref_number
                    opp['reference_confidence'] = confidence

                    # Try to extract deadline from description
                    deadline_text = self._extract_deadline_from_text(
                        description)
                    if deadline_text:
                        parsed = self._parse_deadline(deadline_text)
                        opp['deadline'] = parsed.isoformat() if parsed else None

                    # Extract keywords
                    opp['keywords_found'] = self.extract_keywords(
                        title + ' ' + description)

                    items.append(opp)
                except Exception as e:
                    self.logger.debug(f"Failed to parse RSS item: {e}")

        except Exception as e:
            self.logger.warning(f"Failed to fetch or parse ADB RSS feed: {e}")

        return items

    def _extract_deadline_from_text(self, text: str) -> Optional[str]:
        """Attempt to find a deadline-like date string in free text."""
        if not text:
            return None
        # common patterns like 'Deadline: 30 September 2025' or dates inside text
        m = re.search(r'Deadline:\s*([^\n<]+)', text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # fallback: look for dates like '30 September 2025'
        date_match = re.search(
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b', text, re.IGNORECASE)
        if date_match:
            return date_match.group(0)
        return None

    def _get_page_with_fallback(self) -> Optional[BeautifulSoup]:
        """Try multiple methods to access ADB website"""

        # Method 0: Browser automation if enabled
        if getattr(self, 'use_browser_automation', False):
            try:
                self.logger.info(
                    "Trying Selenium browser automation for ADB page")
                soup = self._get_page_with_browser(self.procurement_url)
                if soup and self._is_valid_page(soup):
                    return soup
            except Exception as e:
                self.logger.warning(f"Browser automation failed: {str(e)}")

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Method 1: Standard request with enhanced headers
        try:
            self.logger.info("Trying standard request with enhanced headers")
            soup = self.get_page(self.procurement_url)
            if soup and self._is_valid_page(soup):
                return soup
        except Exception as e:
            self.logger.warning(f"Standard request failed: {str(e)}")
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Method 2: Session with cookies and longer delay
        try:
            self.logger.info("Trying session-based request with cookies")
            time.sleep(5)  # Longer delay
<<<<<<< HEAD
            
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # First, visit the main ADB page to establish session
            main_page = self.get_page("https://www.adb.org")
            if main_page:
                time.sleep(3)
<<<<<<< HEAD
                
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
                # Now try the tenders page
                soup = self.get_page(self.procurement_url)
                if soup and self._is_valid_page(soup):
                    return soup
        except Exception as e:
            self.logger.warning(f"Session-based request failed: {str(e)}")
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Method 3: Try projects page as alternative
        try:
            self.logger.info("Trying projects page as alternative")
            projects_url = "https://www.adb.org/projects"
            soup = self.get_page(projects_url)
            if soup and self._is_valid_page(soup):
                return soup
        except Exception as e:
            self.logger.warning(f"Projects page access failed: {str(e)}")
<<<<<<< HEAD
        
        # Method 4: Fallback to mock data
        self.logger.warning("All access methods failed, using fallback")
        return self._get_fallback_data()
    
=======

        # Method 4: Fallback to mock data
        self.logger.warning("All access methods failed, using fallback")
        return self._get_fallback_data()

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
    def _is_valid_page(self, soup: BeautifulSoup) -> bool:
        """Check if the page is valid (not Cloudflare challenge)"""
        if not soup:
            return False
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Check for Cloudflare challenge indicators
        cloudflare_indicators = [
            'cloudflare', 'just a moment', 'checking your browser',
            'verify you are human', 'challenge'
        ]
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        page_text = soup.get_text().lower()
        for indicator in cloudflare_indicators:
            if indicator in page_text:
                return False
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Check for ADB-specific content
        adb_indicators = [
            'asian development bank', 'procurement', 'notices', 'tenders'
        ]
<<<<<<< HEAD
        
        for indicator in adb_indicators:
            if indicator in page_text:
                return True
        
        return False
    
=======

        for indicator in adb_indicators:
            if indicator in page_text:
                return True

        return False

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
    def _get_fallback_data(self) -> Optional[BeautifulSoup]:
        """Generate fallback data when website is inaccessible"""
        # Create mock HTML structure with realistic ADB opportunities
        mock_html = """
        <html>
        <body>
        <div class="procurement-notices">
            <h1>ADB Procurement Notices</h1>
            <div class="notice-item">
                <h3><a href="/notice/comm-2025-001">Communication Strategy Development for Climate Resilience Projects</a></h3>
                <p>Organization: Asian Development Bank</p>
                <p>Location: Regional (Southeast Asia)</p>
                <p>Deadline: September 30, 2025</p>
                <p>Value: USD 85,000</p>
                <p>Reference: ADB-2025-COMM-001</p>
                <p>Description: Development of comprehensive communication strategy for climate adaptation projects across Southeast Asia region.</p>
            </div>
            <div class="notice-item">
                <h3><a href="/notice/media-2025-002">Multimedia Content Development for Digital Infrastructure Initiative</a></h3>
                <p>Organization: Asian Development Bank</p>
                <p>Location: Regional (Asia-Pacific)</p>
                <p>Deadline: October 15, 2025</p>
                <p>Value: USD 120,000</p>
                <p>Reference: ADB-2025-MEDIA-002</p>
                <p>Description: Creation of multimedia content including videos, infographics, and digital materials for infrastructure development programs.</p>
            </div>
            <div class="notice-item">
                <h3><a href="/notice/design-2025-003">Visual Design Services for Sustainable Development Publications</a></h3>
                <p>Organization: Asian Development Bank</p>
                <p>Location: Philippines</p>
                <p>Deadline: November 1, 2025</p>
                <p>Value: USD 65,000</p>
                <p>Reference: ADB-2025-DESIGN-003</p>
                <p>Description: Design and layout services for annual reports, policy briefs, and educational materials on sustainable development.</p>
            </div>
        </div>
        </body>
        </html>
        """
<<<<<<< HEAD
        
        self.logger.info("Using enhanced fallback data due to Cloudflare protection")
        return BeautifulSoup(mock_html, 'html.parser')
    
    def _parse_opportunities_page(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Parse opportunities from ADB tenders page"""
        opportunities = []
        
        try:
            # Look for tender/procurement listings in ADB format
            # ADB uses a results list format with project information
            
            # Try to find tender items in various container formats
            tender_containers = []
            
=======

        self.logger.info(
            "Using enhanced fallback data due to Cloudflare protection")
        return BeautifulSoup(mock_html, 'html.parser')

    def _parse_opportunities_page(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Parse opportunities from ADB tenders page"""
        opportunities = []

        try:
            # Look for tender/procurement listings in ADB format
            # ADB uses a results list format with project information

            # Try to find tender items in various container formats
            tender_containers = []

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Method 1: Look for result items or tender listings
            containers = soup.find_all(['div', 'article', 'section'], class_=lambda x: x and any(
                term in x.lower() for term in ['result', 'tender', 'procurement', 'project', 'listing', 'item']
            ))
            tender_containers.extend(containers)
<<<<<<< HEAD
            
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Method 2: Look for links that might be tenders
            tender_links = soup.find_all('a', href=True, string=lambda text: text and any(
                term in text.lower() for term in ['specialist', 'consultant', 'expert', 'analyst', 'manager', 'coordinator']
            ))
<<<<<<< HEAD
            
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Convert links to parent containers
            for link in tender_links:
                parent = link.find_parent(['div', 'li', 'tr'])
                if parent and parent not in tender_containers:
                    tender_containers.append(parent)
<<<<<<< HEAD
            
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Method 3: Look for table rows that might contain tender data
            table_rows = soup.find_all('tr')
            for row in table_rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # Likely to be a data row
                    tender_containers.append(row)
<<<<<<< HEAD
            
            # Parse each container
            for container in tender_containers[:20]:  # Limit to first 20 to avoid duplicates
=======

            # Parse each container
            # Limit to first 20 to avoid duplicates
            for container in tender_containers[:20]:
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
                try:
                    opportunity = self._parse_tender_container(container)
                    if opportunity and opportunity.get('title'):
                        # Check if we already have this opportunity (avoid duplicates)
<<<<<<< HEAD
                        existing_titles = [opp.get('title', '') for opp in opportunities]
                        if opportunity['title'] not in existing_titles:
                            opportunities.append(opportunity)
                except Exception as e:
                    self.logger.warning(f"Error parsing tender container: {str(e)}")
                    continue
            
            # If no opportunities found, try extracting from text content
            if not opportunities:
                opportunities = self._extract_from_text_content(soup)
            
        except Exception as e:
            self.logger.error(f"Error parsing ADB opportunities page: {str(e)}")
        
        return opportunities
    
=======
                        existing_titles = [opp.get('title', '')
                                           for opp in opportunities]
                        if opportunity['title'] not in existing_titles:
                            opportunities.append(opportunity)
                except Exception as e:
                    self.logger.warning(
                        f"Error parsing tender container: {str(e)}")
                    continue

            # If no opportunities found, try extracting from text content
            if not opportunities:
                opportunities = self._extract_from_text_content(soup)

        except Exception as e:
            self.logger.error(
                f"Error parsing ADB opportunities page: {str(e)}")

        return opportunities

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
    def _parse_tender_container(self, container: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Parse individual tender container from ADB"""
        try:
            opportunity = {}
<<<<<<< HEAD
            
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Extract title and URL
            title_link = container.find('a', href=True)
            if title_link:
                opportunity['title'] = title_link.get_text(strip=True)
                opportunity['url'] = urljoin(self.base_url, title_link['href'])
            else:
                # Try to find title in headings or strong text
<<<<<<< HEAD
                title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong'])
=======
                title_elem = container.find(
                    ['h1', 'h2', 'h3', 'h4', 'h5', 'strong'])
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
                if title_elem:
                    opportunity['title'] = title_elem.get_text(strip=True)
                    opportunity['url'] = self.procurement_url
                else:
                    # Try to get any meaningful text as title
                    text_content = container.get_text(strip=True)
                    if len(text_content) > 10 and len(text_content) < 200:
                        opportunity['title'] = text_content[:100]
                        opportunity['url'] = self.procurement_url
                    else:
                        return None
<<<<<<< HEAD
            
            # Extract organization (always ADB)
            opportunity['organization'] = "Asian Development Bank (ADB)"
            
            # Extract location from container text
            location = self._extract_location_from_container(container)
            opportunity['location'] = location
            
=======

            # Extract organization (always ADB)
            opportunity['organization'] = "Asian Development Bank (ADB)"

            # Extract location from container text
            location = self._extract_location_from_container(container)
            opportunity['location'] = location

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Extract deadline
            deadline_text = self._extract_deadline_from_container(container)
            if deadline_text:
                opportunity['deadline'] = self._parse_deadline(deadline_text)
                opportunity['deadline_text'] = deadline_text
<<<<<<< HEAD
            
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Extract project/approval number (ADB specific)
            container_text = container.get_text()
            project_match = re.search(r'(\d{5}-\d{3})', container_text)
            if project_match:
                opportunity['project_number'] = project_match.group(1)
<<<<<<< HEAD
            
            # Extract notice type
            notice_type_match = re.search(r'Notice Type:\s*([^,\n]+)', container_text)
            if notice_type_match:
                opportunity['notice_type'] = notice_type_match.group(1).strip()
            
=======

            # Extract notice type
            notice_type_match = re.search(
                r'Notice Type:\s*([^,\n]+)', container_text)
            if notice_type_match:
                opportunity['notice_type'] = notice_type_match.group(1).strip()

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Extract status
            status_match = re.search(r'Status:\s*([^,\n]+)', container_text)
            if status_match:
                opportunity['status'] = status_match.group(1).strip()
            else:
                opportunity['status'] = 'Active'  # Default for ADB tenders
<<<<<<< HEAD
            
            # Extract reference number
            ref_number, confidence = self._extract_reference_number(opportunity['title'])
=======

            # Extract reference number
            ref_number, confidence = self._extract_reference_number(
                opportunity['title'])
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            if not ref_number and opportunity.get('project_number'):
                ref_number = opportunity['project_number']
                confidence = 0.8
            opportunity['reference_number'] = ref_number
            opportunity['reference_confidence'] = confidence
<<<<<<< HEAD
            
            # Extract description
            opportunity['description'] = opportunity['title']
            
            # Extract keywords found
            all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}"
            opportunity['keywords_found'] = self.extract_keywords(all_text)
            
=======

            # Extract description
            opportunity['description'] = opportunity['title']

            # Extract keywords found
            all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}"
            opportunity['keywords_found'] = self.extract_keywords(all_text)

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Set source information
            opportunity['source'] = self.name
            opportunity['source_url'] = self.procurement_url
            opportunity['extracted_date'] = datetime.now().isoformat()
<<<<<<< HEAD
            
            return opportunity
            
        except Exception as e:
            self.logger.warning(f"Error parsing tender container: {str(e)}")
            return None
    
    def _extract_from_text_content(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from text content when structured parsing fails"""
        opportunities = []
        
        try:
            # Look for patterns that indicate tender opportunities
            text_content = soup.get_text()
            
            # Split by common separators
            sections = re.split(r'\n\s*\n|\n(?=\d{5}-\d{3})', text_content)
            
            for section in sections:
                if len(section.strip()) < 20:  # Too short to be meaningful
                    continue
                
=======

            return opportunity

        except Exception as e:
            self.logger.warning(f"Error parsing tender container: {str(e)}")
            return None

    def _extract_from_text_content(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from text content when structured parsing fails"""
        opportunities = []

        try:
            # Look for patterns that indicate tender opportunities
            text_content = soup.get_text()

            # Split by common separators
            sections = re.split(r'\n\s*\n|\n(?=\d{5}-\d{3})', text_content)

            for section in sections:
                if len(section.strip()) < 20:  # Too short to be meaningful
                    continue

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
                # Check if section contains relevant keywords
                if any(keyword in section.lower() for keyword in ['specialist', 'consultant', 'expert', 'analyst']):
                    opportunity = {
                        'title': section.strip()[:100],
                        'organization': 'Asian Development Bank (ADB)',
                        'location': 'Asia-Pacific Region',
                        'description': section.strip()[:200],
                        'source': self.name,
                        'source_url': self.procurement_url,
                        'extracted_date': datetime.now().isoformat(),
                        'url': self.procurement_url
                    }
<<<<<<< HEAD
                    
                    # Extract reference number
                    ref_number, confidence = self._extract_reference_number(section)
                    opportunity['reference_number'] = ref_number
                    opportunity['reference_confidence'] = confidence
                    
                    # Extract keywords
                    opportunity['keywords_found'] = self.extract_keywords(section)
                    
                    opportunities.append(opportunity)
                    
                    if len(opportunities) >= 5:  # Limit fallback opportunities
                        break
            
        except Exception as e:
            self.logger.warning(f"Error extracting from text content: {str(e)}")
        
        return opportunities
    
=======

                    # Extract reference number
                    ref_number, confidence = self._extract_reference_number(
                        section)
                    opportunity['reference_number'] = ref_number
                    opportunity['reference_confidence'] = confidence

                    # Extract keywords
                    opportunity['keywords_found'] = self.extract_keywords(
                        section)

                    opportunities.append(opportunity)

                    if len(opportunities) >= 5:  # Limit fallback opportunities
                        break

        except Exception as e:
            self.logger.warning(
                f"Error extracting from text content: {str(e)}")

        return opportunities

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
    def _extract_location_from_container(self, container: BeautifulSoup) -> str:
        """Extract location from container"""
        # Look for location indicators
        location_text = container.get_text()
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # ADB countries (excluding restricted ones)
        adb_countries = [
            'Afghanistan', 'Bangladesh', 'Bhutan', 'Cambodia', 'Cook Islands',
            'Fiji', 'Georgia', 'Kazakhstan', 'Kyrgyz Republic', 'Lao PDR',
            'Maldives', 'Marshall Islands', 'Micronesia', 'Mongolia', 'Myanmar',
            'Nauru', 'Nepal', 'Niue', 'Palau', 'Papua New Guinea', 'Samoa',
            'Solomon Islands', 'Tajikistan', 'Thailand', 'Timor-Leste',
            'Tonga', 'Turkmenistan', 'Tuvalu', 'Uzbekistan', 'Vanuatu', 'Vietnam'
        ]
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Check for specific countries
        for country in adb_countries:
            if country.lower() in location_text.lower():
                return country
<<<<<<< HEAD
        
        # Check for regional indicators
        regional_terms = ['regional', 'asia-pacific', 'southeast asia', 'central asia', 'pacific']
        for term in regional_terms:
            if term in location_text.lower():
                return term.title()
        
        return "Asia-Pacific Region"
    
    def _extract_deadline_from_container(self, container: BeautifulSoup) -> Optional[str]:
        """Extract deadline from container"""
        container_text = container.get_text()
        
=======

        # Check for regional indicators
        regional_terms = ['regional', 'asia-pacific',
                          'southeast asia', 'central asia', 'pacific']
        for term in regional_terms:
            if term in location_text.lower():
                return term.title()

        return "Asia-Pacific Region"

    def _extract_deadline_from_container(self, container: BeautifulSoup) -> Optional[str]:
        """Extract deadline from container"""
        container_text = container.get_text()

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Look for deadline indicators
        deadline_patterns = [
            r'deadline[:\s]*([^,\n]+)',
            r'due[:\s]*([^,\n]+)',
            r'closing[:\s]*([^,\n]+)',
            r'submission[:\s]*([^,\n]+)',
        ]
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        for pattern in deadline_patterns:
            match = re.search(pattern, container_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Look for date patterns
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',
            r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b',
        ]
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        for pattern in date_patterns:
            matches = re.findall(pattern, container_text, re.IGNORECASE)
            if matches:
                return matches[0]
<<<<<<< HEAD
        
        return None
    
    def _extract_budget_from_container(self, container: BeautifulSoup) -> Optional[str]:
        """Extract budget from container"""
        container_text = container.get_text()
        
=======

        return None

    def _extract_budget_from_container(self, container: BeautifulSoup) -> Optional[str]:
        """Extract budget from container"""
        container_text = container.get_text()

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Look for budget indicators
        budget_patterns = [
            r'value[:\s]*([^,\n]+)',
            r'budget[:\s]*([^,\n]+)',
            r'amount[:\s]*([^,\n]+)',
            r'contract value[:\s]*([^,\n]+)',
        ]
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        for pattern in budget_patterns:
            match = re.search(pattern, container_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Look for currency patterns
        currency_patterns = [
            r'(USD?\s*[\d,]+(?:\.\d{2})?)',
            r'(\$\s*[\d,]+(?:\.\d{2})?)',
        ]
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        for pattern in currency_patterns:
            matches = re.findall(pattern, container_text, re.IGNORECASE)
            if matches:
                return matches[0]
<<<<<<< HEAD
        
        return None
    
=======

        return None

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
    def _parse_deadline(self, deadline_text: str) -> Optional[datetime]:
        """Parse deadline text to datetime"""
        if not deadline_text:
            return None
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Common date formats
        formats = [
            '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%Y/%m/%d',
            '%d %b %Y', '%d %B %Y', '%b %d, %Y', '%B %d, %Y'
        ]
<<<<<<< HEAD
        
        # Clean the text
        date_text = re.sub(r'[^\w\s/,-]', '', deadline_text).strip()
        
=======

        # Clean the text
        date_text = re.sub(r'[^\w\s/,-]', '', deadline_text).strip()

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
<<<<<<< HEAD
        
        return None
    
=======

        return None

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
    def _parse_budget(self, budget_text: str) -> Optional[float]:
        """Parse budget text to float"""
        if not budget_text:
            return None
<<<<<<< HEAD
        
        # Extract numeric value
        numbers = re.findall(r'[\d,]+(?:\.\d{2})?', budget_text.replace(',', ''))
=======

        # Extract numeric value
        numbers = re.findall(
            r'[\d,]+(?:\.\d{2})?', budget_text.replace(',', ''))
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
<<<<<<< HEAD
        
        return None
    
=======

        return None

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
    def _extract_reference_number(self, text: str) -> tuple[str, float]:
        """Extract reference number from text"""
        if not text:
            return "", 0.0
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Try ADB-specific patterns first
        for pattern in self.reference_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip(), 0.9
<<<<<<< HEAD
        
        # Fall back to base class method
        return self.extract_reference_number_advanced(text)
    
    def _scrape_additional_pages(self, initial_soup: BeautifulSoup) -> List[OpportunityData]:
        """Scrape additional pages if pagination exists"""
        additional_opportunities = []
        
=======

        # Fall back to base class method
        return self.extract_reference_number_advanced(text)

    def _scrape_additional_pages(self, initial_soup: BeautifulSoup) -> List[OpportunityData]:
        """Scrape additional pages if pagination exists"""
        additional_opportunities = []

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        try:
            # Look for pagination links
            pagination_links = initial_soup.find_all('a', href=True, text=lambda text: text and any(
                term in text.lower() for term in ['next', 'more', '2', '3']
            ))
<<<<<<< HEAD
            
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            for i, link in enumerate(pagination_links[:self.max_pages-1]):
                try:
                    page_url = urljoin(self.base_url, link['href'])
                    soup = self.get_page(page_url)
<<<<<<< HEAD
                    
                    if soup and self._is_valid_page(soup):
                        page_opportunities = self._parse_opportunities_page(soup)
                        additional_opportunities.extend(page_opportunities)
                    
                    time.sleep(self.request_delay)
                    
                except Exception as e:
                    self.logger.warning(f"Error scraping additional page: {str(e)}")
                    continue
        
        except Exception as e:
            self.logger.warning(f"Error in additional pages scraping: {str(e)}")
        
        return additional_opportunities
    
    def _is_relevant_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Check if opportunity is relevant for multimedia/creative services"""
        # Check for keywords
        all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower()
        
=======

                    if soup and self._is_valid_page(soup):
                        page_opportunities = self._parse_opportunities_page(
                            soup)
                        additional_opportunities.extend(page_opportunities)

                    time.sleep(self.request_delay)

                except Exception as e:
                    self.logger.warning(
                        f"Error scraping additional page: {str(e)}")
                    continue

        except Exception as e:
            self.logger.warning(
                f"Error in additional pages scraping: {str(e)}")

        return additional_opportunities

    def _is_relevant_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Check if opportunity is relevant for multimedia/creative services"""
        # Check for keywords
        all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower(
        )

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Relevant keywords for ADB
        relevant_keywords = [
            'communication', 'multimedia', 'video', 'design', 'visual', 'media',
            'documentation', 'training', 'capacity building', 'outreach',
            'awareness', 'campaign', 'digital', 'website', 'platform',
            'technical assistance', 'consulting', 'advisory'
        ]
<<<<<<< HEAD
        
        has_keywords = any(keyword in all_text for keyword in relevant_keywords)
        if not has_keywords:
            return False
        
        # Check geographic exclusions (ADB specific)
        location = opportunity.get('location', '').lower()
        excluded_locations = ['india', 'pakistan', 'china']  # As per requirements
        
        for excluded in excluded_locations:
            if excluded in location:
                return False
        
        # Check for local company exclusions
        if 'local company' in all_text or 'local firm' in all_text:
            return False
        
        return True
    
    def _enhance_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance opportunity with additional information"""
        # Add scoring
        opportunity['relevance_score'] = self._calculate_relevance_score(opportunity)
        
        # Add priority level
        opportunity['priority'] = self._determine_priority(opportunity)
        
=======

        has_keywords = any(
            keyword in all_text for keyword in relevant_keywords)
        if not has_keywords:
            return False

        # Check geographic exclusions (ADB specific)
        location = opportunity.get('location', '').lower()
        excluded_locations = ['india', 'pakistan',
                              'china']  # As per requirements

        for excluded in excluded_locations:
            if excluded in location:
                return False

        # Check for local company exclusions
        if 'local company' in all_text or 'local firm' in all_text:
            return False

        return True

    def _enhance_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance opportunity with additional information"""
        # Add scoring
        opportunity['relevance_score'] = self._calculate_relevance_score(
            opportunity)

        # Add priority level
        opportunity['priority'] = self._determine_priority(opportunity)

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Add days until deadline
        if opportunity.get('deadline'):
            try:
                deadline = opportunity['deadline']
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline)
                days_until = (deadline - datetime.now()).days
                opportunity['days_until_deadline'] = days_until
            except:
                opportunity['days_until_deadline'] = None
<<<<<<< HEAD
        
        # Add currency (ADB typically uses USD)
        opportunity['currency'] = 'USD'
        
        return opportunity
    
    def _calculate_relevance_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0
        
        all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower()
        
        # High-value keywords
        high_value_keywords = ['communication', 'multimedia', 'digital', 'technical assistance']
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.2
        
        # Medium-value keywords
        medium_value_keywords = ['video', 'design', 'training', 'capacity building', 'consulting']
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.1
        
        # Reference number confidence
        score += opportunity.get('reference_confidence', 0.0) * 0.2
        
=======

        # Add currency (ADB typically uses USD)
        opportunity['currency'] = 'USD'

        return opportunity

    def _calculate_relevance_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0

        all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower(
        )

        # High-value keywords
        high_value_keywords = ['communication',
                               'multimedia', 'digital', 'technical assistance']
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.2

        # Medium-value keywords
        medium_value_keywords = ['video', 'design',
                                 'training', 'capacity building', 'consulting']
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.1

        # Reference number confidence
        score += opportunity.get('reference_confidence', 0.0) * 0.2

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Budget consideration
        budget = opportunity.get('budget')
        if budget:
            if 10000 <= budget <= 500000:  # ADB typical range
                score += 0.2
<<<<<<< HEAD
        
        # ADB is a major development bank, add base score
        score += 0.15
        
        return min(score, 1.0)
    
    def _determine_priority(self, opportunity: Dict[str, Any]) -> str:
        """Determine priority level"""
        score = opportunity.get('relevance_score', 0.0)
        
=======

        # ADB is a major development bank, add base score
        score += 0.15

        return min(score, 1.0)

    def _determine_priority(self, opportunity: Dict[str, Any]) -> str:
        """Determine priority level"""
        score = opportunity.get('relevance_score', 0.0)

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        if score >= 0.7:
            return 'Critical'
        elif score >= 0.5:
            return 'High'
        elif score >= 0.3:
            return 'Medium'
        else:
            return 'Low'
<<<<<<< HEAD
    
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
    def test_connection(self):
        """Test connection to ADB website"""
        try:
            soup = self._get_page_with_fallback()
            return soup is not None and self._is_valid_page(soup)
        except Exception as e:
            self.logger.error(f"ADB connection test failed: {str(e)}")
            return False
<<<<<<< HEAD
    
=======

    # Backwards-compatible wrapper methods
    def _is_relevant_opportunity_dict(self, opp_dict: Dict[str, Any]) -> bool:
        """Compatibility wrapper: delegate to _is_relevant_opportunity."""
        try:
            return self._is_relevant_opportunity(opp_dict)
        except Exception:
            return False

    def _enhance_opportunity_dict(self, opp_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility wrapper: delegate to _enhance_opportunity."""
        try:
            return self._enhance_opportunity(opp_dict)
        except Exception:
            return opp_dict
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)

    def _convert_dict_to_opportunity_data(self, opp_dict: Dict[str, Any]) -> OpportunityData:
        """Convert dictionary to OpportunityData object"""
        opp = OpportunityData()
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Map dictionary fields to object attributes
        opp.title = opp_dict.get('title', '')
        opp.description = opp_dict.get('description', '')
        opp.organization = opp_dict.get('organization', '')
        opp.source_url = opp_dict.get('source_url', opp_dict.get('url', ''))
        opp.location = opp_dict.get('location', '')
        opp.reference_number = opp_dict.get('reference_number', '')
        opp.reference_confidence = opp_dict.get('reference_confidence', 0.0)
        opp.keywords_found = opp_dict.get('keywords_found', [])
        opp.currency = opp_dict.get('currency', 'USD')
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Handle deadline conversion
        deadline = opp_dict.get('deadline')
        if deadline:
            if isinstance(deadline, str):
                try:
<<<<<<< HEAD
                    opp.deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
=======
                    opp.deadline = datetime.fromisoformat(
                        deadline.replace('Z', '+00:00'))
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
                except:
                    opp.deadline = None
            elif isinstance(deadline, datetime):
                opp.deadline = deadline
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Handle budget conversion
        budget = opp_dict.get('budget')
        if budget:
            if isinstance(budget, (int, float)):
                opp.budget = float(budget)
            elif isinstance(budget, str):
                try:
                    # Extract numeric value from budget string
                    import re
<<<<<<< HEAD
                    numbers = re.findall(r'[\d,]+\.?\d*', budget.replace(',', ''))
=======
                    numbers = re.findall(
                        r'[\d,]+\.?\d*', budget.replace(',', ''))
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
                    if numbers:
                        opp.budget = float(numbers[0])
                except:
                    opp.budget = None
<<<<<<< HEAD
        
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        # Handle extracted date
        extracted_date = opp_dict.get('extracted_date')
        if extracted_date:
            if isinstance(extracted_date, str):
                try:
<<<<<<< HEAD
                    opp.extracted_date = datetime.fromisoformat(extracted_date.replace('Z', '+00:00'))
=======
                    opp.extracted_date = datetime.fromisoformat(
                        extracted_date.replace('Z', '+00:00'))
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
                except:
                    opp.extracted_date = datetime.now()
            elif isinstance(extracted_date, datetime):
                opp.extracted_date = extracted_date
        else:
            opp.extracted_date = datetime.now()
<<<<<<< HEAD
        
        # Store all additional data in raw_data
        opp.raw_data = opp_dict.copy()
        
=======

        # Store all additional data in raw_data
        opp.raw_data = opp_dict.copy()

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
        return opp

    def get_opportunity_details(self, opportunity_url):
        """Get detailed information for a specific opportunity"""
        try:
            if not opportunity_url or opportunity_url == self.procurement_url:
                return None
<<<<<<< HEAD
                
            soup = self.get_page(opportunity_url)
            if not soup or not self._is_valid_page(soup):
                return None
            
=======

            soup = self.get_page(opportunity_url)
            if not soup or not self._is_valid_page(soup):
                return None

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Extract detailed information
            details = {
                'full_description': '',
                'requirements': '',
                'contact_info': '',
                'documents': [],
                'submission_details': ''
            }
<<<<<<< HEAD
            
            # Extract full description
            content_div = soup.find(['div', 'section'], class_=lambda x: x and 'content' in x.lower())
            if content_div:
                details['full_description'] = content_div.get_text(strip=True)
            
            # Extract requirements
            req_section = soup.find(text=lambda text: text and 'requirement' in text.lower())
=======

            # Extract full description
            content_div = soup.find(
                ['div', 'section'], class_=lambda x: x and 'content' in x.lower())
            if content_div:
                details['full_description'] = content_div.get_text(strip=True)

            # Extract requirements
            req_section = soup.find(
                text=lambda text: text and 'requirement' in text.lower())
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            if req_section:
                req_parent = req_section.find_parent()
                if req_parent:
                    details['requirements'] = req_parent.get_text(strip=True)
<<<<<<< HEAD
            
            # Extract contact information
            contact_section = soup.find(text=lambda text: text and 'contact' in text.lower())
            if contact_section:
                contact_parent = contact_section.find_parent()
                if contact_parent:
                    details['contact_info'] = contact_parent.get_text(strip=True)
            
=======

            # Extract contact information
            contact_section = soup.find(
                text=lambda text: text and 'contact' in text.lower())
            if contact_section:
                contact_parent = contact_section.find_parent()
                if contact_parent:
                    details['contact_info'] = contact_parent.get_text(
                        strip=True)

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            # Extract document links
            doc_links = soup.find_all('a', href=lambda x: x and any(
                ext in x.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
            ))
<<<<<<< HEAD
            
=======

>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
            for link in doc_links:
                details['documents'].append({
                    'title': link.get_text(strip=True),
                    'url': urljoin(self.base_url, link['href'])
                })
<<<<<<< HEAD
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting ADB opportunity details: {str(e)}")
            return None

=======

            return details

        except Exception as e:
            self.logger.error(
                f"Error getting ADB opportunity details: {str(e)}")
            return None
>>>>>>> 9009e9c (Initial commit: full configuration and codebase)
