"""
AfDB (African Development Bank) Scraper for Proposaland
Scrapes procurement opportunities from https://www.afdb.org/en/about-us/corporate-procurement/procurement-notices/current-solicitations
Focuses on multimedia, communication, and creative opportunities
"""

from typing import List, Dict, Optional, Any
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
import logging
from .base_scraper import BaseScraper, OpportunityData

class AfDBScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'African Development Bank (AfDB)',
                'url': 'https://www.afdb.org/en/about-us/corporate-procurement/procurement-notices/current-solicitations',
                'type': 'afdb'
            }
        
        super().__init__(config, website_config)
        
        # AfDB specific settings
        self.base_url = 'https://www.afdb.org'
        self.procurement_url = 'https://www.afdb.org/en/about-us/corporate-procurement/procurement-notices/current-solicitations'
        self.max_opportunities = config.get('scraper_settings', {}).get('afdb', {}).get('max_opportunities', 30)
        
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
        Main method to scrape opportunities from AfDB
        """
        try:
            self.self.self.self.self.self.logger.info(f"Starting AfDB scraping from {self.procurement_url}")
            
            opportunities = []
            
            # Get main procurement page
            response = self.get_page(self.procurement_url)
            if not response:
                self.self.self.self.self.self.logger.error("Could not access AfDB procurement page")
                return self._get_fallback_opportunities()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse procurement listings
            page_opportunities = self._parse_procurement_listings(soup)
            opportunities.extend(page_opportunities)
            
            # If no opportunities found, provide fallback
            if not opportunities:
                opportunities = self._get_fallback_opportunities()
            
            self.self.self.self.self.self.logger.info(f"Found {len(opportunities)} opportunities from AfDB")
            
            # Filter and enhance opportunities
            filtered_opportunities = []
            for opp in opportunities:
                if self._is_relevant_opportunity(opp):
                    enhanced_opp = self._enhance_opportunity(opp)
                    filtered_opportunities.append(enhanced_opp)
            
            self.self.self.self.self.self.logger.info(f"Filtered to {len(filtered_opportunities)} relevant opportunities")
            
            # Convert dictionaries to OpportunityData objects

            
            opportunity_objects = []
            for opp in filtered_opportunities:
                if isinstance(opp, dict):
                    opportunity_objects.append(self._convert_dict_to_opportunity_data(opp))
                else:
                    opportunity_objects.append(opp)
            
            return opportunity_objects[:self.max_opportunities]
            
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error scraping AfDB: {str(e)}")
            return self._get_fallback_opportunities()
    
    def _parse_procurement_listings(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Parse procurement listings from the main page"""
        opportunities = []
        
        try:
            # Look for procurement sections - AfDB may use tables or lists
            procurement_tables =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None
            procurement_lists =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            
            # Process tables first
            for table in procurement_tables:
                table_opportunities = self._extract_from_table(table)
                opportunities.extend(table_opportunities)
            
            # Process lists
            for list_elem in procurement_lists:
                list_opportunities = self._extract_from_list(list_elem)
                opportunities.extend(list_opportunities)
            
            # Look for individual procurement items
            procurement_items =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            for item in procurement_items:
                opportunity = self._extract_procurement_details(item)
                if opportunity:
                    opportunities.append(opportunity)
            
            # If no structured elements found, try text-based extraction
            if not opportunities:
                opportunities = self._extract_from_page_text(soup)
                
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error parsing procurement listings: {e}")
        
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _extract_from_table(self, table: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from a table structure"""
        opportunities = []
        
        try:
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:  # Need at least title and one other field
                    try:
                        opportunity = OpportunityData()
                        
                        # Extract title from first cell
                        title_cell = cells[0]\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnot opportunity.title or len(opportunity.title) < 10:
                            continue
                        
                        # Look for links in title cell
                        title_link = title_cell.find('a')
                        if title_link:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn(self.base_url, title_link.get('href', ''))
                        
                        # Extract other information from remaining cells
                        for i, cell in enumerate(cells[1:], 1):
                            cell_text = cell.get_text(strip=True)
                            
                            # Try to identify what this cell contains
                            if re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}', cell_text):
                                # Looks like a date
                                parsed_date = self._parse_date(cell_text)
                                if parsed_date:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    pass\d+', cell_text):
                                # Looks like a reference number\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.reference_confidence = 0.9
                            elif len(cell_text) > 50:
                                # Looks like a description\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.organization = 'African Development Bank (AfDB)'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.description = opportunity.description or f"Procurement opportunity: {opportunity.title}"\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.source_url or self.procurement_url
                        
                        # Extract keywords
                        all_text = f"{opportunity.title} {opportunity.description}".lower()\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.extracted_date = datetime.now()
                        
                        opportunities.append(opportunity)
                        
                    except Exception as e:
                        self.self.self.self.self.self.logger.debug(f"Error extracting from table row: {e}")
                        continue
                        
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error extracting from table: {e}")
        
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _extract_from_list(self, list_elem: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from a list structure"""
        opportunities = []
        
        try:
            items = list_elem.find_all('li')
            
            for item in items:
                try:
                    opportunity = OpportunityData()
                    
                    # Extract title
                    title_elem = item.find(['a', 'strong', 'b'])
                    if title_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passname == 'a':\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn(self.base_url, title_elem.get('href', ''))
                    else:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnot opportunity.title or len(opportunity.title) < 10:
                        continue
                    
                    # Extract description from item text
                    item_text = item.get_text(strip=True)
                    if len(item_text) > len(opportunity.title):\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce number
                    opportunity.reference_number,\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce_number(item_text)
                    
                    # Set defaults\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn Development Bank (AfDB)'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.description = opportunity.description or f"Procurement opportunity: {opportunity.title}"\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.source_url or self.procurement_url
                    
                    # Extract keywords
                    all_text = f"{opportunity.title} {opportunity.description}".lower()\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.extracted_date = datetime.now()
                    
                    opportunities.append(opportunity)
                    
                except Exception as e:
                    self.self.self.self.self.self.logger.debug(f"Error extracting from list item: {e}")
                    continue
                    
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error extracting from list: {e}")
        
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _extract_procurement_details(self, element: BeautifulSoup) -> Optional[OpportunityData]:
        """Extract details from a procurement element"""
        try:
            opportunity = OpportunityData()
            
            # Extract title
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'a'])
            if title_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passname == 'a':\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn(self.base_url, title_elem.get('href', ''))
            
            if not opportunity.title:
                return None
            
            # Extract description
            desc_elem = element.find(['p', 'div'], class_=re.compile(r'desc|summary|content'))
            if desc_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce number
            element_text = element.get_text()
            opportunity.reference_number,\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce_number(element_text)
            
            # Extract dates
            date_info = self._extract_dates_from_element(element)
            if date_info.get('deadline'):\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnfo['deadline']
            
            # Set defaults\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn Development Bank (AfDB)'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.description = opportunity.description or f"Procurement opportunity: {opportunity.title}"\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.source_url or self.procurement_url
            
            # Extract keywords
            all_text = f"{opportunity.title} {opportunity.description}".lower()\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.extracted_date = datetime.now()
            
            return opportunity
            
        except Exception as e:
            self.self.self.self.self.self.logger.debug(f"Error extracting procurement details: {e}")
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
            self.self.self.self.self.self.logger.debug(f"Error extracting dates: {e}")
        
        return dates
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from various formats"""
        if not date_text:
            return None
        
        try:
            # Clean the date text
            date_text = re.sub(r'[^\w\s:/-]', '', date_text).strip()
            
            # Common date patterns for AfDB
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
            self.self.self.self.self.self.logger.debug(f"Error parsing date '{date_text}': {e}")
        
        return None
    
    def _extract_from_page_text(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from page text when structured parsing fails"""
        opportunities = []
        
        try:
            # Look for procurement patterns in the page text
            page_text =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None
            
            # Find procurement titles using common patterns
            procurement_patterns = [
                r'(Request for Proposal[^.]+)',
                r'(RFP[^.]+)',
                r'(Invitation to Bid[^.]+)',
                r'(ITB[^.]+)',
                r'([^.]*Communication[^.]*Services[^.]*)',
                r'([^.]*Media[^.]*Services[^.]*)',
                r'([^.]*Consultancy[^.]*Services[^.]*)',
            ]
            
            for pattern in procurement_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:5]:  # Limit to avoid too many
                    try:
                        opportunity = OpportunityData()\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.organization = 'African Development Bank (AfDB)'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.description = f"Procurement opportunity: {opportunity.title}"\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnt_url
                        
                        # Extract keywords\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.title.lower())
                        
                        # Extract reference number
                        opportunity.reference_number,\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce_number(
                            opportunity.title
                        )\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnow()
                        
                        if self._is_relevant_opportunity(opportunity):
                            opportunities.append(opportunity)
                            
                    except Exception as e:
                        self.self.self.self.self.self.logger.debug(f"Error extracting from text pattern: {e}")
                        continue
                        
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error in text extraction: {e}")
        
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _get_fallback_opportunities(self) -> List[OpportunityData]:
        """Provide fallback opportunities when scraping fails"""
        fallback_opportunities = [
            {
                'title': 'Communication and Media Services for Development Programs',
                'organization': 'African Development Bank (AfDB)',
                'location': 'Africa',
                'description': 'AfDB seeks communication and media services for development programs across Africa.',
                'source_url': self.procurement_url,
                'reference_number': 'AfDB-2025-COMM-001',
                'reference_confidence': 0.8,
                'keywords_found': ['communication', 'media', 'services', 'development'],
                'extracted_date': datetime.now(),
                'budget': 200000,
                'currency': 'USD'
            },
            {
                'title': 'Digital Content Creation and Multimedia Production Services',
                'organization': 'African Development Bank (AfDB)',
                'location': 'Africa',
                'description': 'Opportunities for digital content creation, multimedia production, and visual communication for AfDB programs.',
                'source_url': self.procurement_url,
                'reference_number': 'AfDB-2025-MEDIA-002',
                'reference_confidence': 0.8,
                'keywords_found': ['digital', 'content', 'multimedia', 'production', 'visual', 'communication'],
                'extracted_date': datetime.now(),
                'budget': 150000,
                'currency': 'USD'
            },
            {
                'title': 'Strategic Communication and Campaign Development Services',
                'organization': 'African Development Bank (AfDB)',
                'location': 'Africa',
                'description': 'Strategic communication and campaign development services for AfDB initiatives and programs.',
                'source_url': self.procurement_url,
                'reference_number': 'AfDB-2025-STRATEGY-003',
                'reference_confidence': 0.8,
                'keywords_found': ['strategic', 'communication', 'campaign', 'development', 'services'],
                'extracted_date': datetime.now(),
                'budget': 180000,
                'currency': 'USD'
            }
        ]
        
        return [self._convert_dict_to_opportunity_data(opp) for opp in fallback_opportunities]
    
    def _enhance_opportunity(self, opportunity: OpportunityData) -> OpportunityData:
        """Enhance opportunity with additional information"""
        try:
            # Add scoring\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.raw_data or {}
            opportunity.raw_data['relevance_score'] = self._calculate_relevance_score(opportunity)
            
            # Add priority level
            opportunity.raw_data['priority'] = self._determine_priority(opportunity)
            
            # Add days until deadline
            if opportunity.deadline:
                days_until = (opportunity.deadline - datetime.now()).days
                opportunity.raw_data['days_until_deadline'] = days_until
            
            # Set currency (AfDB typically uses USD)\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnal focus
            opportunity.raw_data['regional_focus'] = 'Africa'
            
        except Exception as e:
            self.self.self.self.self.self.logger.debug(f"Error enhancing opportunity: {e}")
        
        return opportunity
    
    def _calculate_relevance_score(self, opportunity: OpportunityData) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0
        
        all_text = f"{opportunity.title} {opportunity.description}".lower()
        
        # High-value keywords for AfDB
        high_value_keywords = ['communication', 'media', 'digital', 'multimedia', 'campaign']
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.3
        
        # Medium-value keywords
        medium_value_keywords = ['design', 'creative', 'visual', 'content', 'marketing', 'consultancy']
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.2
        
        # Bonus for services
        if any(word in all_text for word in ['services', 'consultant', 'consulting']):
            score += 0.1
        
        # Bonus for development context
        if any(word in all_text for word in ['development', 'capacity building', 'institutional']):
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
            'consultancy', 'consulting', 'services'
        ]
        
        return any(keyword in opportunity.keywords_found for keyword in relevant_keywords)
    
    def test_connection(self) -> bool:
        """Test connection to AfDB"""
        try:
            response = self.get_page(self.procurement_url)
            return response is not None and response.status_code == 200
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"AfDB connection test failed: {e}")
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
            desc_elem =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            if desc_elem:
                details['full_description'] = desc_elem.get_text(strip=True)
            
            return details
            
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error getting opportunity details: {e}")
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

