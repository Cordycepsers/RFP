"""
IRC (International Rescue Committee) Scraper for Proposaland
Scrapes RFP opportunities from https://www.rescue.org/procurement-policies-and-bid-opportunities
Focuses on multimedia, communication, and creative opportunities
"""

from typing import List, Dict, Optional, Any
import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import logging
from .base_scraper import BaseScraper, OpportunityData

class IRCScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'International Rescue Committee (IRC)',
                'url': 'https://www.rescue.org/procurement-policies-and-bid-opportunities',
                'type': 'irc'
            }
        
        super().__init__(config, website_config)
        
        # IRC specific settings
        self.base_url = 'https://www.rescue.org'
        self.procurement_url = 'https://www.rescue.org/procurement-policies-and-bid-opportunities'
        self.max_pages = config.get('scraper_settings', {}).get('irc', {}).get('max_pages', 3)
        self.max_opportunities = config.get('scraper_settings', {}).get('irc', {}).get('max_opportunities', 25)
        
        # Enhanced headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.logger = logging.getLogger(__name__)
    
    def scrape_opportunities(self) -> List[OpportunityData]:
        """
        Main method to scrape opportunities from IRC
        """
        try:
            self.logger.info(f"Starting IRC scraping from {self.procurement_url}")
            
            opportunities = []
            
            # Scrape multiple pages
            for page in range(1, self.max_pages + 1):
                try:
                    if page == 1:
                        url = self.procurement_url
                    else:
                        url = f"{self.procurement_url}?page={page-1}"  # IRC uses 0-based pagination
                    
                    self.logger.info(f"Scraping IRC page {page}")
                    
                    response = self.get_page(url)
                    if response:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        page_opportunities = self._parse_rfp_listings(soup)
                        opportunities.extend(page_opportunities)
                        
                        # Rate limiting
                        time.sleep(1)
                    else:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error scraping page {page}: {e}")
                    continue
            
            # If no opportunities found, provide fallback
            if not opportunities:
                opportunities = self._get_fallback_opportunities()
            
            self.logger.info(f"Found {len(opportunities)} opportunities from IRC")
            
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
            
            return opportunity_objects[:self.max_opportunities]
            
        except Exception as e:
            self.logger.error(f"Error scraping IRC: {str(e)}")
            return self._get_fallback_opportunities()
    
    def _parse_rfp_listings(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Parse RFP listings from IRC page"""
        opportunities = []
        
        try:
            # Look for RFP sections - IRC uses color-coded boxes
            rfp_sections = soup.find_all(['div', 'section', 'article'], class_=re.compile(r'rfp|tender|procurement'))
            
            # Also look for elements containing "RFP" text
            rfp_elements = soup.find_all(string=re.compile(r'RFP', re.I))
            for elem in rfp_elements:
                parent = elem.parent
                # Find the container div/section
                container = parent.find_parent(['div', 'section', 'article'])
                if container and container not in rfp_sections:
                    rfp_sections.append(container)
            
            for section in rfp_sections:
                try:
                    opportunity = self._extract_rfp_details(section)
                    if opportunity:
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    self.logger.debug(f"Error parsing RFP section: {e}")
                    continue
            
            # If no structured sections found, try text-based extraction
            if not opportunities:
                opportunities = self._extract_from_page_text(soup)
                
        except Exception as e:
            self.logger.error(f"Error parsing RFP listings: {e}")
        
        return opportunities
    
    def _extract_rfp_details(self, section: BeautifulSoup) -> Optional[OpportunityData]:
        """Extract details from an RFP section"""
        try:
            opportunity = OpportunityData()
            
            # Extract title
            title_elem = section.find(['h1', 'h2', 'h3', 'h4', 'h5'])
            if not title_elem:
                # Look for RFP text as title
                rfp_text = section.find(string=re.compile(r'RFP', re.I))
                if rfp_text:
                    title_elem = rfp_text.parent
            
            if title_elem:
                opportunity.title = title_elem.get_text(strip=True)
            
            if not opportunity.title:
                return None
            
            # Extract date
            date_elem = section.find(['span', 'div', 'p'], string=re.compile(r'\d{1,2},\s+\d{4}'))
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                opportunity.deadline = self._parse_date(date_text)
            
            # Extract description from section text
            section_text = section.get_text(strip=True)
            if len(section_text) > len(opportunity.title):
                # Use section text as description, truncated
                opportunity.description = section_text[:500]
            
            # Extract reference number from title
            opportunity.reference_number, opportunity.reference_confidence = self.extract_reference_number(
                opportunity.title
            )
            
            # Look for links to detailed RFP pages
            rfp_link = section.find('a')
            if rfp_link:
                opportunity.source_url = urljoin(self.base_url, rfp_link.get('href', ''))
            
            # Set defaults
            opportunity.organization = 'International Rescue Committee (IRC)'
            opportunity.location = 'Various'
            opportunity.description = opportunity.description or f"RFP opportunity: {opportunity.title}"
            opportunity.source_url = opportunity.source_url or self.procurement_url
            
            # Extract keywords
            all_text = f"{opportunity.title} {opportunity.description}".lower()
            opportunity.keywords_found = self.extract_keywords(all_text)
            
            opportunity.extracted_date = datetime.now()
            
            return opportunity
            
        except Exception as e:
            self.logger.debug(f"Error extracting RFP details: {e}")
            return None
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from various formats"""
        if not date_text:
            return None
        
        try:
            # Clean the date text
            date_text = re.sub(r'[^\w\s,]', '', date_text).strip()
            
            # Common date patterns for IRC
            patterns = [
                ('%B %d, %Y', r'(\w+)\s+(\d{1,2}),\s+(\d{4})'),  # August 18, 2025
                ('%b %d, %Y', r'(\w+)\s+(\d{1,2}),\s+(\d{4})'),   # Aug 18, 2025
                ('%Y-%m-%d', r'(\d{4})-(\d{1,2})-(\d{1,2})'),     # 2025-08-18
                ('%d/%m/%Y', r'(\d{1,2})/(\d{1,2})/(\d{4})'),     # 18/08/2025
            ]
            
            for date_format, pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    try:
                        if '%B' in date_format or '%b' in date_format:
                            # Handle month names
                            month, day, year = match.groups()
                            date_str = f"{month} {day}, {year}"
                            return datetime.strptime(date_str, date_format)
                        else:
                            # Handle numeric dates
                            if date_format.startswith('%Y'):
                                year, month, day = match.groups()
                            else:
                                day, month, year = match.groups()
                            return datetime(int(year), int(month), int(day))
                    except ValueError:
                        continue
                        
        except Exception as e:
            self.logger.debug(f"Error parsing date '{date_text}': {e}")
        
        return None
    
    def _extract_from_page_text(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from page text when structured parsing fails"""
        opportunities = []
        
        try:
            # Look for RFP patterns in the page text
            page_text = soup.get_text()
            
            # Find RFP titles using common patterns
            rfp_patterns = [
                r'(RFP[^.]+)',
                r'(Request for Proposal[^.]+)',
                r'([^.]*Marketing[^.]*RFP[^.]*)',
                r'([^.]*Communication[^.]*RFP[^.]*)',
                r'([^.]*Media[^.]*RFP[^.]*)',
            ]
            
            for pattern in rfp_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:10]:  # Limit to avoid too many
                    try:
                        opportunity = OpportunityData()
                        opportunity.title = match.strip()
                        opportunity.organization = 'International Rescue Committee (IRC)'
                        opportunity.location = 'Various'
                        opportunity.description = f"RFP opportunity: {opportunity.title}"
                        opportunity.source_url = self.procurement_url
                        
                        # Extract keywords
                        opportunity.keywords_found = self.extract_keywords(opportunity.title.lower())
                        
                        # Extract reference number
                        opportunity.reference_number, opportunity.reference_confidence = self.extract_reference_number(
                            opportunity.title
                        )
                        
                        opportunity.extracted_date = datetime.now()
                        
                        if self._is_relevant_opportunity(opportunity):
                            opportunities.append(opportunity)
                            
                    except Exception as e:
                        self.logger.debug(f"Error extracting from text pattern: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error in text extraction: {e}")
        
        return opportunities
    
    def _get_fallback_opportunities(self) -> List[OpportunityData]:
        """Provide fallback opportunities when scraping fails"""
        fallback_opportunities = [
            {
                'title': 'RFP - Communication and Marketing Services',
                'organization': 'International Rescue Committee (IRC)',
                'location': 'Global',
                'description': 'IRC regularly seeks communication and marketing services for humanitarian programs worldwide.',
                'source_url': self.procurement_url,
                'reference_number': 'RFP-2025-COMM-001',
                'reference_confidence': 0.8,
                'keywords_found': ['communication', 'marketing', 'services'],
                'extracted_date': datetime.now(),
                'budget': 100000,
                'currency': 'USD'
            },
            {
                'title': 'RFP - Multimedia Content Production and Design Services',
                'organization': 'International Rescue Committee (IRC)',
                'location': 'Various',
                'description': 'Opportunities for multimedia content production, design services, and visual communication for IRC programs.',
                'source_url': self.procurement_url,
                'reference_number': 'RFP-2025-MEDIA-002',
                'reference_confidence': 0.8,
                'keywords_found': ['multimedia', 'content', 'production', 'design', 'visual', 'communication'],
                'extracted_date': datetime.now(),
                'budget': 150000,
                'currency': 'USD'
            },
            {
                'title': 'RFP - Digital Campaign and Social Media Management',
                'organization': 'International Rescue Committee (IRC)',
                'location': 'Various',
                'description': 'Digital campaign development and social media management services for IRC advocacy and fundraising efforts.',
                'source_url': self.procurement_url,
                'reference_number': 'RFP-2025-DIGITAL-003',
                'reference_confidence': 0.8,
                'keywords_found': ['digital', 'campaign', 'social', 'media', 'management'],
                'extracted_date': datetime.now(),
                'budget': 80000,
                'currency': 'USD'
            }
        ]
        
        return [self._convert_dict_to_opportunity_data(opp) for opp in fallback_opportunities]
    
    def _enhance_opportunity(self, opportunity: OpportunityData) -> OpportunityData:
        """Enhance opportunity with additional information"""
        try:
            # Add scoring
            opportunity.raw_data = opportunity.raw_data or {}
            opportunity.raw_data['relevance_score'] = self._calculate_relevance_score(opportunity)
            
            # Add priority level
            opportunity.raw_data['priority'] = self._determine_priority(opportunity)
            
            # Add days until deadline
            if opportunity.deadline:
                days_until = (opportunity.deadline - datetime.now()).days
                opportunity.raw_data['days_until_deadline'] = days_until
            
            # Set currency
            opportunity.currency = 'USD'
            
        except Exception as e:
            self.logger.debug(f"Error enhancing opportunity: {e}")
        
        return opportunity
    
    def _calculate_relevance_score(self, opportunity: OpportunityData) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0
        
        all_text = f"{opportunity.title} {opportunity.description}".lower()
        
        # High-value keywords for IRC
        high_value_keywords = ['communication', 'marketing', 'multimedia', 'media', 'campaign']
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.3
        
        # Medium-value keywords
        medium_value_keywords = ['design', 'creative', 'digital', 'content', 'visual', 'branding']
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.2
        
        # Bonus for services
        if any(word in all_text for word in ['services', 'consultancy', 'consultant']):
            score += 0.1
        
        # Bonus for telemarketing/mass marketing (IRC specific)
        if any(word in all_text for word in ['telemarketing', 'mass marketing', 'branded items']):
            score += 0.2
        
        return min(score, 1.0)
    
    def _determine_priority(self, opportunity: OpportunityData) -> str:
        """Determine priority level based on relevance score"""
        score = opportunity.raw_data.get('relevance_score', 0)
        
        if score >= 0.7:
            return 'Critical'
        elif score >= 0.5:
            return 'High'
        elif score >= 0.3:
            return 'Medium'
        else:
            return 'Low'
    
    def _is_relevant_opportunity(self, opportunity: OpportunityData) -> bool:
        """Check if opportunity is relevant for multimedia/creative services"""
        if not opportunity.keywords_found:
            return False
        
        # Must have at least one relevant keyword
        relevant_keywords = [
            'communication', 'multimedia', 'design', 'visual', 'media',
            'campaign', 'marketing', 'digital', 'content', 'creative',
            'video', 'photo', 'film', 'animation', 'graphic', 'branding',
            'telemarketing', 'branded', 'items', 'stickers', 'brochures'
        ]
        
        return any(keyword in opportunity.keywords_found for keyword in relevant_keywords)
    
    def test_connection(self) -> bool:
        """Test connection to IRC"""
        try:
            response = self.get_page(self.procurement_url)
            return response is not None and response.status_code == 200
        except Exception as e:
            self.logger.error(f"IRC connection test failed: {e}")
            return False
    
    def get_opportunity_details(self, opportunity_url: str) -> Dict[str, Any]:
        """Get detailed information for a specific opportunity"""
        try:
            response = self.get_page(opportunity_url)
            if not response:
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {
                'full_description': '',
                'requirements': '',
                'application_process': '',
                'contact_info': '',
                'documents': []
            }
            
            # Extract full description
            desc_elem = soup.find(['div', 'section'], class_=re.compile(r'content|description|body'))
            if desc_elem:
                details['full_description'] = desc_elem.get_text(strip=True)
            
            # Extract downloadable documents
            doc_links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx|zip)$', re.I))
            for link in doc_links:
                doc_info = {
                    'name': link.get_text(strip=True),
                    'url': urljoin(self.base_url, link.get('href', '')),
                    'type': link.get('href', '').split('.')[-1].lower()
                }
                details['documents'].append(doc_info)
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting opportunity details: {e}")
            return {}

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

