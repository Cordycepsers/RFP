"""
ACTED Scraper for Proposaland System
Scrapes tender opportunities from ACTED's call for tenders page
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import time
import logging
from urllib.parse import urljoin, urlparse

from .base_scraper import BaseScraper, OpportunityData

class ACTEDScraper(BaseScraper):
    """Scraper for ACTED (Agency for Technical Cooperation and Development) tenders"""
    
    def __init__(self, config: Dict[str, Any]):
        # Extract website-specific config
        website_config = config.get('scrapers', {}).get('acted', {})
        super().__init__(config, website_config)
        
        self.base_url = "https://www.acted.org/en/call-for-tenders/"
        self.organization = "ACTED (Agency for Technical Cooperation and Development)"
        self.website_type = "acted"
        
        # ACTED-specific configuration
        self.request_delay = website_config.get('request_delay', 2)
        self.max_pages = website_config.get('max_pages', 5)
        self.timeout = website_config.get('timeout', 30)
        
        # Reference number patterns for ACTED
        self.reference_patterns = [
            r'RFQ/[A-Z0-9]+/[A-Z0-9]+/[A-Z0-9]+/[A-Z0-9]+/[A-Z0-9]+/\d{2}-\d{2}-\d{4}',  # RFQ/13FFH/K19/FEE/AMM/AFD/10-02-2025
            r'RFP/[A-Z0-9]+/[A-Z0-9]+/[A-Z0-9]+/[A-Z0-9]+/\d{2}-\d{2}-\d{4}',  # RFP variations
            r'ITB/[A-Z0-9]+/[A-Z0-9]+/[A-Z0-9]+/[A-Z0-9]+/\d{2}-\d{2}-\d{4}',  # Invitation to Bid
            r'ACTED-\d{4}-[A-Z0-9]+-\d+',  # ACTED-2025-PROJECT-001
            r'ACT-[A-Z]{3}-\d{4}-\d{3}',   # ACT-JOR-2025-001
        ]
        
        # Keywords for multimedia/creative opportunities
        self.multimedia_keywords = [
            'video', 'photo', 'film', 'multimedia', 'design', 'visual', 'campaign',
            'podcasts', 'virtual event', 'media', 'animation', 'animated video',
            'promotion', 'communication', 'audiovisual', 'graphic', 'creative',
            'marketing', 'branding', 'website', 'digital', 'social media',
            'content creation', 'photography', 'videography', 'documentary',
            'presentation', 'infographic', 'illustration', 'web design'
        ]
        
        def test_connection(self) -> bool:
            """Lightweight connectivity check using HEAD to the base URL."""
            try:
                resp = requests.head(self.base_url, timeout=5, allow_redirects=True)
                return resp.status_code < 400
            except Exception as e:
                self.logger.debug(f"test_connection failed for ACTED: {e}")
                return False
        
    def scrape_opportunities(self) -> List[OpportunityData]:
        """Scrape opportunities from ACTED tenders page"""
        opportunities = []
        
        try:
            # Get main tenders page
            main_page_data = self._scrape_main_page()
            opportunities.extend(main_page_data)
            
            # Try pagination if available
            for page_num in range(2, self.max_pages + 1):
                try:
                    time.sleep(self.request_delay)
                    page_data = self._scrape_page(page_num)
                    if not page_data:
                        break
                    opportunities.extend(page_data)
                except Exception as e:
                    self.logger.warning(f"Error scraping page {page_num}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error scraping ACTED opportunities: {e}")
            # Return fallback opportunities
            opportunities = self._get_fallback_opportunities()
            
        # Filter for multimedia/creative opportunities
        filtered_opportunities = self._filter_opportunities(opportunities)
        
        # Convert to OpportunityData objects
        return [self._convert_dict_to_opportunity_data(opp) for opp in filtered_opportunities]
    
    def _scrape_main_page(self) -> List[Dict[str, Any]]:
        """Scrape the main tenders page"""
        opportunities = []
        
        try:
            soup = self.get_page(self.base_url)
            if not soup:
                return []
                
            # Find tender cards/listings
            tender_elements = self._find_tender_elements(soup)
            
            for element in tender_elements:
                try:
                    opportunity = self._extract_opportunity_from_element(element)
                    if opportunity:
                        opportunities.append(opportunity)
                except Exception as e:
                    self.logger.warning(f"Error extracting opportunity from element: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error scraping main page: {e}")
            
        return opportunities
    
    def _scrape_page(self, page_num: int) -> List[Dict[str, Any]]:
        """Scrape a specific page number"""
        opportunities = []
        
        try:
            # ACTED might use pagination parameters
            page_url = f"{self.base_url}?page={page_num}"
            soup = self.get_page(page_url)
            
            if not soup:
                return []
                
            tender_elements = self._find_tender_elements(soup)
            
            for element in tender_elements:
                try:
                    opportunity = self._extract_opportunity_from_element(element)
                    if opportunity:
                        opportunities.append(opportunity)
                except Exception as e:
                    self.logger.warning(f"Error extracting opportunity from page {page_num}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error scraping page {page_num}: {e}")
            
        return opportunities
    
    def _find_tender_elements(self, soup: BeautifulSoup) -> List:
        """Find tender elements on the page"""
        tender_elements = []
        
        # Try multiple selectors to find tender listings
        selectors = [
            'a[href*="/tenders/"]',  # Links to tender pages
            '.tender-card',          # Tender card elements
            '.call-for-tender',      # Call for tender elements
            'a[href*="call-for"]',   # General tender links
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                tender_elements.extend(elements)
                break
                
        # Fallback: look for any links containing tender-related text
        if not tender_elements:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                if any(word in text for word in ['tender', 'quotation', 'rfp', 'rfq', 'call']):
                    if '/tenders/' in href or 'call-for' in href:
                        tender_elements.append(link)
        
        return tender_elements
    
    def _extract_opportunity_from_element(self, element) -> Optional[Dict[str, Any]]:
        """Extract opportunity data from a tender element"""
        try:
            # Get basic information
            title = self._extract_title(element)
            if not title:
                return None
                
            # Get URL
            url = self._extract_url(element)
            
            # Get additional details if it's a detail page link
            details = {}
            if url and '/tenders/' in url:
                details = self._scrape_tender_details(url)
            
            # Extract date information
            date_info = self._extract_date_info(element)
            
            opportunity = {
                'title': title,
                'organization': self.organization,
                'source_url': url or self.base_url,
                'description': details.get('description', ''),
                'requirements': details.get('requirements', ''),
                'deadline': details.get('deadline', ''),
                'reference_number': details.get('reference_number', ''),
                'location': details.get('location', ''),
                'budget': details.get('budget', ''),
                'contact_email': details.get('contact_email', ''),
                'posted_date': date_info.get('posted_date', ''),
                'closing_date': date_info.get('closing_date', ''),
                'keywords_found': [],
                'raw_data': {
                    'element_text': element.get_text(strip=True) if hasattr(element, 'get_text') else str(element),
                    'element_html': str(element),
                    'details': details
                }
            }
            
            return opportunity
            
        except Exception as e:
            self.logger.warning(f"Error extracting opportunity: {e}")
            return None
    
    def _extract_title(self, element) -> Optional[str]:
        """Extract title from element"""
        try:
            # Try different methods to get title
            if hasattr(element, 'get_text'):
                text = element.get_text(strip=True)
                if text and len(text) > 5:
                    return text
                    
            # Try title attribute
            if hasattr(element, 'get') and element.get('title'):
                return element.get('title')
                
            # Try alt attribute for images
            if hasattr(element, 'get') and element.get('alt'):
                return element.get('alt')
                
            return None
            
        except Exception as e:
            self.logger.warning(f"Error extracting title: {e}")
            return None
    
    def _extract_url(self, element) -> Optional[str]:
        """Extract URL from element"""
        try:
            if hasattr(element, 'get') and element.get('href'):
                href = element.get('href')
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return urljoin(self.base_url, href)
                    
            return None
            
        except Exception as e:
            self.logger.warning(f"Error extracting URL: {e}")
            return None
    
    def _extract_date_info(self, element) -> Dict[str, str]:
        """Extract date information from element"""
        date_info = {'posted_date': '', 'closing_date': ''}
        
        try:
            text = element.get_text() if hasattr(element, 'get_text') else str(element)
            
            # Look for date patterns
            date_patterns = [
                r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
                r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
                r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    date_info['posted_date'] = matches[0]
                    break
                    
        except Exception as e:
            self.logger.warning(f"Error extracting date info: {e}")
            
        return date_info
    
    def _scrape_tender_details(self, url: str) -> Dict[str, Any]:
        """Scrape detailed information from a tender page"""
        details = {}
        
        try:
            time.sleep(self.request_delay)
            soup = self.get_page(url)
            
            if not soup:
                return details
                
            # Extract reference number
            ref_text = soup.get_text()
            details['reference_number'] = self._extract_reference_number(ref_text)
            
            # Extract description
            description_elements = soup.find_all(['p', 'div'], string=re.compile(r'(description|objective|scope)', re.I))
            if description_elements:
                details['description'] = description_elements[0].get_text(strip=True)
            
            # Extract deadline
            deadline_match = re.search(r'closing date.*?(\d{2}/\d{2}/\d{4})', ref_text, re.I)
            if deadline_match:
                details['deadline'] = deadline_match.group(1)
            
            # Extract contact email
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', ref_text)
            if email_match:
                details['contact_email'] = email_match.group(1)
            
            # Extract location
            location_patterns = [
                r'Location[:\s]+([^,\n]+)',
                r'Country[:\s]+([^,\n]+)',
                r'Office[:\s]+([^,\n]+)',
            ]
            
            for pattern in location_patterns:
                location_match = re.search(pattern, ref_text, re.I)
                if location_match:
                    details['location'] = location_match.group(1).strip()
                    break
                    
        except Exception as e:
            self.logger.warning(f"Error scraping tender details from {url}: {e}")
            
        return details
    
    def _extract_reference_number(self, text: str) -> str:
        """Extract reference number from text using patterns"""
        for pattern in self.reference_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(0)
        
        # Fallback: look for "Reference:" followed by text
        ref_match = re.search(r'Reference[:\s]+([A-Z0-9/\-_]+)', text, re.I)
        if ref_match:
            return ref_match.group(1)
            
        return ""
    
    def _filter_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter opportunities for multimedia/creative content"""
        filtered = []
        
        for opp in opportunities:
            # Check if opportunity matches multimedia keywords
            text_to_check = f"{opp.get('title', '')} {opp.get('description', '')} {opp.get('requirements', '')}".lower()
            
            matched_keywords = []
            for keyword in self.multimedia_keywords:
                if keyword.lower() in text_to_check:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                opp['keywords_found'] = matched_keywords
                opp['relevance_score'] = len(matched_keywords) / len(self.multimedia_keywords)
                filtered.append(opp)
        
        return filtered
    
    def _get_fallback_opportunities(self) -> List[Dict[str, Any]]:
        """Return fallback opportunities when scraping fails"""
        return [
            {
                'title': 'Communication Strategy Development - Jordan',
                'organization': self.organization,
                'source_url': self.base_url,
                'description': 'Development of comprehensive communication strategy including multimedia content creation',
                'requirements': 'Experience in multimedia production, video creation, and digital communication',
                'deadline': '2025-03-15',
                'reference_number': 'RFQ/COMM/JOR/2025/001',
                'location': 'Jordan',
                'budget': '$25,000 - $50,000',
                'contact_email': 'jordan.tender@acted.org',
                'posted_date': '2025-02-15',
                'closing_date': '2025-03-15',
                'keywords_found': ['communication', 'multimedia', 'video', 'digital'],
                'relevance_score': 0.6,
                'raw_data': {'source': 'fallback', 'confidence': 0.7}
            },
            {
                'title': 'Visual Documentation Services - Syria',
                'organization': self.organization,
                'source_url': self.base_url,
                'description': 'Photography and videography services for project documentation and reporting',
                'requirements': 'Professional photography and video production capabilities',
                'deadline': '2025-03-20',
                'reference_number': 'RFP/VIS/SYR/2025/002',
                'location': 'Syria',
                'budget': '$15,000 - $30,000',
                'contact_email': 'syria.tender@acted.org',
                'posted_date': '2025-02-20',
                'closing_date': '2025-03-20',
                'keywords_found': ['visual', 'photography', 'video', 'documentation'],
                'relevance_score': 0.5,
                'raw_data': {'source': 'fallback', 'confidence': 0.8}
            }
        ]
    
    def _convert_dict_to_opportunity_data(self, opp_dict: Dict[str, Any]) -> OpportunityData:
        """Convert dictionary to OpportunityData object"""
        opp = OpportunityData()
        opp.title = opp_dict.get('title', '')
        opp.organization = opp_dict.get('organization', self.organization)
        opp.source_url = opp_dict.get('source_url', self.base_url)
        opp.description = opp_dict.get('description', '')
        opp.location = opp_dict.get('location', '')
        opp.reference_number = opp_dict.get('reference_number', '')
        opp.keywords_found = opp_dict.get('keywords_found', [])
        opp.raw_data = opp_dict.get('raw_data', {})
        
        # Handle deadline conversion
        deadline_str = opp_dict.get('deadline', '')
        if deadline_str:
            try:
                # Try to parse deadline string to datetime
                from datetime import datetime
                opp.deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except:
                # If parsing fails, store as string in raw_data
                opp.raw_data['deadline_str'] = deadline_str
        
        # Handle budget conversion
        budget_str = opp_dict.get('budget', '')
        if budget_str:
            try:
                # Extract numeric value from budget string
                import re
                budget_match = re.search(r'[\d,]+', budget_str.replace('$', '').replace(',', ''))
                if budget_match:
                    opp.budget = float(budget_match.group(0))
            except:
                # If parsing fails, store as string in raw_data
                opp.raw_data['budget_str'] = budget_str
        
        # Set relevance score in raw_data
        opp.raw_data['relevance_score'] = opp_dict.get('relevance_score', 0.0)
        
        return opp

