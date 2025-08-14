"""
Global Fund Scraper
Scrapes procurement opportunities from The Global Fund to Fight AIDS, Tuberculosis and Malaria
https://www.theglobalfund.org/en/business-opportunities/
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
import logging
from typing import Dict, Any
from .base_scraper import OpportunityData, BaseScraper

class GlobalFundScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'Global Fund',
                'url': 'https://www.theglobalfund.org/en/business-opportunities/',
                'type': 'globalfund',
                'priority': 1.0
            }
        
        super().__init__(config, website_config)
        self.base_url = "https://www.theglobalfund.org"
        self.business_opportunities_url = "https://www.theglobalfund.org/en/business-opportunities/"
        self.oracle_base_url = "https://fa-enmo-saasfaprod1.fa.ocs.oraclecloud.com"
        self.name = "Global Fund"
        
        # Global Fund specific configuration
        scraper_config = config.get('scraper_configs', {}).get('globalfund', {})
        self.max_tenders = scraper_config.get('max_tenders', 50)
        self.request_delay = scraper_config.get('request_delay', 3.0)
        
        # Reference number pattern for Global Fund
        self.reference_patterns = [
            r'TGF-\d{2}-\d{2,3}(?:,\d+)?',  # TGF-25-46, TGF-25-41,1
        ]
        
        self.logger = logging.getLogger(__name__)
        
        # Oracle system may require specific headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def scrape_opportunities(self):
        """
        Scrape opportunities from Global Fund
        """
        opportunities = []
        
        try:
            self.logger.info(f"Starting Global Fund scraping from {self.business_opportunities_url}")
            
            # First, get the main business opportunities page
            soup = self.get_page(self.business_opportunities_url)
            if not soup:
                return opportunities
            
            # Find the "VIEW OPEN TENDERS" link or similar
            tender_link = self._find_tender_link(soup)
            if not tender_link:
                self.logger.warning("Could not find tender link on Global Fund page")
                return opportunities
                
            self.logger.info(f"Found tender link: {tender_link}")
            
            # Navigate to the Oracle tender system
            oracle_soup = self.get_page(tender_link)
            if not oracle_soup:
                return opportunities
            
            # Parse opportunities from Oracle system
            opportunities = self._parse_oracle_tenders(oracle_soup)
            
        except Exception as e:
            self.logger.error(f"Error scraping Global Fund: {str(e)}")
            
        self.logger.info(f"Global Fund scraping completed. Found {len(opportunities)} opportunities")
        return opportunities

    def _find_tender_link(self, soup):
        """
        Find the link to the tender system
        """
        # Look for "VIEW OPEN TENDERS" button or similar
        tender_selectors = [
            'a[href*="oracle"]',
            'a[href*="tender"]',
            'a:contains("VIEW OPEN TENDERS")',
            'a:contains("Open Tenders")',
            'a:contains("Tenders")'
        ]
        
        for selector in tender_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    href = element.get('href')
                    if href:
                        return urljoin(self.base_url, href)
            except:
                continue
                
        # Fallback: look for any link containing oracle or tender
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '').lower()
            text = link.get_text().lower()
            
            if 'oracle' in href or 'tender' in href or 'tender' in text:
                return urljoin(self.base_url, link.get('href'))
                
        return None

    def _parse_oracle_tenders(self, soup):
        """
        Parse tenders from Oracle system page
        """
        opportunities = []
        
        try:
            # Look for the tender table
            # Oracle systems typically use tables for data display
            tables = soup.find_all('table')
            
            tender_table = None
            for table in tables:
                # Look for table headers that indicate tender data
                headers = table.find_all(['th', 'td'])
                header_text = ' '.join([h.get_text().lower() for h in headers[:10]])  # Check first 10 cells
                
                if any(keyword in header_text for keyword in ['negotiation', 'title', 'status', 'deadline', 'close']):
                    tender_table = table
                    break
                    
            if not tender_table:
                self.logger.warning("Could not find tender table in Oracle system")
                return opportunities
                
            # Parse table rows
            rows = tender_table.find_all('tr')[1:]  # Skip header row
            
            for row in rows[:self.max_tenders]:  # Limit number of tenders
                opportunity = self._parse_oracle_tender_row(row)
                if opportunity:
                    opportunities.append(opportunity)
                    
        except Exception as e:
            self.logger.error(f"Error parsing Oracle tenders: {str(e)}")
            
        return opportunities

    def _parse_oracle_tender_row(self, row):
        """
        Parse a single tender row from Oracle system
        """
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                return None
                
            # Typical Oracle tender table structure:
            # Negotiation | Title | Type | Status | Posting Date | Open Date | Close Date
            
            # Extract basic information
            negotiation_id = cells[0].get_text(strip=True) if len(cells) > 0 else ''
            title = cells[1].get_text(strip=True) if len(cells) > 1 else ''
            tender_type = cells[2].get_text(strip=True) if len(cells) > 2 else ''
            status = cells[3].get_text(strip=True) if len(cells) > 3 else ''
            posting_date = cells[4].get_text(strip=True) if len(cells) > 4 else ''
            open_date = cells[5].get_text(strip=True) if len(cells) > 5 else ''
            close_date = cells[6].get_text(strip=True) if len(cells) > 6 else ''
            
            # Skip closed or inactive tenders
            if status.lower() in ['closed', 'cancelled', 'awarded']:
                return None
                
            # Extract URL if available
            title_link = cells[1].find('a') if len(cells) > 1 else None
            url = ''
            if title_link:
                href = title_link.get('href', '')
                if href:
                    url = urljoin(self.oracle_base_url, href)
                    
            # Parse dates
            parsed_deadline = self._parse_oracle_date(close_date) if close_date else None
            parsed_posting_date = self._parse_oracle_date(posting_date) if posting_date else None
            
            # Extract reference number (should be the negotiation ID)
            reference = negotiation_id if negotiation_id else self._extract_reference_from_text(title)
            
            # Determine location/scope
            location = self._determine_location_from_title(title)
            
            opportunity = {
                'title': title,
                'url': url,
                'deadline': parsed_deadline,
                'organization': 'The Global Fund',
                'location': location,
                'reference_number': reference,
                'source': self.name,
                'scraped_at': datetime.now().isoformat(),
                'description': title,  # Use title as description
                'budget': None,  # Not typically available in listings
                'type': tender_type or 'RFP',
                'status': status,
                'posting_date': parsed_posting_date
            }
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"Error parsing Global Fund tender row: {str(e)}")
            return None

    def _parse_oracle_date(self, date_str):
        """
        Parse date from Oracle system format
        """
        if not date_str:
            return None
            
        try:
            # Clean the date string
            date_str = date_str.strip()
            
            # Oracle typically uses formats like:
            # 04/Aug/2025 12:37 PM
            # 31/Jul/2025 4:57 PM
            # 29/Jul/2025 3:26 PM
            
            # Extract just the date part
            date_part = re.search(r'(\d{1,2}/\w{3}/\d{4})', date_str)
            if date_part:
                date_str = date_part.group(1)
                return datetime.strptime(date_str, '%d/%b/%Y').isoformat()
                
            # Try other common formats
            date_formats = [
                '%d/%m/%Y',      # 04/08/2025
                '%m/%d/%Y',      # 08/04/2025
                '%Y-%m-%d',      # 2025-08-04
                '%d-%b-%Y',      # 04-Aug-2025
                '%b %d, %Y',     # Aug 04, 2025
            ]
            
            for date_format in date_formats:
                try:
                    return datetime.strptime(date_str, date_format).isoformat()
                except ValueError:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Could not parse Global Fund date '{date_str}': {str(e)}")
            
        return None

    def _determine_location_from_title(self, title):
        """
        Determine location/scope from opportunity title
        """
        title_lower = title.lower()
        
        # Look for country/region mentions
        locations = {
            'angola': 'Angola',
            'drc': 'Democratic Republic of Congo',
            'congo': 'Democratic Republic of Congo',
            'mauritania': 'Mauritania',
            'guinea bissau': 'Guinea Bissau',
            'togo': 'Togo',
            'africa': 'Africa',
            'global': 'Global',
            'multi-country': 'Multi-country',
            'regional': 'Regional'
        }
        
        for keyword, location in locations.items():
            if keyword in title_lower:
                return location
                
        # Default to Global for Global Fund opportunities
        return 'Global'

    def test_connection(self):
        """
        Test connection to Global Fund website
        """
        try:
            soup = self.get_page(self.business_opportunities_url)
            return soup is not None
        except Exception as e:
            self.logger.error(f"Global Fund connection test failed: {str(e)}")
            return False

    def get_opportunity_details(self, opportunity_url):
        """
        Get detailed information for a specific opportunity
        """
        try:
            if not opportunity_url or 'oracle' not in opportunity_url:
                return None
                
            soup = self.get_page(opportunity_url)
            if not soup:
                return None
            
            # Extract detailed information from Oracle tender page
            details = {
                'full_description': self._extract_oracle_description(soup),
                'requirements': self._extract_oracle_requirements(soup),
                'contact_info': self._extract_oracle_contact_info(soup),
                'documents': self._extract_oracle_documents(soup),
                'timeline': self._extract_oracle_timeline(soup)
            }
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting Global Fund opportunity details: {str(e)}")
            return None

    def _extract_oracle_description(self, soup):
        """Extract description from Oracle tender detail page"""
        description_selectors = [
            'div[id*="description"]',
            'div[class*="description"]',
            'div[id*="details"]',
            'div[class*="details"]',
            'div[id*="content"]'
        ]
        
        for selector in description_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if len(text) > 50:  # Ensure it's substantial content
                    return text
                    
        return None

    def _extract_oracle_requirements(self, soup):
        """Extract requirements from Oracle tender detail page"""
        # Look for requirements or eligibility sections
        requirements_keywords = ['requirement', 'eligibility', 'criteria', 'qualification']
        
        for keyword in requirements_keywords:
            # Look for headings containing the keyword
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                if keyword in heading.get_text().lower():
                    # Get the content following this heading
                    next_element = heading.find_next_sibling()
                    if next_element:
                        return next_element.get_text(strip=True)
                        
        return None

    def _extract_oracle_contact_info(self, soup):
        """Extract contact information from Oracle tender detail page"""
        contact_info = {}
        
        # Look for contact information patterns
        text = soup.get_text()
        
        # Email pattern
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
            
        # Phone pattern
        phone_pattern = r'(?:phone|tel|telephone)[:\s]+([+\d\s\-\(\)]+)'
        phones = re.findall(phone_pattern, text, re.I)
        if phones:
            contact_info['phone'] = phones[0].strip()
            
        return contact_info if contact_info else None

    def _extract_oracle_documents(self, soup):
        """Extract document links from Oracle tender detail page"""
        documents = []
        
        # Look for document links
        doc_links = soup.find_all('a', href=True)
        for link in doc_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if it's a document link
            doc_indicators = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', 'download', 'document', 'attachment']
            if any(indicator in href.lower() or indicator in text.lower() for indicator in doc_indicators):
                documents.append({
                    'title': text,
                    'url': urljoin(self.oracle_base_url, href)
                })
                
        return documents if documents else None

    def _extract_oracle_timeline(self, soup):
        """Extract timeline information from Oracle tender detail page"""
        timeline = {}
        
        # Look for date-related information
        date_keywords = ['posting', 'open', 'close', 'deadline', 'submission']
        
        for keyword in date_keywords:
            # Look for labels containing date keywords
            labels = soup.find_all(['label', 'span', 'div'], string=re.compile(keyword, re.I))
            for label in labels:
                # Get the next element which might contain the date
                next_element = label.find_next_sibling() or label.parent.find_next_sibling()
                if next_element:
                    date_text = next_element.get_text(strip=True)
                    parsed_date = self._parse_oracle_date(date_text)
                    if parsed_date:
                        timeline[keyword.lower()] = parsed_date
                        
        return timeline if timeline else None


    def _convert_dict_to_opportunity_data(self, opp_dict: Dict[str, Any]) -> OpportunityData:
        """Convert dictionary to OpportunityData object"""
        opp = OpportunityData()
        
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
        
        # Handle deadline conversion
        deadline = opp_dict.get('deadline')
        if deadline:
            if isinstance(deadline, str):
                try:
                    opp.deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                except:
                    opp.deadline = None
            elif isinstance(deadline, datetime):
                opp.deadline = deadline
        
        # Handle budget conversion
        budget = opp_dict.get('budget')
        if budget:
            if isinstance(budget, (int, float)):
                opp.budget = float(budget)
            elif isinstance(budget, str):
                try:
                    # Extract numeric value from budget string
                    import re
                    numbers = re.findall(r'[\d,]+\.?\d*', budget.replace(',', ''))
                    if numbers:
                        opp.budget = float(numbers[0])
                except:
                    opp.budget = None
        
        # Handle extracted date
        extracted_date = opp_dict.get('extracted_date')
        if extracted_date:
            if isinstance(extracted_date, str):
                try:
                    opp.extracted_date = datetime.fromisoformat(extracted_date.replace('Z', '+00:00'))
                except:
                    opp.extracted_date = datetime.now()
            elif isinstance(extracted_date, datetime):
                opp.extracted_date = extracted_date
        else:
            opp.extracted_date = datetime.now()
        
        # Store all additional data in raw_data
        opp.raw_data = opp_dict.copy()
        
        return opp

    def _is_relevant_opportunity(self, opportunity):
        """
        Check if opportunity is relevant based on Global Fund criteria
        """
        if not opportunity:
            return False
            
        title = opportunity.get('title', '').lower()
        location = opportunity.get('location', '').lower()
        
        # Check for multimedia/creative keywords
        relevant_keywords = [
            'communication', 'media', 'campaign', 'outreach', 'advocacy',
            'training', 'capacity building', 'evaluation', 'assessment',
            'technical assistance', 'consultant', 'expert', 'specialist'
        ]
        
        has_relevant_keywords = any(keyword in title for keyword in relevant_keywords)
        
        # Check geographic exclusions
        excluded_locations = ['india', 'pakistan', 'china', 'bangladesh', 'sri lanka']
        is_excluded_location = any(excluded in location for excluded in excluded_locations)
        
        return has_relevant_keywords and not is_excluded_location

