"""
Save the Children Scraper for Proposaland
Scrapes tender opportunities from https://www.savethechildren.net/tenders
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

class SaveTheChildrenScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'Save the Children',
                'url': 'https://www.savethechildren.net/tenders',
                'type': 'savethechildren'
            }
        
        super().__init__(config, website_config)
        
        # Save the Children specific settings
        self.base_url = 'https://www.savethechildren.net'
        self.tenders_url = 'https://www.savethechildren.net/tenders'
        self.max_opportunities = config.get('scraper_settings', {}).get('savethechildren', {}).get('max_opportunities', 30)
        
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
        Main method to scrape opportunities from Save the Children
        """
        try:
            self.logger.info(f"Starting Save the Children scraping from {self.tenders_url}")
            
            opportunities = []
            
            # Get initial page
            response = self.get_page(self.tenders_url)
            if not response:
                self.logger.error("Could not access Save the Children tenders page")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse tender listings
            page_opportunities = self._parse_tender_listings(soup)
            opportunities.extend(page_opportunities)
            
            # Handle "Load More" functionality if present
            load_more_opportunities = self._handle_load_more(soup)
            opportunities.extend(load_more_opportunities)
            
            self.logger.info(f"Found {len(opportunities)} opportunities from Save the Children")
            
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
            self.logger.error(f"Error scraping Save the Children: {str(e)}")
            return []
    
    def _parse_tender_listings(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Parse tender listings from the main page"""
        opportunities = []
        
        try:
            # Look for tender sections/containers
            tender_sections = soup.find_all(['div', 'section', 'article'], class_=re.compile(r'tender|invitation|itt'))
            
            if not tender_sections:
                # Try alternative selectors
                tender_sections = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'tender|invitation|itt|expression', re.I))
                # Get parent containers
                tender_sections = [h.find_parent(['div', 'section', 'article']) for h in tender_sections if h.find_parent(['div', 'section', 'article'])]
            
            for section in tender_sections:
                try:
                    opportunity = self._extract_tender_details(section)
                    if opportunity:
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    self.logger.debug(f"Error parsing tender section: {e}")
                    continue
            
            # If no structured sections found, try text-based extraction
            if not opportunities:
                opportunities = self._extract_from_page_text(soup)
                
        except Exception as e:
            self.logger.error(f"Error parsing tender listings: {e}")
        
        return opportunities
    
    def _extract_tender_details(self, section: BeautifulSoup) -> Optional[OpportunityData]:
        """Extract details from a tender section"""
        try:
            opportunity = OpportunityData()
            
            # Extract title
            title_elem = section.find(['h1', 'h2', 'h3', 'h4', 'h5'])
            if title_elem:
                opportunity.title = title_elem.get_text(strip=True)
            
            if not opportunity.title:
                return None
            
            # Extract description
            desc_elem = section.find(['p', 'div'], class_=re.compile(r'desc|summary|content'))
            if not desc_elem:
                # Look for text content in the section
                desc_elem = section.find('p')
            
            if desc_elem:
                opportunity.description = desc_elem.get_text(strip=True)[:500]
            
            # Extract dates
            date_info = self._extract_dates_from_section(section)
            if date_info.get('deadline'):
                opportunity.deadline = date_info['deadline']
            
            # Extract location
            location_text = section.get_text()
            location_match = re.search(r'(country|location|destination)[:\s]*([^\n,]+)', location_text, re.I)
            if location_match:
                opportunity.location = location_match.group(2).strip()
            
            # Extract reference number
            ref_text = section.get_text()
            opportunity.reference_number, opportunity.reference_confidence = self.extract_reference_number(ref_text)
            
            # Look for "Read More" links
            read_more_link = section.find('a', string=re.compile(r'read more|more info|details', re.I))
            if read_more_link:
                opportunity.source_url = urljoin(self.base_url, read_more_link.get('href', ''))
            
            # Set defaults
            opportunity.organization = 'Save the Children'
            opportunity.location = opportunity.location or 'Various'
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
    
    def _extract_dates_from_section(self, section: BeautifulSoup) -> Dict[str, Optional[datetime]]:
        """Extract posting and deadline dates from a section"""
        dates = {'posting_date': None, 'deadline': None}
        
        try:
            section_text = section.get_text()
            
            # Look for deadline patterns
            deadline_patterns = [
                r'deadline[:\s]*([^\n,]+)',
                r'closing[:\s]*([^\n,]+)',
                r'submit[^:]*by[:\s]*([^\n,]+)',
                r'responses[^:]*by[:\s]*([^\n,]+)',
                r'no later than[:\s]*([^\n,]+)',
            ]
            
            for pattern in deadline_patterns:
                match = re.search(pattern, section_text, re.I)
                if match:
                    date_str = match.group(1).strip()
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        dates['deadline'] = parsed_date
                        break
            
            # Look for posting date patterns
            posting_patterns = [
                r'(\d{1,2}\s+\w+\s+\d{4})',  # 20 Aug 2025
                r'(\d{4}-\d{1,2}-\d{1,2})',  # 2025-08-20
            ]
            
            for pattern in posting_patterns:
                matches = re.findall(pattern, section_text)
                if matches:
                    for date_str in matches:
                        parsed_date = self._parse_date(date_str)
                        if parsed_date and not dates['posting_date']:
                            dates['posting_date'] = parsed_date
                            break
                    if dates['posting_date']:
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
            
            # Common date patterns
            patterns = [
                ('%d %B %Y', r'(\d{1,2})\s+(\w+)\s+(\d{4})'),  # 20 August 2025
                ('%d %b %Y', r'(\d{1,2})\s+(\w+)\s+(\d{4})'),   # 20 Aug 2025
                ('%Y-%m-%d', r'(\d{4})-(\d{1,2})-(\d{1,2})'),   # 2025-08-20
                ('%d/%m/%Y', r'(\d{1,2})/(\d{1,2})/(\d{4})'),   # 20/08/2025
                ('%d-%m-%Y', r'(\d{1,2})-(\d{1,2})-(\d{4})'),   # 20-08-2025
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
                            else:
                                day, month, year = match.groups()
                            return datetime(int(year), int(month), int(day))
                    except ValueError:
                        continue
            
            # Try to extract time information if present
            time_match = re.search(r'(\d{1,2}):(\d{2})', date_text)
            if time_match and dates:
                hour, minute = map(int, time_match.groups())
                # Add time to the last successfully parsed date
                return dates.replace(hour=hour, minute=minute)
                
        except Exception as e:
            self.logger.debug(f"Error parsing date '{date_text}': {e}")
        
        return None
    
    def _handle_load_more(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Handle dynamic loading of more tenders"""
        opportunities = []
        
        try:
            # Look for "Load More" button or similar
            load_more_btn = soup.find(['button', 'a'], string=re.compile(r'load more|show more|more', re.I))
            
            if load_more_btn:
                # This would require JavaScript execution for dynamic loading
                # For now, we'll skip this and rely on the initial page content
                self.logger.info("Load More functionality detected but not implemented")
                
        except Exception as e:
            self.logger.debug(f"Error handling load more: {e}")
        
        return opportunities
    
    def _extract_from_page_text(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from page text when structured parsing fails"""
        opportunities = []
        
        try:
            # Look for tender-related text patterns
            page_text = soup.get_text()
            
            # Find tender titles using common patterns
            tender_patterns = [
                r'(Expression of Interest[^.]+)',
                r'(Invitation to Tender[^.]+)',
                r'(ITT[^.]+)',
                r'(Request for Proposal[^.]+)',
                r'(RFP[^.]+)',
            ]
            
            for pattern in tender_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:5]:  # Limit to avoid too many
                    try:
                        opportunity = OpportunityData()
                        opportunity.title = match.strip()
                        opportunity.organization = 'Save the Children'
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
            
            # Add currency (Save the Children typically uses USD/GBP)
            opportunity.currency = 'USD'
            
        except Exception as e:
            self.logger.debug(f"Error enhancing opportunity: {e}")
        
        return opportunity
    
    def _calculate_relevance_score(self, opportunity: OpportunityData) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0
        
        all_text = f"{opportunity.title} {opportunity.description}".lower()
        
        # High-value keywords
        high_value_keywords = ['communication', 'multimedia', 'design', 'creative', 'campaign']
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.3
        
        # Medium-value keywords
        medium_value_keywords = ['media', 'digital', 'content', 'visual', 'marketing']
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.2
        
        # Bonus for consultancy/services
        if any(word in all_text for word in ['consultancy', 'consultant', 'services', 'technical assistance']):
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
            'video', 'photo', 'film', 'animation', 'graphic', 'branding'
        ]
        
        return any(keyword in opportunity.keywords_found for keyword in relevant_keywords)
    
    def test_connection(self) -> bool:
        """Test connection to Save the Children"""
        try:
            response = self.get_page(self.tenders_url)
            return response is not None and response.status_code == 200
        except Exception as e:
            self.logger.error(f"Save the Children connection test failed: {e}")
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

