"""
World Bank Scraper
Scrapes procurement opportunities from World Bank Projects & Operations
https://projects.worldbank.org/en/projects-operations/procurement
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

class WorldBankScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'World Bank',
                'url': 'https://projects.worldbank.org/en/projects-operations/procurement?srce=both',
                'type': 'worldbank',
                'priority': 1.0
            }
        
        super().__init__(config, website_config)
        self.base_url = "https://projects.worldbank.org"
        self.procurement_url = "https://projects.worldbank.org/en/projects-operations/procurement"
        self.name = "World Bank"
        
        # World Bank specific configuration
        scraper_config = config.get('scraper_configs', {}).get('worldbank', {})
        self.max_pages = scraper_config.get('max_pages', 5)
        self.results_per_page = 20  # World Bank shows 20 results per page
        self.max_opportunities = scraper_config.get('max_opportunities', 100)
        self.request_delay = scraper_config.get('request_delay', 2.0)
        
        # Reference number patterns for World Bank projects
        self.reference_patterns = [
            r'P\d{6}',                    # P158522, P168539
            r'WB-\d{4}-\d{3}',           # WB-2025-001
            r'IBRD-\d{5}',               # IBRD-12345
            r'IDA-\d{5}',                # IDA-12345
        ]
        
        self.logger = logging.getLogger(__name__)
        
        # World Bank may require specific headers
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
        Scrape opportunities from World Bank
        """
        opportunities = []
        
        try:
            self.logger.info(f"Starting World Bank scraping from {self.procurement_url}")
            
            # Start with the main procurement page
            url = f"{self.procurement_url}?srce=both"  # Include both Bank and Borrower procurement
            
            # Scrape multiple pages
            for page in range(self.max_pages):
                self.logger.info(f"Scraping World Bank page {page + 1}/{self.max_pages}")
                
                # Add pagination parameters
                page_url = f"{url}&page={page + 1}" if page > 0 else url
                
                soup = self.get_page(page_url)
                if not soup:
                    break
                
                # Parse opportunities from this page
                page_opportunities = self._parse_opportunities_page(soup)
                
                if not page_opportunities:
                    self.logger.info("No more opportunities found, stopping pagination")
                    break
                    
                opportunities.extend(page_opportunities)
                
                # Check if we've reached our limit
                if len(opportunities) >= self.max_opportunities:
                    opportunities = opportunities[:self.max_opportunities]
                    break
                    
                # Rate limiting
                if page < self.max_pages - 1:
                    time.sleep(self.request_delay)
                    
        except Exception as e:
            self.logger.error(f"Error scraping World Bank: {str(e)}")
            
        self.logger.info(f"World Bank scraping completed. Found {len(opportunities)} opportunities")
        return opportunities

    def _parse_opportunities_page(self, soup):
        """
        Parse opportunities from a single page
        """
        opportunities = []
        
        try:
            # Find the procurement table
            # World Bank uses a table structure for displaying procurement notices
            table = soup.find('table') or soup.find('div', class_=lambda x: x and 'table' in x.lower())
            
            if not table:
                # Try alternative selectors for the opportunities list
                opportunities_container = soup.find('div', class_=lambda x: x and ('procurement' in x.lower() or 'notice' in x.lower()))
                if opportunities_container:
                    # Look for individual opportunity items
                    opportunity_items = opportunities_container.find_all(['tr', 'div'], class_=lambda x: x and ('row' in x.lower() or 'item' in x.lower()))
                    
                    for item in opportunity_items:
                        opportunity = self._parse_opportunity_item(item)
                        if opportunity:
                            opportunities.append(opportunity)
                else:
                    self.logger.warning("Could not find procurement table or container")
                    return opportunities
            else:
                # Parse table rows
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    opportunity = self._parse_opportunity_row(row)
                    if opportunity:
                        opportunities.append(opportunity)
                        
        except Exception as e:
            self.logger.error(f"Error parsing World Bank opportunities page: {str(e)}")
            
        return opportunities

    def _parse_opportunity_row(self, row):
        """
        Parse opportunity data from a table row
        """
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 4:
                return None
                
            # World Bank table structure:
            # Description | Country | Project Title | Notice Type | Language | Published Date
            
            description_cell = cells[0] if len(cells) > 0 else None
            country_cell = cells[1] if len(cells) > 1 else None
            project_title_cell = cells[2] if len(cells) > 2 else None
            notice_type_cell = cells[3] if len(cells) > 3 else None
            language_cell = cells[4] if len(cells) > 4 else None
            published_date_cell = cells[5] if len(cells) > 5 else None
            
            # Extract basic information
            description = description_cell.get_text(strip=True) if description_cell else ''
            country = country_cell.get_text(strip=True) if country_cell else ''
            project_title = project_title_cell.get_text(strip=True) if project_title_cell else ''
            notice_type = notice_type_cell.get_text(strip=True) if notice_type_cell else ''
            language = language_cell.get_text(strip=True) if language_cell else ''
            published_date = published_date_cell.get_text(strip=True) if published_date_cell else ''
            
            # Skip if essential information is missing
            if not description or not country:
                return None
                
            # Apply geographic exclusions
            if self._is_excluded_location(country):
                return None
                
            # Extract URLs
            description_link = description_cell.find('a') if description_cell else None
            project_link = project_title_cell.find('a') if project_title_cell else None
            
            opportunity_url = ''
            if description_link:
                opportunity_url = urljoin(self.base_url, description_link.get('href', ''))
            elif project_link:
                opportunity_url = urljoin(self.base_url, project_link.get('href', ''))
                
            # Extract project ID from project title or URL
            project_id = self._extract_project_id(project_title, opportunity_url)
            
            # Parse published date
            parsed_date = self._parse_worldbank_date(published_date) if published_date else None
            
            # Determine if this is a relevant opportunity
            if not self._is_relevant_opportunity(description, notice_type):
                return None
                
            opportunity = {
                'title': description,
                'url': opportunity_url,
                'deadline': None,  # Not typically shown in listing, would need detail page
                'organization': 'World Bank',
                'location': country,
                'reference_number': project_id,
                'source': self.name,
                'scraped_at': datetime.now().isoformat(),
                'description': description,
                'budget': None,  # Not typically available in listings
                'type': notice_type,
                'project_title': project_title,
                'language': language,
                'published_date': parsed_date
            }
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"Error parsing World Bank opportunity row: {str(e)}")
            return None

    def _parse_opportunity_item(self, item):
        """
        Parse opportunity data from a div item (alternative structure)
        """
        try:
            # Extract text content
            text = item.get_text(strip=True)
            if len(text) < 20:  # Skip items with too little content
                return None
                
            # Look for links within the item
            links = item.find_all('a', href=True)
            
            opportunity_url = ''
            title = ''
            
            for link in links:
                link_text = link.get_text(strip=True)
                if len(link_text) > 20:  # Likely the main opportunity title
                    title = link_text
                    opportunity_url = urljoin(self.base_url, link.get('href', ''))
                    break
                    
            if not title:
                title = text[:100] + '...' if len(text) > 100 else text
                
            # Extract other information from the text
            country = self._extract_country_from_text(text)
            project_id = self._extract_project_id(text, opportunity_url)
            
            # Apply geographic exclusions
            if country and self._is_excluded_location(country):
                return None
                
            # Check relevance
            if not self._is_relevant_opportunity(title, ''):
                return None
                
            opportunity = {
                'title': title,
                'url': opportunity_url,
                'deadline': None,
                'organization': 'World Bank',
                'location': country or 'Not specified',
                'reference_number': project_id,
                'source': self.name,
                'scraped_at': datetime.now().isoformat(),
                'description': title,
                'budget': None,
                'type': 'Procurement Notice',
                'project_title': '',
                'language': 'English',
                'published_date': None
            }
            
            return opportunity
            
        except Exception as e:
            self.logger.error(f"Error parsing World Bank opportunity item: {str(e)}")
            return None

    def _extract_project_id(self, text, url):
        """
        Extract World Bank project ID from text or URL
        """
        # Look for P followed by 6 digits
        project_pattern = r'P\d{6}'
        
        # First try the text
        match = re.search(project_pattern, text)
        if match:
            return match.group(0)
            
        # Then try the URL
        if url:
            match = re.search(project_pattern, url)
            if match:
                return match.group(0)
                
        return None

    def _extract_country_from_text(self, text):
        """
        Extract country name from text
        """
        # This is a simplified approach - in production, you'd use a comprehensive country list
        common_countries = [
            'Afghanistan', 'Albania', 'Algeria', 'Angola', 'Argentina', 'Armenia', 'Azerbaijan',
            'Bangladesh', 'Belarus', 'Bolivia', 'Bosnia', 'Brazil', 'Bulgaria', 'Burkina Faso',
            'Cambodia', 'Cameroon', 'Chad', 'Colombia', 'Congo', 'Costa Rica', 'Croatia',
            'Ecuador', 'Egypt', 'Ethiopia', 'Georgia', 'Ghana', 'Guatemala', 'Guinea', 'Haiti',
            'Honduras', 'India', 'Indonesia', 'Iraq', 'Jordan', 'Kazakhstan', 'Kenya', 'Kosovo',
            'Kyrgyz', 'Lebanon', 'Liberia', 'Madagascar', 'Mali', 'Mexico', 'Moldova', 'Mongolia',
            'Morocco', 'Mozambique', 'Myanmar', 'Nepal', 'Nicaragua', 'Niger', 'Nigeria',
            'Pakistan', 'Papua New Guinea', 'Peru', 'Philippines', 'Rwanda', 'Senegal',
            'Sierra Leone', 'Somalia', 'South Sudan', 'Sudan', 'Syria', 'Tajikistan', 'Tanzania',
            'Tunisia', 'Turkey', 'Turkiye', 'Uganda', 'Ukraine', 'Venezuela', 'Vietnam',
            'Yemen', 'Zambia', 'Zimbabwe'
        ]
        
        for country in common_countries:
            if country in text:
                return country
                
        return None

    def _is_excluded_location(self, location):
        """
        Check if location should be excluded based on criteria
        """
        if not location:
            return False
            
        location_lower = location.lower()
        
        # Exclude India, Pakistan, most of Asia (except Nepal), China
        excluded_locations = [
            'india', 'pakistan', 'china', 'bangladesh', 'sri lanka', 'myanmar',
            'thailand', 'vietnam', 'cambodia', 'laos', 'malaysia', 'singapore',
            'indonesia', 'philippines'  # Most of Asia except Nepal
        ]
        
        return any(excluded in location_lower for excluded in excluded_locations)

    def _is_relevant_opportunity(self, title, notice_type):
        """
        Check if opportunity is relevant for multimedia/creative work
        """
        if not title:
            return False
            
        title_lower = title.lower()
        notice_type_lower = notice_type.lower() if notice_type else ''
        
        # Relevant keywords for multimedia/creative opportunities
        relevant_keywords = [
            'communication', 'media', 'campaign', 'outreach', 'advocacy',
            'training', 'capacity building', 'evaluation', 'assessment',
            'technical assistance', 'consultant', 'expert', 'specialist',
            'video', 'photo', 'multimedia', 'design', 'visual',
            'documentation', 'reporting', 'publication', 'website',
            'digital', 'technology', 'ict', 'information system',
            'monitoring', 'evaluation', 'survey', 'study'
        ]
        
        # Check for relevant keywords
        has_relevant_keywords = any(keyword in title_lower for keyword in relevant_keywords)
        
        # Exclude purely construction/infrastructure projects
        excluded_keywords = [
            'construction', 'building', 'road', 'bridge', 'water supply',
            'sewerage', 'drainage', 'irrigation', 'dam', 'power plant',
            'transmission line', 'substation', 'pipeline', 'port',
            'airport', 'railway', 'tunnel'
        ]
        
        has_excluded_keywords = any(keyword in title_lower for keyword in excluded_keywords)
        
        # Include if has relevant keywords and doesn't have excluded keywords
        # OR if it's a consultancy/service type opportunity
        is_service_opportunity = any(service_type in notice_type_lower for service_type in [
            'consultant', 'service', 'technical assistance', 'evaluation'
        ])
        
        return (has_relevant_keywords and not has_excluded_keywords) or is_service_opportunity

    def _parse_worldbank_date(self, date_str):
        """
        Parse date from World Bank format
        """
        if not date_str:
            return None
            
        try:
            # Clean the date string
            date_str = date_str.strip()
            
            # World Bank typically uses formats like:
            # August 12, 2025
            # 12-Aug-2025
            # 2025-08-12
            
            date_formats = [
                '%B %d, %Y',     # August 12, 2025
                '%b %d, %Y',     # Aug 12, 2025
                '%d-%b-%Y',      # 12-Aug-2025
                '%d/%m/%Y',      # 12/08/2025
                '%m/%d/%Y',      # 08/12/2025
                '%Y-%m-%d',      # 2025-08-12
            ]
            
            for date_format in date_formats:
                try:
                    return datetime.strptime(date_str, date_format).isoformat()
                except ValueError:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Could not parse World Bank date '{date_str}': {str(e)}")
            
        return None

    def test_connection(self):
        """
        Test connection to World Bank website
        """
        try:
            soup = self.get_page(self.procurement_url)
            return soup is not None
        except Exception as e:
            self.logger.error(f"World Bank connection test failed: {str(e)}")
            return False

    def get_opportunity_details(self, opportunity_url):
        """
        Get detailed information for a specific opportunity
        """
        try:
            if not opportunity_url:
                return None
                
            soup = self.get_page(opportunity_url)
            if not soup:
                return None
            
            # Extract detailed information
            details = {
                'full_description': self._extract_worldbank_description(soup),
                'requirements': self._extract_worldbank_requirements(soup),
                'contact_info': self._extract_worldbank_contact_info(soup),
                'documents': self._extract_worldbank_documents(soup),
                'timeline': self._extract_worldbank_timeline(soup),
                'project_info': self._extract_project_info(soup)
            }
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting World Bank opportunity details: {str(e)}")
            return None

    def _extract_worldbank_description(self, soup):
        """Extract description from World Bank opportunity detail page"""
        description_selectors = [
            'div.description',
            'div.content',
            'div.details',
            'div.summary',
            'p'
        ]
        
        for selector in description_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if len(text) > 100:  # Ensure substantial content
                    return text
                    
        return None

    def _extract_worldbank_requirements(self, soup):
        """Extract requirements from World Bank opportunity detail page"""
        # Look for requirements sections
        requirements_keywords = ['requirement', 'eligibility', 'criteria', 'qualification', 'specification']
        
        for keyword in requirements_keywords:
            # Look for headings containing the keyword
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                if keyword in heading.get_text().lower():
                    # Get content following this heading
                    content = []
                    next_element = heading.find_next_sibling()
                    while next_element and next_element.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        if next_element.get_text(strip=True):
                            content.append(next_element.get_text(strip=True))
                        next_element = next_element.find_next_sibling()
                    
                    if content:
                        return ' '.join(content)
                        
        return None

    def _extract_worldbank_contact_info(self, soup):
        """Extract contact information from World Bank opportunity detail page"""
        contact_info = {}
        
        text = soup.get_text()
        
        # Email pattern
        email_pattern = r'([a-zA-Z0-9._%+-]+@worldbank\.org|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
            
        # Phone pattern
        phone_pattern = r'(?:phone|tel|telephone)[:\s]+([+\d\s\-\(\)]+)'
        phones = re.findall(phone_pattern, text, re.I)
        if phones:
            contact_info['phone'] = phones[0].strip()
            
        return contact_info if contact_info else None

    def _extract_worldbank_documents(self, soup):
        """Extract document links from World Bank opportunity detail page"""
        documents = []
        
        # Look for document links
        doc_links = soup.find_all('a', href=True)
        for link in doc_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if it's a document link
            doc_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
            doc_keywords = ['download', 'document', 'attachment', 'tender', 'rfp', 'specification']
            
            is_document = (any(ext in href.lower() for ext in doc_extensions) or
                          any(keyword in text.lower() for keyword in doc_keywords))
            
            if is_document and len(text) > 3:
                documents.append({
                    'title': text,
                    'url': urljoin(self.base_url, href)
                })
                
        return documents if documents else None

    def _extract_worldbank_timeline(self, soup):
        """Extract timeline information from World Bank opportunity detail page"""
        timeline = {}
        
        # Look for date-related information
        date_keywords = ['deadline', 'submission', 'closing', 'opening', 'published']
        
        text = soup.get_text()
        
        for keyword in date_keywords:
            # Look for patterns like "Deadline: August 15, 2025"
            pattern = rf'{keyword}[:\s]+([A-Za-z]+ \d{{1,2}}, \d{{4}}|\d{{1,2}}-[A-Za-z]+-\d{{4}}|\d{{4}}-\d{{2}}-\d{{2}})'
            matches = re.findall(pattern, text, re.I)
            if matches:
                parsed_date = self._parse_worldbank_date(matches[0])
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

    def _extract_project_info(self, soup):
        """Extract project information from World Bank opportunity detail page"""
        project_info = {}
        
        # Look for project-specific information
        project_keywords = ['project id', 'project number', 'project title', 'country', 'region']
        
        text = soup.get_text()
        
        for keyword in project_keywords:
            pattern = rf'{keyword}[:\s]+([^\n\r]+)'
            matches = re.findall(pattern, text, re.I)
            if matches:
                project_info[keyword.lower().replace(' ', '_')] = matches[0].strip()
                
        return project_info if project_info else None

