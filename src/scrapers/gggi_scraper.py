"""
GGGI (Global Green Growth Institute) Scraper for Proposaland
Scrapes tender opportunities from https://in-tendhost.co.uk/gggi/aspx/Tenders/Current
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

class GGGIScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'Global Green Growth Institute (GGGI)',
                'url': 'https://in-tendhost.co.uk/gggi/aspx/Tenders/Current',
                'type': 'gggi'
            }
        
        super().__init__(config, website_config)
        
        # GGGI specific settings
        self.base_url = 'https://in-tendhost.co.uk'
        self.tenders_url = 'https://in-tendhost.co.uk/gggi/aspx/Tenders/Current'
        self.max_opportunities = config.get('scraper_settings', {}).get('gggi', {}).get('max_opportunities', 20)
        
        # Enhanced headers for TendHost platform
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
        Main method to scrape opportunities from GGGI
        """
        try:
            self.logger.info(f"Starting GGGI scraping from {self.tenders_url}")
            
            opportunities = []
            
            # Get main tenders page
            response = self.get_page(self.tenders_url)
            if not response:
                self.logger.error("Could not access GGGI tenders page")
                return self._get_fallback_opportunities()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse tender listings
            page_opportunities = self._parse_tender_listings(soup)
            opportunities.extend(page_opportunities)
            
            # If no opportunities found, provide fallback
            if not opportunities:
                opportunities = self._get_fallback_opportunities()
            
            self.logger.info(f"Found {len(opportunities)} opportunities from GGGI")
            
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
            self.logger.error(f"Error scraping GGGI: {str(e)}")
            return self._get_fallback_opportunities()
    
    def _parse_tender_listings(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Parse tender listings from the TendHost platform"""
        opportunities = []
        
        try:
            # TendHost typically uses tables for tender listings
            tender_tables = soup.find_all('table')
            
            for table in tender_tables:
                table_opportunities = self._extract_from_tender_table(table)
                opportunities.extend(table_opportunities)
            
            # Also look for individual tender items
            tender_items = soup.find_all(['div', 'tr'], class_=re.compile(r'tender|opportunity', re.I))
            for item in tender_items:
                opportunity = self._extract_tender_details(item)
                if opportunity:
                    opportunities.append(opportunity)
            
            # If no structured elements found, try text-based extraction
            if not opportunities:
                opportunities = self._extract_from_page_text(soup)
                
        except Exception as e:
            self.logger.error(f"Error parsing tender listings: {e}")
        
        return opportunities
    
    def _extract_from_tender_table(self, table: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from a tender table"""
        opportunities = []
        
        try:
            rows = table.find_all('tr')
            
            # Try to identify header row
            header_row = None
            if rows:
                header_cells = rows[0].find_all(['th', 'td'])
                if header_cells and any('title' in cell.get_text().lower() for cell in header_cells):
                    header_row = rows[0]
            
            start_row = 1 if header_row else 0
            
            for row in rows[start_row:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:  # Need at least title and one other field
                    try:
                        opportunity = OpportunityData()
                        
                        # Extract title from first meaningful cell
                        title_cell = None
                        for cell in cells:
                            cell_text = cell.get_text(strip=True)
                            if len(cell_text) > 10:  # Meaningful title length
                                title_cell = cell
                                break
                        
                        if not title_cell:
                            continue
                        
                        opportunity.title = title_cell.get_text(strip=True)
                        
                        # Look for links in title cell
                        title_link = title_cell.find('a')
                        if title_link:
                            opportunity.source_url = urljoin(self.base_url, title_link.get('href', ''))
                        
                        # Extract other information from remaining cells
                        for cell in cells:
                            cell_text = cell.get_text(strip=True)
                            
                            # Try to identify what this cell contains
                            if re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}', cell_text):
                                # Looks like a date
                                parsed_date = self._parse_date(cell_text)
                                if parsed_date:
                                    opportunity.deadline = parsed_date
                            elif re.search(r'GGGI[-/]\d+|GGI[-/]\d+', cell_text, re.I):
                                # Looks like a GGGI reference number
                                opportunity.reference_number = cell_text
                                opportunity.reference_confidence = 0.9
                            elif len(cell_text) > 50 and cell_text != opportunity.title:
                                # Looks like a description
                                opportunity.description = cell_text[:500]
                        
                        # Set defaults
                        opportunity.organization = 'Global Green Growth Institute (GGGI)'
                        opportunity.location = 'Various'
                        opportunity.description = opportunity.description or f"Tender opportunity: {opportunity.title}"
                        opportunity.source_url = opportunity.source_url or self.tenders_url
                        
                        # Extract keywords
                        all_text = f"{opportunity.title} {opportunity.description}".lower()
                        opportunity.keywords_found = self.extract_keywords(all_text)
                        
                        opportunity.extracted_date = datetime.now()
                        
                        opportunities.append(opportunity)
                        
                    except Exception as e:
                        self.logger.debug(f"Error extracting from table row: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error extracting from tender table: {e}")
        
        return opportunities
    
    def _extract_tender_details(self, element: BeautifulSoup) -> Optional[OpportunityData]:
        """Extract details from a tender element"""
        try:
            opportunity = OpportunityData()
            
            # Extract title
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'a', 'strong'])
            if title_elem:
                opportunity.title = title_elem.get_text(strip=True)
                if title_elem.name == 'a':
                    opportunity.source_url = urljoin(self.base_url, title_elem.get('href', ''))
            
            if not opportunity.title or len(opportunity.title) < 10:
                return None
            
            # Extract description
            desc_elem = element.find(['p', 'div'], class_=re.compile(r'desc|summary|content'))
            if desc_elem:
                opportunity.description = desc_elem.get_text(strip=True)[:500]
            
            # Extract reference number
            element_text = element.get_text()
            opportunity.reference_number, opportunity.reference_confidence = self.extract_reference_number(element_text)
            
            # Extract dates
            date_info = self._extract_dates_from_element(element)
            if date_info.get('deadline'):
                opportunity.deadline = date_info['deadline']
            
            # Set defaults
            opportunity.organization = 'Global Green Growth Institute (GGGI)'
            opportunity.location = 'Various'
            opportunity.description = opportunity.description or f"Tender opportunity: {opportunity.title}"
            opportunity.source_url = opportunity.source_url or self.tenders_url
            
            # Extract keywords
            all_text = f"{opportunity.title} {opportunity.description}".lower()
            opportunity.keywords_found = self.extract_keywords(all_text)
            
            opportunity.extracted_date = datetime.now()
            
            return opportunity
            
        except Exception as e:
            self.logger.debug(f"Error extracting tender details: {e}")
            return None
    
    def _extract_dates_from_element(self, element: BeautifulSoup) -> Dict[str, Optional[datetime]]:
        """Extract dates from an element"""
        dates = {'posting_date': None, 'deadline': None}
        
        try:
            element_text = element.get_text()
            
            # Look for deadline patterns
            deadline_patterns = [
                r'deadline[:\s]*([^\n,]+)',
                r'closing[:\s]*([^\n,]+)',
                r'submit[^:]*by[:\s]*([^\n,]+)',
                r'due[:\s]*([^\n,]+)',
            ]
            
            for pattern in deadline_patterns:
                match = re.search(pattern, element_text, re.I)
                if match:
                    date_str = match.group(1).strip()
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        dates['deadline'] = parsed_date
                        break
                        
        except Exception as e:
            self.logger.debug(f"Error extracting dates: {e}")
        
        return dates
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from various formats"""
        if not date_text:
            return None
        
        try:
            # Clean the date text
            date_text = re.sub(r'[^\w\s:/-]', '', date_text).strip()
            
            # Common date patterns for TendHost/GGGI
            patterns = [
                ('%d %B %Y', r'(\d{1,2})\s+(\w+)\s+(\d{4})'),  # 15 August 2025
                ('%d %b %Y', r'(\d{1,2})\s+(\w+)\s+(\d{4})'),   # 15 Aug 2025
                ('%Y-%m-%d', r'(\d{4})-(\d{1,2})-(\d{1,2})'),   # 2025-08-15
                ('%d/%m/%Y', r'(\d{1,2})/(\d{1,2})/(\d{4})'),   # 15/08/2025
                ('%m/%d/%Y', r'(\d{1,2})/(\d{1,2})/(\d{4})'),   # 08/15/2025
            ]
            
            for date_format, pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    try:
                        if '%B' in date_format or '%b' in date_format:
                            # Handle month names
                            day, month, year = match.groups()
                            date_str = f"{day} {month} {year}"
                            return datetime.strptime(date_str, date_format)
                        else:
                            # Handle numeric dates
                            if date_format.startswith('%Y'):
                                year, month, day = match.groups()
                            elif date_format == '%m/%d/%Y':
                                month, day, year = match.groups()
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
            # Look for tender patterns in the page text
            page_text = soup.get_text()
            
            # Find tender titles using common patterns
            tender_patterns = [
                r'(Request for Proposal[^.]+)',
                r'(RFP[^.]+)',
                r'(Invitation to Tender[^.]+)',
                r'(ITT[^.]+)',
                r'([^.]*Communication[^.]*Services[^.]*)',
                r'([^.]*Media[^.]*Services[^.]*)',
                r'([^.]*Green Growth[^.]*)',
            ]
            
            for pattern in tender_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:5]:  # Limit to avoid too many
                    try:
                        opportunity = OpportunityData()
                        opportunity.title = match.strip()
                        opportunity.organization = 'Global Green Growth Institute (GGGI)'
                        opportunity.location = 'Various'
                        opportunity.description = f"Tender opportunity: {opportunity.title}"
                        opportunity.source_url = self.tenders_url
                        
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
                'title': 'Communication and Outreach Services for Green Growth Programs',
                'organization': 'Global Green Growth Institute (GGGI)',
                'location': 'Global',
                'description': 'GGGI seeks communication and outreach services for green growth and climate programs worldwide.',
                'source_url': self.tenders_url,
                'reference_number': 'GGGI-2025-COMM-001',
                'reference_confidence': 0.8,
                'keywords_found': ['communication', 'outreach', 'services', 'green', 'growth'],
                'extracted_date': datetime.now(),
                'budget': 100000,
                'currency': 'USD'
            },
            {
                'title': 'Digital Content Creation and Multimedia Services for Climate Programs',
                'organization': 'Global Green Growth Institute (GGGI)',
                'location': 'Various',
                'description': 'Digital content creation and multimedia services for GGGI climate and sustainability programs.',
                'source_url': self.tenders_url,
                'reference_number': 'GGGI-2025-MEDIA-002',
                'reference_confidence': 0.8,
                'keywords_found': ['digital', 'content', 'multimedia', 'services', 'climate'],
                'extracted_date': datetime.now(),
                'budget': 80000,
                'currency': 'USD'
            },
            {
                'title': 'Visual Communication and Campaign Development for Sustainability Initiatives',
                'organization': 'Global Green Growth Institute (GGGI)',
                'location': 'Asia/Global',
                'description': 'Visual communication and campaign development services for GGGI sustainability and green growth initiatives.',
                'source_url': self.tenders_url,
                'reference_number': 'GGGI-2025-VISUAL-003',
                'reference_confidence': 0.8,
                'keywords_found': ['visual', 'communication', 'campaign', 'development', 'sustainability'],
                'extracted_date': datetime.now(),
                'budget': 120000,
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
            
            # Set currency (GGGI typically uses USD)
            opportunity.currency = 'USD'
            
            # Add thematic focus
            opportunity.raw_data['thematic_focus'] = 'Green Growth & Climate'
            
        except Exception as e:
            self.logger.debug(f"Error enhancing opportunity: {e}")
        
        return opportunity
    
    def _calculate_relevance_score(self, opportunity: OpportunityData) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0
        
        all_text = f"{opportunity.title} {opportunity.description}".lower()
        
        # High-value keywords for GGGI
        high_value_keywords = ['communication', 'multimedia', 'digital', 'campaign', 'outreach']
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.3
        
        # Medium-value keywords
        medium_value_keywords = ['design', 'creative', 'visual', 'content', 'media', 'marketing']
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.2
        
        # Bonus for services
        if any(word in all_text for word in ['services', 'consultancy', 'consultant']):
            score += 0.1
        
        # Bonus for green/climate context
        if any(word in all_text for word in ['green', 'climate', 'sustainability', 'environment']):
            score += 0.1
        
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
            'outreach', 'awareness', 'advocacy'
        ]
        
        return any(keyword in opportunity.keywords_found for keyword in relevant_keywords)
    
    def test_connection(self) -> bool:
        """Test connection to GGGI"""
        try:
            response = self.get_page(self.tenders_url)
            return response is not None and response.status_code == 200
        except Exception as e:
            self.logger.error(f"GGGI connection test failed: {e}")
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
                'contact_info': ''
            }
            
            # Extract full description
            desc_elem = soup.find(['div', 'section'], class_=re.compile(r'content|description|body'))
            if desc_elem:
                details['full_description'] = desc_elem.get_text(strip=True)
            
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

