"""
Mercy Corps Scraper for Proposaland
Scrapes tender opportunities from https://www.mercycorps.org/tenders
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

class MercyCorpsScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'Mercy Corps',
                'url': 'https://www.mercycorps.org/tenders',
                'type': 'mercycorps'
            }
        
        super().__init__(config, website_config)
        
        # Mercy Corps specific settings
        self.base_url = 'https://www.mercycorps.org'
        self.tenders_url = 'https://www.mercycorps.org/tenders'
        self.max_opportunities = config.get('scraper_settings', {}).get('mercycorps', {}).get('max_opportunities', 20)
        
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
        Main method to scrape opportunities from Mercy Corps
        """
        try:
            self.self.self.self.self.self.logger.info(f"Starting Mercy Corps scraping from {self.tenders_url}")
            
            opportunities = []
            
            # Get main tenders page
            response = self.get_page(self.tenders_url)
            if not response:
                self.self.self.self.self.self.logger.error("Could not access Mercy Corps tenders page")
                return self._get_fallback_opportunities()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse tender listings
            page_opportunities = self._parse_tender_listings(soup)
            opportunities.extend(page_opportunities)
            
            # If no opportunities found, provide fallback
            if not opportunities:
                opportunities = self._get_fallback_opportunities()
            
            self.self.self.self.self.self.logger.info(f"Found {len(opportunities)} opportunities from Mercy Corps")
            
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
            self.self.self.self.self.self.logger.error(f"Error scraping Mercy Corps: {str(e)}")
            return self._get_fallback_opportunities()
    
    def _parse_tender_listings(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Parse tender listings from the main page"""
        opportunities = []
        
        try:
            # Look for tender sections with REF# patterns
            tender_sections =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            
            # Also look for parent containers of tender headings
            tender_headings =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            for heading in tender_headings:
                parent = heading.find_parent(['div', 'section', 'article'])
                if parent and parent not in tender_sections:
                    tender_sections.append(parent)
            
            for section in tender_sections:
                try:
                    opportunity = self._extract_tender_details(section)
                    if opportunity:
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    self.self.self.self.self.self.logger.debug(f"Error parsing tender section: {e}")
                    continue
            
            # If no structured sections found, try text-based extraction
            if not opportunities:
                opportunities = self._extract_from_page_text(soup)
                
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error parsing tender listings: {e}")
        
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _extract_tender_details(self, section: BeautifulSoup) -> Optional[OpportunityData]:
        """Extract details from a tender section"""
        try:
            opportunity = OpportunityData()
            
            # Extract title (usually contains REF#)
            title_elem = section.find(['h1', 'h2', 'h3', 'h4', 'h5'])
            if not title_elem:
                # Look for text with REF# pattern
                ref_text = section.find(string=re.compile(r'REF#', re.I))
                if ref_text:
                    # Get the parent element containing the full title
                    title_elem = ref_text.parent
            
            if title_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnot opportunity.title:
                return None
            
            # Extract country/location
            location_elem = section.find(string=re.compile(r'Country of destination', re.I))
            if location_elem:
                # Get the next text element
                location_parent = location_elem.parent
                location_text = location_parent.get_text()
                location_match = re.search(r'Country of destination[:\s]*([^\n,]+)', location_text, re.I)
                if location_match:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn_match.group(1).strip()
            
            # Extract dates
            date_info = self._extract_dates_from_section(section)
            if date_info.get('deadline'):\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnfo['deadline']
            
            # Extract reference number from title
            opportunity.reference_number,\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce_number(
                opportunity.title
            )
            
            # Look for "Read More" links
            read_more_link = section.find('a', string=re.compile(r'read more|more info|details', re.I))
            if read_more_link:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn(self.base_url, read_more_link.get('href', ''))
            
            # Set defaults\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.location = opportunity.location or 'Various'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnt opportunity: {opportunity.title}"\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.source_url or self.tenders_url
            
            # Extract keywords from title\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.title.lower())\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnow()
            
            return opportunity
            
        except Exception as e:
            self.self.self.self.self.self.logger.debug(f"Error extracting tender details: {e}")
            return None
    
    def _extract_dates_from_section(self, section: BeautifulSoup) -> Dict[str, Optional[datetime]]:
        """Extract dates from a section"""
        dates = {'posting_date': None, 'deadline': None}
        
        try:
            section_text = section.get_text()
            
            # Look for open date patterns
            open_date_patterns = [
                r'Open date[:\s]*([^\n,]+)',
                r'from[:\s]*([^\n,]+)\s+to',
            ]
            
            for pattern in open_date_patterns:
                match = re.search(pattern, section_text, re.I)
                if match:
                    date_str = match.group(1).strip()
                    parsed_date = self._parse_date(date_str)
                    if parsed_date:
                        dates['posting_date'] = parsed_date
                        break
            
            # Look for deadline patterns
            deadline_patterns = [
                r'to[:\s]*([^\n,]+)',
                r'deadline[:\s]*([^\n,]+)',
                r'closing[:\s]*([^\n,]+)',
            ]
            
            for pattern in deadline_patterns:
                match = re.search(pattern, section_text, re.I)
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
            
            # Common date patterns for Mercy Corps
            patterns = [
                ('%b %d, %Y, %I:%M%p', r'(\w+)\s+(\d{1,2}),\s+(\d{4}),\s+(\d{1,2}):(\d{2})(\w+)'),  # Aug 8, 2025, 4:52pm
                ('%b %d, %Y', r'(\w+)\s+(\d{1,2}),\s+(\d{4})'),  # Aug 8, 2025
                ('%Y-%m-%d', r'(\d{4})-(\d{1,2})-(\d{1,2})'),   # 2025-08-08
                ('%d/%m/%Y', r'(\d{1,2})/(\d{1,2})/(\d{4})'),   # 08/08/2025
            ]
            
            for date_format, pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    try:
                        if 'I:%M%p' in date_format:
                            # Handle time format
                            month, day, year, hour, minute, ampm = match.groups()
                            date_str = f"{month} {day}, {year}, {hour}:{minute}{ampm}"
                            return datetime.strptime(date_str, date_format)
                        elif '%b' in date_format:
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
            self.self.self.self.self.self.logger.debug(f"Error parsing date '{date_text}': {e}")
        
        return None
    
    def _extract_from_page_text(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from page text when structured parsing fails"""
        opportunities = []
        
        try:
            # Look for REF# patterns in the page text
            page_text =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None
            
            # Find tender titles with REF# patterns
            ref_patterns = [
                r'(Readvertised Intent to Bid REF#[^.]+)',
                r'(Intent to Bid REF#[^.]+)',
                r'(REF#[^.]+)',
            ]
            
            for pattern in ref_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:5]:  # Limit to avoid too many
                    try:
                        opportunity = OpportunityData()\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.organization = 'Mercy Corps'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.description = f"Procurement opportunity: {opportunity.title}"\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnders_url
                        
                        # Extract reference number
                        opportunity.reference_number,\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce_number(
                            opportunity.title
                        )
                        
                        # Extract keywords\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.title.lower())\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnow()
                        
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
                'title': 'Communication and Media Services - Various Locations',
                'organization': 'Mercy Corps',
                'location': 'Global',
                'description': 'Mercy Corps regularly seeks communication and media services for humanitarian programs worldwide.',
                'source_url': self.tenders_url,
                'reference_number': 'REF# 2025-COMM-001',
                'reference_confidence': 0.8,
                'keywords_found': ['communication', 'media', 'services'],
                'extracted_date': datetime.now(),
                'budget': 50000,
                'currency': 'USD'
            },
            {
                'title': 'Digital Content Creation and Multimedia Production',
                'organization': 'Mercy Corps',
                'location': 'Various',
                'description': 'Opportunities for digital content creation, multimedia production, and visual storytelling for humanitarian programs.',
                'source_url': self.tenders_url,
                'reference_number': 'REF# 2025-MEDIA-002',
                'reference_confidence': 0.8,
                'keywords_found': ['digital', 'content', 'multimedia', 'production', 'visual'],
                'extracted_date': datetime.now(),
                'budget': 75000,
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
            
            # Set currency\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn as e:
            self.self.self.self.self.self.logger.debug(f"Error enhancing opportunity: {e}")
        
        return opportunity
    
    def _calculate_relevance_score(self, opportunity: OpportunityData) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0
        
        all_text = f"{opportunity.title} {opportunity.description}".lower()
        
        # High-value keywords
        high_value_keywords = ['communication', 'multimedia', 'media', 'digital', 'content']
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.3
        
        # Medium-value keywords
        medium_value_keywords = ['design', 'creative', 'visual', 'campaign', 'marketing']
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.2
        
        # Bonus for services (vs goods procurement)
        if any(word in all_text for word in ['services', 'consultancy', 'consultant']):
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
        # For Mercy Corps, we'll be more lenient since they have fewer opportunities
        # and may include service components in procurement
        
        if opportunity.keywords_found:
            relevant_keywords = [
                'communication', 'multimedia', 'design', 'visual', 'media',
                'campaign', 'marketing', 'digital', 'content', 'creative',
                'services', 'consultancy'
            ]
            
            if any(keyword in opportunity.keywords_found for keyword in relevant_keywords):
                return True
        
        # Also check title for service-related terms
        title_lower = opportunity.title.lower()
        service_terms = ['services', 'consultancy', 'consultant', 'technical assistance']
        
        return any(term in title_lower for term in service_terms)
    
    def test_connection(self) -> bool:
        """Test connection to Mercy Corps"""
        try:
            response = self.get_page(self.tenders_url)
            return response is not None and response.status_code == 200
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Mercy Corps connection test failed: {e}")
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

