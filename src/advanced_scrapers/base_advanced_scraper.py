"""
Base class for advanced scrapers using Playwright MCP integration.
Handles complex websites requiring browser automation.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from loguru import logger

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scrapers.base_scraper import BaseScraper, OpportunityData


class BaseAdvancedScraper(BaseScraper):
    """
    Base class for advanced scrapers using Playwright MCP patterns.
    Provides common functionality for browser automation and data extraction.
    """
    
    def __init__(self, config, website_config):
        super().__init__(config, website_config)
        
        # Playwright MCP configuration
        self.playwright_config = {
            'headless': True,
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'timeout': 30000,
            'wait_for_load_state': 'domcontentloaded'
        }
        
        # Enhanced keyword configuration from user specs
        self.keywords = config.get('keywords', {}).get('primary', [
            "video", "photo", "film", "multimedia", "design", "visual",
            "campaign", "podcasts", "virtual event", "media", "animation", 
            "animated video", "promotion", "communication", "audiovisual"
        ])
        
        # Geographic filters from user specs
        self.geographic_filters = config.get('geographic_filters', {})
        self.excluded_countries = self.geographic_filters.get('excluded_countries', [
            "India", "Pakistan", "China", "Bangladesh", "Sri Lanka", 
            "Myanmar", "Thailand", "Vietnam", "Cambodia", "Laos", 
            "Malaysia", "Indonesia", "Philippines", "Singapore"
        ])
        self.included_countries = self.geographic_filters.get('included_countries', ["Nepal"])
        
        # Search configuration based on manual exploration
        self.search_filters = {
            'types': ['tender', 'grant'],  # Tenders & Grants
            'statuses': ['open', 'forecast'],  # Open, Forecast
            'time_range': 'last_week',  # Last week
            'max_results_per_keyword': 50,
            'enable_document_download': True
        }
        
        # Output configuration
        self.output_fields = [
            'title', 'funder', 'location', 'published_date', 'deadline',
            'reference_number', 'detailed_description', 'requirements',
            'contact_email', 'submission_portal', 'document_links'
        ]
        
    def scrape_with_playwright(self) -> List[OpportunityData]:
        """
        Main scraping method using Playwright MCP patterns.
        """
        opportunities = []
        
        try:
            # Check if running in MCP environment
            if self._is_mcp_available():
                opportunities = self._scrape_with_mcp()
            else:
                logger.warning("MCP not available, attempting fallback scraping")
                opportunities = self._fallback_scraping()
                
        except Exception as e:
            logger.error(f"Error in Playwright scraping for {self.website_config['name']}: {e}")
            self._notify_error(f"Scraping failed for {self.website_config['name']}: {e}")
        
        return opportunities
    
    def _is_mcp_available(self) -> bool:
        """Check if MCP Playwright tools are available."""
        try:
            # Try to import MCP tools (this would be available in MCP environment)
            import playwright
            return True
        except ImportError:
            return False
    
    def _scrape_with_mcp(self) -> List[OpportunityData]:
        """
        Scrape using MCP Playwright tools.
        This method should be overridden by specific scrapers.
        """
        raise NotImplementedError("Subclasses must implement _scrape_with_mcp")
    
    def _navigate_and_search(self, page, keyword: str) -> List[Dict]:
        """
        Common navigation and search pattern for MCP Playwright.
        """
        results = []
        
        try:
            # Navigate to search page
            page.goto(self.website_config['url'], wait_until='domcontentloaded')
            page.wait_for_timeout(2000)
            
            # Enter keyword
            search_selectors = [
                'input[placeholder*="keyword"]',
                'input[placeholder*="search"]',
                'input[type="search"]',
                'input[name*="search"]',
                'textbox'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = page.locator(selector).first
                    if search_input.is_visible():
                        break
                except:
                    continue
            
            if search_input and search_input.is_visible():
                search_input.clear()
                search_input.fill(keyword)
                
                # Apply filters
                self._apply_search_filters(page)
                
                # Execute search
                self._execute_search(page)
                
                # Extract results
                results = self._extract_search_results(page, keyword)
        
        except Exception as e:
            logger.error(f"Error in navigation and search for keyword '{keyword}': {e}")
        
        return results
    
    def _apply_search_filters(self, page):
        """Apply search filters based on configuration."""
        try:
            # Apply Tenders & Grants filter
            for filter_type in self.search_filters['types']:
                try:
                    checkbox = page.locator(f'input[type="checkbox"]:near(text("{filter_type.title()}"))')
                    if checkbox.is_visible() and not checkbox.is_checked():
                        checkbox.check()
                except:
                    continue
            
            # Apply status filters (Open, Forecast)
            for status in self.search_filters['statuses']:
                try:
                    checkbox = page.locator(f'input[type="checkbox"]:near(text("{status.title()}"))')
                    if checkbox.is_visible() and not checkbox.is_checked():
                        checkbox.check()
                except:
                    continue
            
            # Apply time filter (Last week)
            if self.search_filters['time_range'] == 'last_week':
                try:
                    time_filter = page.locator('text("Last week"), text("7 days"), text("1 week")')
                    if time_filter.is_visible():
                        time_filter.click()
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Error applying search filters: {e}")
    
    def _execute_search(self, page):
        """Execute the search."""
        try:
            # Look for search button
            search_buttons = [
                'button:has-text("Search")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Find")'
            ]
            
            for button_selector in search_buttons:
                try:
                    button = page.locator(button_selector).first
                    if button.is_visible():
                        button.click()
                        page.wait_for_timeout(3000)  # Wait for results
                        return
                except:
                    continue
                    
            # If no button found, try pressing Enter on search input
            try:
                page.keyboard.press('Enter')
                page.wait_for_timeout(3000)
            except:
                pass
                
        except Exception as e:
            logger.warning(f"Error executing search: {e}")
    
    def _extract_search_results(self, page, keyword: str) -> List[Dict]:
        """Extract search results from page."""
        results = []
        
        try:
            # Wait for results to load
            page.wait_for_selector('li, article, div[class*="result"], div[class*="opportunity"]', timeout=10000)
            
            # Get result items
            result_selectors = [
                'li:has(heading)',
                'article',
                'div[class*="opportunity"]',
                'div[class*="tender"]',
                'div[class*="grant"]'
            ]
            
            items = []
            for selector in result_selectors:
                try:
                    items = page.locator(selector).all()
                    if items:
                        break
                except:
                    continue
            
            # Process each result item
            for item in items[:self.search_filters['max_results_per_keyword']]:
                try:
                    result = self._parse_result_item(page, item, keyword)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error parsing result item: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error extracting search results: {e}")
        
        return results
    
    def _parse_result_item(self, page, item, keyword: str) -> Optional[Dict]:
        """Parse individual result item."""
        try:
            result = {
                'source_keyword': keyword,
                'extraction_date': datetime.now().isoformat()
            }
            
            # Extract title
            title_selectors = ['heading', 'h1', 'h2', 'h3', 'h4', 'h5']
            for selector in title_selectors:
                try:
                    title_elem = item.locator(selector).first
                    if title_elem.is_visible():
                        result['title'] = title_elem.text_content().strip()
                        break
                except:
                    continue
            
            # Extract organization/funder
            org_selectors = [
                'text("United Nations")', 'text("World Bank")', 'text("UNDP")',
                'text("UNICEF")', 'text("WHO")', 'generic:has-text("UN")'
            ]
            for selector in org_selectors:
                try:
                    org_elem = item.locator(selector).first
                    if org_elem.is_visible():
                        result['funder'] = org_elem.text_content().strip()
                        break
                except:
                    continue
            
            # Extract location
            try:
                location_elem = item.locator('generic:near(text("Location")), generic:has-text("Chad"), generic:has-text("Ethiopia")').first
                if location_elem.is_visible():
                    result['location'] = location_elem.text_content().strip()
            except:
                pass
            
            # Extract deadline
            try:
                deadline_elem = item.locator('generic:has-text("2025"), text("Sep"), text("Aug"), text("deadline")').first
                if deadline_elem.is_visible():
                    result['deadline'] = deadline_elem.text_content().strip()
            except:
                pass
            
            # Extract link for detailed information
            try:
                link_elem = item.locator('a[href]').first
                if link_elem.is_visible():
                    href = link_elem.get_attribute('href')
                    if href:
                        if href.startswith('/'):
                            href = self._get_base_url() + href
                        result['detail_url'] = href
                        
                        # Extract detailed info
                        detailed_info = self._extract_detailed_info(page, href)
                        result.update(detailed_info)
            except:
                pass
            
            return result if result.get('title') else None
            
        except Exception as e:
            logger.error(f"Error parsing result item: {e}")
            return None
    
    def _extract_detailed_info(self, page, detail_url: str) -> Dict:
        """Extract detailed information from opportunity detail page."""
        detailed_info = {}
        
        try:
            # Navigate to detail page
            original_url = page.url
            page.goto(detail_url, wait_until='domcontentloaded')
            page.wait_for_timeout(2000)
            
            # Extract detailed description
            desc_selectors = [
                'paragraph:has-text("Contexte")', 'paragraph:has-text("Project")',
                'div:has-text("Description")', 'div:has-text("Overview")',
                'generic:has-text("Objectif")', 'generic:has-text("Objective")'
            ]
            
            for selector in desc_selectors:
                try:
                    desc_elem = page.locator(selector).first
                    if desc_elem.is_visible():
                        detailed_info['detailed_description'] = desc_elem.text_content().strip()[:1000]
                        break
                except:
                    continue
            
            # Extract contact information
            try:
                contact_elem = page.locator('text("@"), text("email"), generic:has-text(".org")').first
                if contact_elem.is_visible():
                    detailed_info['contact_email'] = self._extract_email(contact_elem.text_content())
            except:
                pass
            
            # Extract reference number
            try:
                ref_elem = page.locator('text("Reference"), text("UNDP-"), text("PRC"), text("ID:")').first
                if ref_elem.is_visible():
                    detailed_info['reference_number'] = ref_elem.text_content().strip()
            except:
                pass
            
            # Extract document links
            doc_links = []
            try:
                doc_elements = page.locator('link:has-text("Terms"), link:has-text("RFP"), link:has-text("Document")').all()
                for doc_elem in doc_elements:
                    href = doc_elem.get_attribute('href')
                    if href:
                        doc_links.append(href)
                detailed_info['document_links'] = doc_links
            except:
                pass
            
            # Extract submission portal
            try:
                portal_elem = page.locator('link:has-text("Portal"), link:has-text("Submit"), link:has-text("Apply")').first
                if portal_elem.is_visible():
                    detailed_info['submission_portal'] = portal_elem.get_attribute('href')
            except:
                pass
            
            # Navigate back
            page.goto(original_url, wait_until='domcontentloaded')
            
        except Exception as e:
            logger.warning(f"Error extracting detailed info from {detail_url}: {e}")
        
        return detailed_info
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group() if match else None
    
    def _get_base_url(self) -> str:
        """Get base URL for the website."""
        url = self.website_config['url']
        if '://' in url:
            parts = url.split('/')
            return f"{parts[0]}//{parts[2]}"
        return url
    
    def _convert_to_opportunity_data(self, result_dict: Dict) -> OpportunityData:
        """Convert result dictionary to OpportunityData object."""
        opportunity = OpportunityData()
        
        # Map fields based on user specifications
        opportunity.title = result_dict.get('title', '')
        opportunity.organization = self.website_config['name']
        opportunity.funding_organization = result_dict.get('funder', '')
        opportunity.location = result_dict.get('location', '')
        opportunity.description = result_dict.get('detailed_description', '')
        opportunity.contact_email = result_dict.get('contact_email', '')
        opportunity.reference_number = result_dict.get('reference_number', '')
        opportunity.source_url = result_dict.get('detail_url', '')
        opportunity.date_found = datetime.now()
        
        # Parse deadline
        if result_dict.get('deadline'):
            opportunity.deadline = self._parse_deadline(result_dict['deadline'])
        
        # Set document information
        if result_dict.get('document_links'):
            opportunity.documents_available = True
            opportunity.document_urls = result_dict['document_links']
        
        # Extract keywords
        all_text = f"{opportunity.title} {opportunity.description}"
        opportunity.keywords_found = self.extract_keywords(all_text)
        
        # Extract budget
        opportunity.budget = self.extract_budget(all_text)
        
        return opportunity
    
    def _parse_deadline(self, deadline_text: str) -> Optional[datetime]:
        """Parse deadline from various text formats."""
        import re
        try:
            # Common patterns
            patterns = [
                r'(\d{1,2})\s+(Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',
                r'(\d{4})-(\d{2})-(\d{2})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, deadline_text, re.IGNORECASE)
                if match:
                    if any(month in deadline_text for month in ['Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                        day, month_name, year = match.groups()
                        month_map = {'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                        month = month_map.get(month_name, 1)
                        return datetime(int(year), month, int(day))
                    else:
                        parts = match.groups()
                        if len(parts) == 3:
                            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        except:
            pass
        return None
    
    def _notify_error(self, error_message: str):
        """Notify about scraping errors."""
        logger.error(f"SCRAPING ERROR: {error_message}")
        
        # You can extend this to send email notifications, Slack alerts, etc.
        error_log = {
            'timestamp': datetime.now().isoformat(),
            'website': self.website_config['name'],
            'error': error_message,
            'scraper_type': 'advanced_playwright'
        }
        
        # Save error to log file
        error_file = Path("logs/scraper_errors.json")
        error_file.parent.mkdir(exist_ok=True)
        
        errors = []
        if error_file.exists():
            try:
                with open(error_file, 'r') as f:
                    errors = json.load(f)
            except:
                errors = []
        
        errors.append(error_log)
        
        # Keep only last 100 errors
        errors = errors[-100:]
        
        with open(error_file, 'w') as f:
            json.dump(errors, f, indent=2)
    
    def _fallback_scraping(self) -> List[OpportunityData]:
        """Fallback to basic scraping if Playwright fails."""
        logger.info("Using fallback scraping method")
        opportunities = []
        
        try:
            soup = self.get_page(self.website_config['url'])
            if soup:
                # Basic extraction
                containers = soup.find_all(['div', 'article'], class_=re.compile(r'(opportunity|tender|grant)', re.IGNORECASE))
                
                for container in containers[:20]:
                    try:
                        opportunity = self._parse_static_container(container)
                        if opportunity:
                            opportunities.append(opportunity)
                    except Exception as e:
                        logger.warning(f"Error in fallback parsing: {e}")
                        continue
        except Exception as e:
            logger.error(f"Fallback scraping failed: {e}")
            self._notify_error(f"Both Playwright and fallback scraping failed: {e}")
        
        return opportunities
    
    def _parse_static_container(self, container) -> Optional[OpportunityData]:
        """Parse opportunity from static HTML container."""
        import re
        
        opportunity = OpportunityData()
        opportunity.organization = self.website_config['name']
        opportunity.source_url = self.website_config['url']
        opportunity.date_found = datetime.now()
        
        # Extract title
        title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
        if title_elem:
            opportunity.title = title_elem.get_text(strip=True)
        
        # Extract description
        desc_elem = container.find(['p', 'div'], class_=re.compile(r'(description|summary)', re.I))
        if desc_elem:
            opportunity.description = desc_elem.get_text(strip=True)[:500]
        
        # Extract link
        link_elem = container.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if href.startswith('/'):
                href = self._get_base_url() + href
            opportunity.source_url = href
        
        # Extract keywords
        all_text = f"{opportunity.title} {opportunity.description}"
        opportunity.keywords_found = self.extract_keywords(all_text)
        
        return opportunity if opportunity.title else None
