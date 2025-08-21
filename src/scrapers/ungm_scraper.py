"""
UNGM (United Nations Global Marketplace) Scraper
Scrapes procurement opportunities from https://www.ungm.org/Public/Notice
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import logging
from typing import Dict, Any
from .base_scraper import OpportunityData, BaseScraper

class UNGMScraper(BaseScraper):
    def _extract_reference_from_text(self, text: str) -> str:
        """Extract reference number from text using known patterns."""
        for pattern in self.reference_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return ''
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'UN Global Marketplace',
                'url': 'https://www.ungm.org/Public/Notice',
                'type': 'ungm',
                'priority': 1.0
            }
        
        super().__init__(config, website_config)
        self.base_url = "https://www.ungm.org"
        self.search_url = "https://www.ungm.org/Public/Notice"
        self.name = "UNGM"
        
        # UNGM-specific configuration
        scraper_config = config.get('scraper_configs', {}).get('ungm', {})
        self.max_pages = scraper_config.get('max_pages', 10)
        self.results_per_page = 15  # UNGM shows 15 results per page
        self.request_delay = scraper_config.get('request_delay', 2.0)
        
        # Reference number patterns for UN organizations
        self.reference_patterns = [
            r'RFP/\d{4}/[A-Z]+/[A-Z]{3}/\d+',  # RFP/2025/ACNUR/MEX/047
            r'UNDP-[A-Z]{3}-\d{5,6}',          # UNDP-FJI-00666
            r'UNW-[A-Z]{3}-\d{4}-\d{5}-\d',    # UNW-FJI-2025-00021-2
            r'RFQ/[A-Z]+/\d{4}/\d+',           # RFQ/CRPC/2025/003
            r'RFP\d{7}',                       # RFP9198628
            r'\d{4}/[A-Z]+/[A-Z]+/\d+',       # 2025/FLPER/FLPER/133103
            r'UNDP-HQ-\d{5}',                 # UNDP-HQ-01804
            r'LRPS-\d{4}-\d{7}',              # LRPS-2025-9198844
            r'LRFQ-\d{7}',                     # LRFQ-9199119
            r'EOIOSESGY\d{5}',                 # EOIOSESGY23781
        ]
        
        self.logger = logging.getLogger(__name__)

    def scrape_opportunities(self):
        """
        Scrape opportunities from UNGM
        """
        opportunities = []
        
        try:
            self.logger.info(f"Starting UNGM scraping from {self.search_url}")
            
            # Get initial page to understand pagination
            soup = self.get_page(self.search_url)
            if not soup:
                return opportunities
            
            # Extract total number of opportunities
            total_text = None
            for label in soup.find_all('label'):
                label_text = label.get_text()
                if 'of' in label_text:
                    total_text = label
                    break
            total_opportunities = 0
            if total_text:
                # Extract number from text like "Displaying results 1 to 15 of 1746"
                match = re.search(r'of\s+(\d+)', total_text.get_text())
                if match:
                    total_opportunities = int(match.group(1))
                    
            self.logger.info(f"Found {total_opportunities} total opportunities on UNGM")
            
            # Calculate number of pages to scrape
            max_opportunities = self.max_pages * self.results_per_page
            opportunities_to_scrape = min(total_opportunities, max_opportunities)
            pages_to_scrape = min(self.max_pages, (opportunities_to_scrape + self.results_per_page - 1) // self.results_per_page)
            
            # Scrape opportunities from multiple pages
            for page in range(pages_to_scrape):
                self.logger.info(f"Scraping UNGM page {page + 1}/{pages_to_scrape}")
                
                if page == 0:
                    # Use the initial response for first page
                    page_opportunities = self._parse_opportunities_page(soup)
                else:
                    # Get subsequent pages (would need to implement pagination logic)
                    # For now, we'll work with the first page
                    break
                    
                opportunities.extend(page_opportunities)
                
                # Rate limiting
                if page < pages_to_scrape - 1:
                    time.sleep(self.request_delay)
                    
        except Exception as e:
            self.logger.error(f"Error scraping UNGM: {str(e)}")
            
        self.logger.info(f"UNGM scraping completed. Found {len(opportunities)} opportunities")
        return opportunities

    def _parse_opportunities_page(self, soup):
        """
        Parse opportunities from a single page
        """
        opportunities = []
        
        try:
            # Find all opportunity rows in the table
            # UNGM uses a specific structure for opportunity listings
            opportunity_rows = soup.find_all('div', class_=lambda x: x and 'opportunity' in x.lower()) or \
                             soup.find_all('tr')[1:]  # Skip header row
            
            # If no specific opportunity divs found, look for table rows with opportunity data
            if not opportunity_rows:
                # Look for the main content area with opportunities
                content_area = soup.find('div', class_='content') or soup.find('main') or soup
                
                # Find all links that contain opportunity titles
                opportunity_links = content_area.find_all('a', href=True)
                opportunity_links = [link for link in opportunity_links if self._is_opportunity_link(link)]
                
                for link in opportunity_links:
                    opportunity = self._parse_opportunity_from_link(link)
                    if opportunity:
                        opportunities.append(opportunity)
            else:
                # Parse structured opportunity rows
                for row in opportunity_rows:
                    opportunity = self._parse_opportunity_row(row)
                    if opportunity:
                        opportunities.append(opportunity)
                        
        except Exception as e:
            self.logger.error(f"Error parsing UNGM opportunities page: {str(e)}")
            
        return opportunities

    def _is_opportunity_link(self, link):
        """
        Check if a link represents an opportunity
        """
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Skip navigation and utility links
        skip_patterns = [
            'javascript:', 'mailto:', '#', 
            'help', 'login', 'register', 'home',
            'search', 'filter', 'sort'
        ]
        
        if any(pattern in href.lower() for pattern in skip_patterns):
            return False
            
        # Look for opportunity indicators
        opportunity_indicators = [
            'rfp', 'rfq', 'itb', 'eoi', 'tender', 'procurement',
            'proposal', 'quotation', 'bid', 'consultant'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in opportunity_indicators) and len(text) > 20

    def _parse_opportunity_from_link(self, link):
        """
        Parse opportunity data from a link element and surrounding context
        """
        try:
            title = link.get_text(strip=True)
            url = urljoin(self.base_url, link.get('href', ''))
            
            # Find parent container to extract additional data
            parent = link.find_parent('tr')
            if not parent:
                # Try to find a div with class containing 'row'
                for ancestor in link.parents:
                    if ancestor.name == 'div' and ancestor.has_attr('class') and any('row' in c.lower() for c in ancestor['class']):
                        parent = ancestor
                        break
            
            # Extract data from parent container
            deadline = self._extract_deadline_from_context(parent) if parent else None
            organization = self._extract_organization_from_context(parent) if parent else None
            country = self._extract_country_from_context(parent) if parent else None
            reference = self._extract_reference_from_text(title)
            
            # Create opportunity object
            opportunity = {
                'title': title,
                'url': url,
                'deadline': deadline,
                'organization': organization or 'UN Organization',
                'location': country or 'Not specified',
                'reference_number': reference,
                'source': self.name,
                'scraped_at': datetime.now().isoformat(),
                'description': title,  # Use title as description for now
                'budget': None,  # Not typically available in listings
                'type': self._determine_opportunity_type(title)
            }
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"Error parsing UNGM opportunity from link: {str(e)}")
            return None

    def _parse_opportunity_row(self, row):
        """
        Parse opportunity data from a table row
        """
        try:
            # Extract data from table cells
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                return None
                
            # Typical UNGM table structure:
            # Title | Deadline | Published | Organization | Type | Reference | Country
            
            title_cell = cells[0] if cells else None
            title = title_cell.get_text(strip=True) if title_cell else ''
            
            # Extract URL from title cell
            title_link = title_cell.find('a') if title_cell else None
            url = urljoin(self.base_url, title_link.get('href', '')) if title_link and title_link.has_attr('href') else ''
            
            # Extract other fields based on position
            deadline = cells[1].get_text(strip=True) if len(cells) > 1 else None
            organization = cells[3].get_text(strip=True) if len(cells) > 3 else 'UN Organization'
            opportunity_type = cells[4].get_text(strip=True) if len(cells) > 4 else None
            reference = cells[5].get_text(strip=True) if len(cells) > 5 else None
            country = cells[6].get_text(strip=True) if len(cells) > 6 else None
            
            # Clean and validate reference number
            if not reference:
                reference = self._extract_reference_from_text(title)
                
            # Parse deadline
            parsed_deadline = self._parse_deadline(deadline) if deadline else None
            
            opportunity = {
                'title': title,
                'url': url,
                'deadline': parsed_deadline,
                'organization': organization,
                'location': country or 'Not specified',
                'reference_number': reference,
                'source': self.name,
                'scraped_at': datetime.now().isoformat(),
                'description': title,
                'budget': None,
                'type': opportunity_type or self._determine_opportunity_type(title)
            }
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"Error parsing UNGM opportunity row: {str(e)}")
            return None

    def _extract_deadline_from_context(self, context):
        """
        Extract deadline from surrounding context
        """
        if not context:
            return None
            
        text = context.get_text()
        
        # Look for deadline patterns
        deadline_patterns = [
            r'(\d{1,2}[-/]\w{3}[-/]\d{4})',  # 13-Aug-2025
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # 13/08/2025
            r'(\w{3}\s+\d{1,2},?\s+\d{4})',  # Aug 13, 2025
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, text)
            if match:
                return self._parse_deadline(match.group(1))
                
        return None

    def _extract_organization_from_context(self, context):
        """
        Extract organization from surrounding context
        """
        if not context:
            return None
            
        text = context.get_text()
        
        # Common UN organizations
        un_orgs = [
            'UNDP', 'UNICEF', 'UNHCR', 'UNOPS', 'UN-Women', 'FAO', 
            'WFP', 'WHO', 'ILO', 'UNESCO', 'UNIDO', 'UNFPA'
        ]
        
        for org in un_orgs:
            if org in text:
                return org
                
        return None

    def _extract_country_from_context(self, context):
        """
        Extract country from surrounding context
        """
        if not context:
            return None
            
        text = context.get_text()
        
        # Look for country patterns (this is a simplified approach)
        # In a full implementation, you'd use a comprehensive country list
        common_countries = [
            'Afghanistan', 'Albania', 'Algeria', 'Angola', 'Argentina', 'Armenia',
            'Bangladesh', 'Bolivia', 'Brazil', 'Burkina Faso', 'Cambodia', 'Cameroon',
            'Chad', 'Colombia', 'Congo', 'Costa Rica', 'Ecuador', 'Egypt', 'Ethiopia',
            'Ghana', 'Guatemala', 'Guinea', 'Haiti', 'Honduras', 'India', 'Indonesia',
            'Iraq', 'Jordan', 'Kenya', 'Lebanon', 'Liberia', 'Madagascar', 'Mali',
            'Mexico', 'Morocco', 'Mozambique', 'Myanmar', 'Nepal', 'Nicaragua',
            'Niger', 'Nigeria', 'Pakistan', 'Peru', 'Philippines', 'Rwanda',
            'Senegal', 'Sierra Leone', 'Somalia', 'South Sudan', 'Sudan', 'Syria',
            'Tajikistan', 'Tanzania', 'Tunisia', 'Turkey', 'Uganda', 'Ukraine',
            'Venezuela', 'Yemen', 'Zambia', 'Zimbabwe'
        ]
        
        for country in common_countries:
            if country in text:
                return country
                
        return None

    def _parse_deadline(self, deadline_str):
        """
        Parse deadline string into datetime
        """
        if not deadline_str:
            return None
            
        try:
            # Clean the deadline string
            deadline_str = deadline_str.strip()
            
            # Handle different date formats
            date_formats = [
                '%d-%b-%Y',      # 13-Aug-2025
                '%d/%m/%Y',      # 13/08/2025
                '%m/%d/%Y',      # 08/13/2025
                '%Y-%m-%d',      # 2025-08-13
                '%b %d, %Y',     # Aug 13, 2025
                '%d %b %Y',      # 13 Aug 2025
            ]
            
            # Extract just the date part (remove time and timezone info)
            date_part = re.search(r'(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|\w{3}\s+\d{1,2},?\s+\d{4})', deadline_str)
            if date_part:
                deadline_str = date_part.group(1)
            
            for date_format in date_formats:
                try:
                    return datetime.strptime(deadline_str, date_format).isoformat()
                except ValueError:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Could not parse deadline '{deadline_str}': {str(e)}")
            
        return None

    def _determine_opportunity_type(self, title):
        """
        Determine opportunity type from title
        """
        title_lower = title.lower()
        
        if 'rfp' in title_lower or 'proposal' in title_lower:
            return 'Request for Proposal'
        elif 'rfq' in title_lower or 'quotation' in title_lower:
            return 'Request for Quotation'
        elif 'itb' in title_lower or 'bid' in title_lower:
            return 'Invitation to Bid'
        elif 'eoi' in title_lower or 'expression of interest' in title_lower:
            return 'Expression of Interest'
        elif 'consultant' in title_lower:
            return 'Individual Consultant'
        else:
            return 'Procurement Notice'

    def test_connection(self):
        """
        Test connection to UNGM website
        """
        try:
            soup = self.get_page(self.search_url)
            return soup is not None
        except Exception as e:
            self.logger.error(f"UNGM connection test failed: {str(e)}")
            return False

    def get_opportunity_details(self, opportunity_url):
        """
        Get detailed information for a specific opportunity
        """
        try:
            soup = self.get_page(opportunity_url)
            if not soup:
                return None
            
            # Extract detailed information
            details = {
                'full_description': self._extract_full_description(soup),
                'requirements': self._extract_requirements(soup),
                'contact_info': self._extract_contact_info(soup),
                'documents': self._extract_documents(soup)
            }
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting UNGM opportunity details: {str(e)}")
            return None

    def _extract_full_description(self, soup):
        """Extract full description from opportunity detail page"""
        description_selectors = [
            'div.description',
            'div.content',
            'div.details',
            'p'
        ]
        
        for selector in description_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
                
        return None

    def _extract_requirements(self, soup):
        """Extract requirements from opportunity detail page"""
        # Look for requirements section
        requirements_section = soup.find(text=re.compile(r'requirements?', re.I))
        if requirements_section:
            parent = requirements_section.find_parent()
            if parent:
                return parent.get_text(strip=True)
                
        return None

    def _extract_contact_info(self, soup):
        """Extract contact information from opportunity detail page"""
        # Look for contact information
        contact_patterns = [
            r'contact[:\s]+([^<\n]+)',
            r'email[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'phone[:\s]+([+\d\s\-\(\)]+)'
        ]
        
        text = soup.get_text()
        contacts = {}
        
        for pattern in contact_patterns:
            matches = re.findall(pattern, text, re.I)
            if matches:
                contacts[pattern.split('[')[0]] = matches[0]
                
        return contacts if contacts else None


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

    def _extract_documents(self, soup):
        """Extract document links from opportunity detail page"""
        documents = []
        
        # Look for document links
        doc_links = soup.find_all('a', href=True)
        for link in doc_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if it's a document link
            doc_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
            if any(ext in href.lower() for ext in doc_extensions):
                documents.append({
                    'title': text,
                    'url': urljoin(self.base_url, href)
                })
                
        return documents if documents else None

