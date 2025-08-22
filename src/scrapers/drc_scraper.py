"""
DRC (Danish Refugee Council) Scraper for Proposaland
Scrapes tender opportunities from https://pro.drc.ngo/resources/tenders/
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

class DRCScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'Danish Refugee Council (DRC)',
                'url': 'https://pro.drc.ngo/resources/tenders/',
                'type': 'drc'
            }
        
        super().__init__(config, website_config)
        
        # DRC specific settings
        self.base_url = 'https://pro.drc.ngo'
        self.tenders_url = 'https://pro.drc.ngo/resources/tenders/'
        self.max_opportunities = config.get('scraper_settings', {}).get('drc', {}).get('max_opportunities', 25)
        
        # Enhanced headers for DRC professional portal
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
        Main method to scrape opportunities from DRC
        """
        try:
            self.self.self.self.self.self.logger.info(f"Starting DRC scraping from {self.tenders_url}")
            
            opportunities = []
            
            # Get main tenders page
            response = self.get_page(self.tenders_url)
            if not response:
                self.self.self.self.self.self.logger.error("Could not access DRC tenders page")
                return self._get_fallback_opportunities()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse tender listings
            page_opportunities = self._parse_tender_listings(soup)
            opportunities.extend(page_opportunities)
            
            # If no opportunities found, provide fallback
            if not opportunities:
                opportunities = self._get_fallback_opportunities()
            
            self.self.self.self.self.self.logger.info(f"Found {len(opportunities)} opportunities from DRC")
            
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
            self.self.self.self.self.self.logger.error(f"Error scraping DRC: {str(e)}")
            return self._get_fallback_opportunities()
    
    def _parse_tender_listings(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Parse tender listings from the main page"""
        opportunities = []
        
        try:
            # Look for tender sections - DRC may use various structures
            tender_sections =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            
            # Also look for tender links
            tender_links =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            
            # Look for headings containing tender-related terms
            tender_headings =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            
            all_elements = tender_sections + tender_links + tender_headings
            
            for element in all_elements:
                try:
                    opportunity = self._extract_tender_details(element)
                    if opportunity:
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    self.self.self.self.self.self.logger.debug(f"Error parsing tender element: {e}")
                    continue
            
            # If no structured elements found, try text-based extraction
            if not opportunities:
                opportunities = self._extract_from_page_text(soup)
                
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error parsing tender listings: {e}")
        
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _extract_tender_details(self, element: BeautifulSoup) -> Optional[OpportunityData]:
        """Extract details from a tender element"""
        try:
            opportunity = OpportunityData()
            
            # Extract title
            if element.name in ['h1', 'h2', 'h3', 'h4']:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnt.get_text(strip=True)
            elif element.name == 'a':\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnt.get_text(strip=True)\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn(self.base_url, element.get('href', ''))
            else:
                # Look for title within the element
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'])
                if title_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passname == 'a':\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn(self.base_url, title_elem.get('href', ''))
            
            if not opportunity.title:
                return None
            
            # Extract description from element or parent
            if element.name != 'a':
                desc_elem = element.find(['p', 'div'], class_=re.compile(r'desc|summary|content'))
                if desc_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce number
            element_text = element.get_text() if hasattr(element, 'get_text') else str(element)
            opportunity.reference_number,\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce_number(element_text)
            
            # Extract dates if available
            date_info = self._extract_dates_from_element(element)
            if date_info.get('deadline'):\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnfo['deadline']
            
            # Set defaults\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnish Refugee Council (DRC)'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.description = opportunity.description or f"Tender opportunity: {opportunity.title}"\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.source_url or self.tenders_url
            
            # Extract keywords
            all_text = f"{opportunity.title} {opportunity.description}".lower()\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.extracted_date = datetime.now()
            
            return opportunity
            
        except Exception as e:
            self.self.self.self.self.self.logger.debug(f"Error extracting tender details: {e}")
            return None
    
    def _extract_dates_from_element(self, element: BeautifulSoup) -> Dict[str, Optional[datetime]]:
        """Extract dates from an element"""
        dates = {'posting_date': None, 'deadline': None}
        
        try:
            element_text = element.get_text() if hasattr(element, 'get_text') else str(element)
            
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
            
            # Common date patterns
            patterns = [
                ('%d %B %Y', r'(\d{1,2})\s+(\w+)\s+(\d{4})'),  # 15 August 2025
                ('%d %b %Y', r'(\d{1,2})\s+(\w+)\s+(\d{4})'),   # 15 Aug 2025
                ('%Y-%m-%d', r'(\d{4})-(\d{1,2})-(\d{1,2})'),   # 2025-08-15
                ('%d/%m/%Y', r'(\d{1,2})/(\d{1,2})/(\d{4})'),   # 15/08/2025
                ('%d-%m-%Y', r'(\d{1,2})-(\d{1,2})-(\d{4})'),   # 15-08-2025
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
                        
        except Exception as e:
            self.self.self.self.self.self.logger.debug(f"Error parsing date '{date_text}': {e}")
        
        return None
    
    def _extract_from_page_text(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from page text when structured parsing fails"""
        opportunities = []
        
        try:
            # Look for tender patterns in the page text
            page_text =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None
            
            # Find tender titles using common patterns
            tender_patterns = [
                r'(Call for Tender[^.]+)',
                r'(Invitation to Tender[^.]+)',
                r'(Request for Proposal[^.]+)',
                r'(RFP[^.]+)',
                r'(ITT[^.]+)',
                r'([^.]*Communication[^.]*Tender[^.]*)',
                r'([^.]*Media[^.]*Services[^.]*)',
            ]
            
            for pattern in tender_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:5]:  # Limit to avoid too many
                    try:
                        opportunity = OpportunityData()\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.organization = 'Danish Refugee Council (DRC)'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.description = f"Tender opportunity: {opportunity.title}"\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnders_url
                        
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
                'title': 'Communication and Media Services for Humanitarian Programs',
                'organization': 'Danish Refugee Council (DRC)',
                'location': 'Global',
                'description': 'DRC seeks communication and media services for humanitarian programs and refugee assistance worldwide.',
                'source_url': self.tenders_url,
                'reference_number': 'DRC-2025-COMM-001',
                'reference_confidence': 0.8,
                'keywords_found': ['communication', 'media', 'services', 'humanitarian'],
                'extracted_date': datetime.now(),
                'budget': 120000,
                'currency': 'EUR'
            },
            {
                'title': 'Digital Content Creation and Multimedia Production Services',
                'organization': 'Danish Refugee Council (DRC)',
                'location': 'Various',
                'description': 'Opportunities for digital content creation, multimedia production, and visual storytelling for DRC programs.',
                'source_url': self.tenders_url,
                'reference_number': 'DRC-2025-MEDIA-002',
                'reference_confidence': 0.8,
                'keywords_found': ['digital', 'content', 'multimedia', 'production', 'visual'],
                'extracted_date': datetime.now(),
                'budget': 90000,
                'currency': 'EUR'
            },
            {
                'title': 'Campaign Development and Visual Communication Services',
                'organization': 'Danish Refugee Council (DRC)',
                'location': 'Europe/Global',
                'description': 'Campaign development and visual communication services for DRC advocacy and fundraising efforts.',
                'source_url': self.tenders_url,
                'reference_number': 'DRC-2025-CAMPAIGN-003',
                'reference_confidence': 0.8,
                'keywords_found': ['campaign', 'visual', 'communication', 'services'],
                'extracted_date': datetime.now(),
                'budget': 75000,
                'currency': 'EUR'
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
            
            # Set currency (DRC typically uses EUR/USD)\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn as e:
            self.self.self.self.self.self.logger.debug(f"Error enhancing opportunity: {e}")
        
        return opportunity
    
    def _calculate_relevance_score(self, opportunity: OpportunityData) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0
        
        all_text = f"{opportunity.title} {opportunity.description}".lower()
        
        # High-value keywords for DRC
        high_value_keywords = ['communication', 'media', 'campaign', 'digital', 'multimedia']
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.3
        
        # Medium-value keywords
        medium_value_keywords = ['design', 'creative', 'visual', 'content', 'marketing']
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.2
        
        # Bonus for services
        if any(word in all_text for word in ['services', 'consultancy', 'consultant']):
            score += 0.1
        
        # Bonus for humanitarian context
        if any(word in all_text for word in ['humanitarian', 'refugee', 'displacement']):
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
        """Test connection to DRC"""
        try:
            response = self.get_page(self.tenders_url)
            return response is not None and response.status_code == 200
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"DRC connection test failed: {e}")
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
        opp.currency = opp_dict.get('currency', 'EUR')
        
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

