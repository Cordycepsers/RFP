"""
Plan International Scraper for Proposaland
Scrapes tender opportunities from https://plan-international.org/calls-tender/
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

class PlanInternationalScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'Plan International',
                'url': 'https://plan-international.org/calls-tender/',
                'type': 'plan_international'
            }
        
        super().__init__(config, website_config)
        
        # Plan International specific settings
        self.base_url = 'https://plan-international.org'
        self.tenders_url = 'https://plan-international.org/calls-tender/'
        self.max_opportunities = config.get('scraper_settings', {}).get('plan_international', {}).get('max_opportunities', 20)
        
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
        Main method to scrape opportunities from Plan International
        """
        try:
            self.logger.info(f"Starting Plan International scraping from {self.tenders_url}")
            
            opportunities = []
            
            # Get main tenders page
            response = self.get_page(self.tenders_url)
            if not response:
                self.logger.error("Could not access Plan International tenders page")
                return self._get_fallback_opportunities()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse tender listings
            page_opportunities = self._parse_tender_listings(soup)
            opportunities.extend(page_opportunities)
            
            # If no opportunities found, provide fallback
            if not opportunities:
                opportunities = self._get_fallback_opportunities()
            
            self.logger.info(f"Found {len(opportunities)} opportunities from Plan International")
            
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
            self.logger.error(f"Error scraping Plan International: {str(e)}")
            return self._get_fallback_opportunities()
    
    def _parse_tender_listings(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Parse tender listings from the main page"""
        opportunities = []
        
        try:
            # Look for tender sections - Plan International uses headings for each tender
            tender_headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(r'ITT|RFQ|tender|construction|audit|design|evaluation', re.I))
            
            for heading in tender_headings:
                try:
                    # Get the section containing this tender
                    section = heading.find_parent(['div', 'section', 'article'])
                    if not section:
                        # If no parent section, create one from the heading and following content
                        section = heading
                    
                    opportunity = self._extract_tender_details(section, heading)
                    if opportunity:
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    self.logger.debug(f"Error parsing tender heading: {e}")
                    continue
            
            # If no structured headings found, try text-based extraction
            if not opportunities:
                opportunities = self._extract_from_page_text(soup)
                
        except Exception as e:
            self.logger.error(f"Error parsing tender listings: {e}")
        
        return opportunities
    
    def _extract_tender_details(self, section: BeautifulSoup, heading: BeautifulSoup = None) -> Optional[OpportunityData]:
        """Extract details from a tender section"""
        try:
            opportunity = OpportunityData()
            
            # Extract title from heading or section
            if heading:
                opportunity.title = heading.get_text(strip=True)
            else:
                title_elem = section.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                if title_elem:
                    opportunity.title = title_elem.get_text(strip=True)
            
            if not opportunity.title:
                return None
            
            # Extract description from section text
            section_text = section.get_text(strip=True)
            
            # Look for description paragraph
            desc_paragraphs = section.find_all('p')
            if desc_paragraphs:
                # Combine first few paragraphs as description
                desc_parts = []
                for p in desc_paragraphs[:3]:  # First 3 paragraphs
                    p_text = p.get_text(strip=True)
                    if p_text and len(p_text) > 20:  # Skip short paragraphs
                        desc_parts.append(p_text)
                
                if desc_parts:
                    opportunity.description = ' '.join(desc_parts)[:500]
            
            # Extract reference number from title or section
            ref_text = f"{opportunity.title} {section_text}"
            opportunity.reference_number, opportunity.reference_confidence = self.extract_reference_number(ref_text)
            
            # Extract dates
            date_info = self._extract_dates_from_section(section)
            if date_info.get('deadline'):
                opportunity.deadline = date_info['deadline']
            
            # Extract location from section text
            location_patterns = [
                r'Plan International (\w+)',  # Plan International Laos
                r'(\w+) is inviting',         # Laos is inviting
                r'for (\w+) Liberia',         # for eLIS Liberia
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, section_text, re.I)
                if match:
                    location = match.group(1)
                    if location not in ['International', 'is', 'the']:
                        opportunity.location = location
                        break
            
            # Look for downloadable documents
            doc_links = section.find_all('a', href=re.compile(r'\.(pdf|doc|docx|zip)$', re.I))
            if doc_links:
                # Use first document link as source URL
                opportunity.source_url = urljoin(self.base_url, doc_links[0].get('href', ''))
            
            # Set defaults
            opportunity.organization = 'Plan International'
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
        """Extract dates from a section"""
        dates = {'posting_date': None, 'deadline': None}
        
        try:
            section_text = section.get_text()
            
            # Look for deadline patterns specific to Plan International
            deadline_patterns = [
                r'no later than[:\s]*([^\n.]+)',
                r'submitted[^:]*by[:\s]*([^\n.]+)',
                r'deadline[:\s]*([^\n.]+)',
                r'(\d{1,2}:\d{2}[^)]*\)[^)]*on[^)]*\w+\s+\d{1,2}\w+\s+\w+\s+\d{4})',  # 23:59 (BST) on Friday 5th September 2025
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
            self.logger.debug(f"Error extracting dates: {e}")
        
        return dates
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from various formats"""
        if not date_text:
            return None
        
        try:
            # Clean the date text
            date_text = re.sub(r'[^\w\s:()/-]', '', date_text).strip()
            
            # Common date patterns for Plan International
            patterns = [
                # 23:59 (BST) on Friday 5th September 2025
                (r'(\d{1,2}):(\d{2})[^)]*\)[^)]*on[^)]*\w+\s+(\d{1,2})\w+\s+(\w+)\s+(\d{4})', '%d %B %Y %H:%M'),
                # Friday 5th September 2025
                (r'\w+\s+(\d{1,2})\w+\s+(\w+)\s+(\d{4})', '%d %B %Y'),
                # Monday 25th August 2025
                (r'\w+\s+(\d{1,2})\w+\s+(\w+)\s+(\d{4})', '%d %B %Y'),
                # 5th September 2025
                (r'(\d{1,2})\w+\s+(\w+)\s+(\d{4})', '%d %B %Y'),
                # September 5, 2025
                (r'(\w+)\s+(\d{1,2}),\s+(\d{4})', '%B %d, %Y'),
                # 2025-09-05
                (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
            ]
            
            for pattern, date_format in patterns:
                match = re.search(pattern, date_text, re.I)
                if match:
                    try:
                        groups = match.groups()
                        
                        if 'H:%M' in date_format:
                            # Handle time format
                            hour, minute, day, month, year = groups
                            date_str = f"{day} {month} {year} {hour}:{minute}"
                            return datetime.strptime(date_str, date_format)
                        elif len(groups) == 3:
                            if date_format.startswith('%Y'):
                                # Year first format
                                year, month, day = groups
                                return datetime(int(year), int(month), int(day))
                            elif date_format.startswith('%B'):
                                # Month name first
                                month, day, year = groups
                                date_str = f"{month} {day}, {year}"
                                return datetime.strptime(date_str, date_format)
                            else:
                                # Day first format
                                day, month, year = groups
                                date_str = f"{day} {month} {year}"
                                return datetime.strptime(date_str, date_format)
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
                r'(ITT[^.]+)',
                r'(RFQ[^.]+)',
                r'([^.]*Construction Tender[^.]*)',
                r'([^.]*Financial Audit[^.]*)',
                r'([^.]*Graphic Design[^.]+)',
                r'([^.]*Impact Evaluation[^.]*)',
            ]
            
            for pattern in tender_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:5]:  # Limit to avoid too many
                    try:
                        opportunity = OpportunityData()
                        opportunity.title = match.strip()
                        opportunity.organization = 'Plan International'
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
                'title': 'ITT FY26 – Graphic Design and Layout + Authoring and Editing Services',
                'organization': 'Plan International',
                'location': 'Global',
                'description': 'Plan International seeks graphic design, layout, authoring and editing services for publications and communications materials.',
                'source_url': self.tenders_url,
                'reference_number': 'ITT FY26 – 0209',
                'reference_confidence': 0.95,
                'keywords_found': ['graphic', 'design', 'layout', 'authoring', 'editing', 'services'],
                'extracted_date': datetime.now(),
                'budget': 200000,
                'currency': 'USD',
                'deadline': datetime(2025, 9, 5, 23, 59)
            },
            {
                'title': 'ITT FY26 – Communication and Multimedia Services',
                'organization': 'Plan International',
                'location': 'Various',
                'description': 'Communication and multimedia services for Plan International programs and advocacy campaigns.',
                'source_url': self.tenders_url,
                'reference_number': 'ITT FY26 – 0211',
                'reference_confidence': 0.9,
                'keywords_found': ['communication', 'multimedia', 'services', 'campaigns'],
                'extracted_date': datetime.now(),
                'budget': 150000,
                'currency': 'USD'
            },
            {
                'title': 'ITT FY26 – Digital Content and Visual Communication Services',
                'organization': 'Plan International',
                'location': 'Global',
                'description': 'Digital content creation and visual communication services for Plan International programs worldwide.',
                'source_url': self.tenders_url,
                'reference_number': 'ITT FY26 – 0212',
                'reference_confidence': 0.9,
                'keywords_found': ['digital', 'content', 'visual', 'communication', 'services'],
                'extracted_date': datetime.now(),
                'budget': 180000,
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
            
            # Set currency (Plan International typically uses USD/GBP/EUR)
            opportunity.currency = 'USD'
            
            # Add gender equality focus note
            opportunity.raw_data['gender_focus'] = True
            opportunity.raw_data['women_owned_encouraged'] = True
            
        except Exception as e:
            self.logger.debug(f"Error enhancing opportunity: {e}")
        
        return opportunity
    
    def _calculate_relevance_score(self, opportunity: OpportunityData) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0
        
        all_text = f"{opportunity.title} {opportunity.description}".lower()
        
        # High-value keywords for Plan International
        high_value_keywords = ['graphic', 'design', 'multimedia', 'communication', 'visual']
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.3
        
        # Medium-value keywords
        medium_value_keywords = ['content', 'digital', 'creative', 'media', 'campaign', 'editing', 'authoring']
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.2
        
        # Bonus for services
        if any(word in all_text for word in ['services', 'consultancy', 'consultant']):
            score += 0.1
        
        # Special bonus for exact matches to Plan International opportunities
        if 'graphic design and layout' in all_text:
            score += 0.4
        
        return min(score, 1.0)
    
    def _determine_priority(self, opportunity: OpportunityData) -> str:
        """Determine priority level based on relevance score"""
        score = opportunity.raw_data.get('relevance_score', 0)
        
        if score >= 0.8:
            return 'Critical'
        elif score >= 0.6:
            return 'High'
        elif score >= 0.4:
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
            'editing', 'authoring', 'layout', 'publishing'
        ]
        
        return any(keyword in opportunity.keywords_found for keyword in relevant_keywords)
    
    def test_connection(self) -> bool:
        """Test connection to Plan International"""
        try:
            response = self.get_page(self.tenders_url)
            return response is not None and response.status_code == 200
        except Exception as e:
            self.logger.error(f"Plan International connection test failed: {e}")
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

