"""
ReliefWeb Scraper for Proposaland
Scrapes job and consultancy opportunities from https://reliefweb.int/jobs
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

class ReliefWebScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'ReliefWeb',
                'url': 'https://reliefweb.int/jobs',
                'type': 'reliefweb'
            }
        
        super().__init__(config, website_config)
        
        # ReliefWeb specific settings
        self.base_url = 'https://reliefweb.int'
        self.jobs_url = 'https://reliefweb.int/jobs'
        self.max_pages = config.get('scraper_settings', {}).get('reliefweb', {}).get('max_pages', 5)
        self.max_opportunities = config.get('scraper_settings', {}).get('reliefweb', {}).get('max_opportunities', 50)
        
        # Enhanced headers for ReliefWeb
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
        Main method to scrape opportunities from ReliefWeb
        """
        try:
            self.self.self.self.self.self.logger.info(f"Starting ReliefWeb scraping from {self.jobs_url}")
            
            all_opportunities = []
            
            # Start with multimedia keyword search
            multimedia_opportunities = self._search_multimedia_opportunities()
            all_opportunities.extend(multimedia_opportunities)
            
            # If we need more opportunities, scrape general listings
            if len(all_opportunities) < self.max_opportunities:
                general_opportunities = self._scrape_general_listings()
                all_opportunities.extend(general_opportunities)
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_opportunities = []
            for opp in all_opportunities:
                if opp.source_url not in seen_urls:
                    seen_urls.add(opp.source_url)
                    unique_opportunities.append(opp)
            
            self.self.self.self.self.self.logger.info(f"Found {len(unique_opportunities)} unique opportunities from ReliefWeb")
            
            # Convert dictionaries to OpportunityData objects

            
            opportunity_objects = []
            for opp in unique_opportunities:
                if isinstance(opp, dict):
                    opportunity_objects.append(self._convert_dict_to_opportunity_data(opp))
                else:
                    opportunity_objects.append(opp)
            
            return opportunity_objects[:self.max_opportunities]
            
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error scraping ReliefWeb: {str(e)}")
            return [self._convert_dict_to_opportunity_data(opp) for opp in self._get_fallback_opportunities()]
    
    def _search_multimedia_opportunities(self) -> List[OpportunityData]:
        """Search for multimedia-specific opportunities"""
        opportunities = []
        
        multimedia_keywords = [
            'communication', 'multimedia', 'design', 'media', 'visual',
            'campaign', 'marketing', 'digital', 'content', 'creative'
        ]
        
        for keyword in multimedia_keywords[:3]:  # Limit to avoid too many requests
            try:
                search_url = f"{self.jobs_url}?search={keyword}"
                self.self.self.self.self.self.logger.info(f"Searching ReliefWeb for: {keyword}")
                
                response = self.get_page(search_url)
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_opportunities = self._parse_job_listings(soup, keyword_context=keyword)
                    opportunities.extend(page_opportunities)
                    
                    # Rate limiting
                    time.sleep(2)
                    
            except Exception as e:
                self.self.self.self.self.self.logger.warning(f"Error searching for {keyword}: {e}")
                continue
        
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _scrape_general_listings(self) -> List[OpportunityData]:
        """Scrape general job listings"""
        opportunities = []
        
        for page in range(1, min(self.max_pages + 1, 4)):  # Limit pages
            try:
                if page == 1:
                    url = self.jobs_url
                else:
                    url = f"{self.jobs_url}?page={page-1}"  # ReliefWeb uses 0-based pagination
                
                self.self.self.self.self.self.logger.info(f"Scraping ReliefWeb page {page}")
                
                response = self.get_page(url)
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_opportunities = self._parse_job_listings(soup)
                    opportunities.extend(page_opportunities)
                    
                    # Rate limiting
                    time.sleep(1)
                else:
                    break
                    
            except Exception as e:
                self.self.self.self.self.self.logger.warning(f"Error scraping page {page}: {e}")
                continue
        
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _parse_job_listings(self, soup: BeautifulSoup, keyword_context: str = None) -> List[OpportunityData]:
        """Parse job listings from ReliefWeb page"""
        opportunities = []
        
        try:
            # Find job listings - ReliefWeb uses specific structure
            job_items =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            
            if not job_items:
                # Try alternative selectors
                job_items =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
                
            for item in job_items[:20]:  # Limit per page
                try:
                    opportunity = self._extract_job_details(item, keyword_context)
                    if opportunity and self._is_relevant_opportunity(opportunity):
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    self.self.self.self.self.self.logger.debug(f"Error parsing job item: {e}")
                    continue
            
            # If no structured items found, try text-based extraction
            if not opportunities:
                opportunities = self._extract_from_text(soup, keyword_context)
                
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error parsing job listings: {e}")
        
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _extract_job_details(self, item: BeautifulSoup, keyword_context: str = None) -> Optional[OpportunityData]:
        """Extract details from a job listing item"""
        try:
            opportunity = OpportunityData()
            
            # Extract title
            title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|heading'))
            if not title_elem:
                title_elem = item.find('a', href=re.compile(r'/job/'))
            
            if title_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passname == 'a':\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn(self.base_url, title_elem.get('href', ''))
                else:
                    link_elem = item.find('a', href=re.compile(r'/job/'))
                    if link_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn(self.base_url, link_elem.get('href', ''))
            
            if not opportunity.title:
                return None
            
            # Extract organization
            org_elem = item.find(['span', 'div', 'p'], class_=re.compile(r'org|source|author'))
            if org_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn
            location_elem = item.find(['span', 'div'], class_=re.compile(r'location|country'))
            if location_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn_elem.get_text(strip=True)
            
            # Extract dates
            date_elem = item.find(['span', 'div', 'time'], class_=re.compile(r'date|time'))
            if date_elem:
                date_text = date_elem.get_text(strip=True)\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn
            desc_elem = item.find(['p', 'div'], class_=re.compile(r'desc|summary|content'))
            if desc_elem:\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.organization = opportunity.organization or 'ReliefWeb Partner'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.location or 'Various'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.description or f"Opportunity from ReliefWeb: {opportunity.title}"\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.source_url or self.jobs_url
            
            # Extract keywords
            all_text = f"{opportunity.title} {opportunity.description}".lower()\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passntext keyword if provided
            if keyword_context and keyword_context.lower() not in opportunity.keywords_found:
                opportunity.keywords_found.append(keyword_context.lower())
            
            # Extract reference number
            opportunity.reference_number,\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce_number(
                f"{opportunity.title} {opportunity.description}"
            )
            
            # Set extracted date\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnow()
            
            return opportunity
            
        except Exception as e:
            self.self.self.self.self.self.logger.debug(f"Error extracting job details: {e}")
            return None
    
    def _extract_from_text(self, soup: BeautifulSoup, keyword_context: str = None) -> List[OpportunityData]:
        """Extract opportunities from page text when structured parsing fails"""
        opportunities = []
        
        try:
            # Look for job-related links
            job_links =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            
            for link in job_links[:10]:  # Limit to avoid too many
                try:
                    opportunity = OpportunityData()\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnk.get_text(strip=True)\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passn(self.base_url, link.get('href', ''))\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passner'\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.description = f"Job opportunity from ReliefWeb: {opportunity.title}"
                    
                    # Extract keywords\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnity.title.lower())
                    
                    # Add context keyword if provided
                    if keyword_context and keyword_context.lower() not in opportunity.keywords_found:
                        opportunity.keywords_found.append(keyword_context.lower())
                    
                    # Extract reference number
                    opportunity.reference_number,\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnce_number(
                        opportunity.title
                    )\1try:\n\1    \2 = \3\n\1except (AttributeError, KeyError):\n\1    passnow()
                    
                    if self._is_relevant_opportunity(opportunity):
                        opportunities.append(opportunity)
                        
                except Exception as e:
                    self.self.self.self.self.self.logger.debug(f"Error extracting from link: {e}")
                    continue
                    
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"Error in text extraction: {e}")
        
        return [self._convert_dict_to_opportunity_data(opp) if isinstance(opp, dict) else opp for opp in opportunities]
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from various formats"""
        if not date_text:
            return None
        
        try:
            # Common date patterns
            patterns = [
                r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # 15 Aug 2025
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2025-08-15
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 15/08/2025
                r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 15-08-2025
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    try:
                        if len(match.groups()) == 3:
                            if match.group(2).isalpha():  # Month name
                                date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                                return datetime.strptime(date_str, '%d %b %Y')
                            else:  # Numeric date
                                if len(match.group(1)) == 4:  # Year first
                                    return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                                else:  # Day first
                                    return datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)))
                    except ValueError:
                        continue
            
            # If no pattern matches, try relative dates
            if 'day' in date_text.lower():
                days_match = re.search(r'(\d+)\s*day', date_text.lower())
                if days_match:
                    days = int(days_match.group(1))
                    return datetime.now() + timedelta(days=days)
            
        except Exception as e:
            self.self.self.self.self.self.logger.debug(f"Error parsing date '{date_text}': {e}")
        
        return None
    
    def _is_relevant_opportunity(self, opportunity: OpportunityData) -> bool:
        """Check if opportunity is relevant for multimedia/creative services"""
        if not opportunity.keywords_found:
            return False
        
        # Must have at least one relevant keyword
        relevant_keywords = [
            'communication', 'multimedia', 'design', 'visual', 'media',
            'campaign', 'marketing', 'digital', 'content', 'creative',
            'video', 'photo', 'film', 'animation', 'graphic'
        ]
        
        return any(keyword in opportunity.keywords_found for keyword in relevant_keywords)
    
    def test_connection(self) -> bool:
        """Test connection to ReliefWeb"""
        try:
            response = self.get_page(self.jobs_url)
            return response is not None and response.status_code == 200
        except Exception as e:
            self.self.self.self.self.self.logger.error(f"ReliefWeb connection test failed: {e}")
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
            
            # Extract requirements
            req_elem =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            if req_elem:
                details['requirements'] = req_elem.get_text(strip=True)
            
            # Extract application process
            app_elem =\1try:\n\1    \2\n\1except (AttributeError, TypeError):\n\1    None)
            if app_elem:
                details['application_process'] = app_elem.get_text(strip=True)
            
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
    def _get_fallback_opportunities(self) -> List[dict]:
        """Provide fallback opportunities when scraping fails"""
        return [
            {
                'title': f'{self.organization} - Multimedia Services Opportunity',
                'organization': self.organization,
                'location': 'Global',
                'description': f'Multimedia and communication services opportunity from {self.organization}. This is a fallback opportunity generated when live scraping encounters issues.',
                'source_url': getattr(self, 'base_url', ''),
                'deadline': '',
                'reference_number': f'{self.organization.upper().replace(" ", "")}-FALLBACK-001',
                'keywords_found': ['multimedia', 'communication'],
                'relevance_score': 0.6,
                'raw_data': {'source': 'fallback', 'confidence': 0.5}
            }
        ]
