"""
UNDP (United Nations Development Programme) scraper for Proposaland
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper, OpportunityData


class UNDPScraper(BaseScraper):
    """Scraper for UNDP procurement opportunities."""

    def __init__(self, config: Dict, website_config: Dict = None):
        super().__init__(config, website_config)
        self.organization = "UNDP"
        self.base_url = "https://procurement-notices.undp.org"
        self.opportunities_url = "https://procurement-notices.undp.org/view_procurements.cfm"
        scraper_config = config.get('scraper_configs', {}).get('undp', {})
        self.max_pages = scraper_config.get('max_pages', 5)

    def scrape_opportunities(self) -> List[OpportunityData]:
        opportunities: List[OpportunityData] = []
        try:
            soup = self.get_page(self.opportunities_url)
            if not soup:
                self.logger.error("Failed to fetch UNDP main page")
                return self._get_fallback_opportunities()

            parsed = self._parse_opportunities(soup)
            for opp in parsed:
                opportunities.append(self._convert_dict_to_opportunity_data(opp))

            self.logger.info(f"Found {len(opportunities)} opportunities from UNDP")
            return opportunities
        except Exception as e:
            self.logger.error(f"Error scraping UNDP: {e}")
            return self._get_fallback_opportunities()

    def _parse_opportunities(self, soup: BeautifulSoup) -> List[Dict]:
        opportunities: List[Dict] = []
        try:
            containers = soup.find_all(
                ['div', 'tr'],
                class_=lambda x: x and any(t in x.lower() for t in ['opportunity', 'procurement', 'notice']) if x else False,
            )
            if not containers:
                containers = soup.find_all('tr')

            for c in containers:
                opp = self._parse_opportunity_container(c)
                if opp:
                    opportunities.append(opp)
        except Exception as e:
            self.logger.warning(f"Error parsing UNDP opportunities: {e}")
        return opportunities

    def _parse_opportunity_container(self, container) -> Optional[Dict]:
        try:
            text_content = container.get_text("\n", strip=True)
            if len(text_content) < 20:
                return None

            lines = [ln.strip() for ln in text_content.split('\n') if ln.strip()]
            title = lines[0] if lines else ''

            source_url = self.opportunities_url
            link = container.find('a', href=True)
            if link:
                href = link['href']
                if href.startswith('http'):
                    source_url = href
                elif href.startswith('/'):
                    source_url = f"{self.base_url}{href}"

            opportunity: Dict[str, Optional[str]] = {
                'title': title,
                'organization': self.organization,
                'source_url': source_url,
                'description': text_content[:500],
                'location': '',
                'reference_number': self.extract_reference_number(text_content),
                'keywords_found': self.extract_keywords(text_content),
                'raw_data': {'full_text': text_content},
            }
            return opportunity if title else None
        except Exception as e:
            self.logger.warning(f"Error parsing UNDP opportunity container: {e}")
            return None

    def _convert_dict_to_opportunity_data(self, opp_dict: Dict) -> OpportunityData:
        opp = OpportunityData()
        opp.title = opp_dict.get('title', '')
        opp.organization = opp_dict.get('organization', self.organization)
        opp.source_url = opp_dict.get('source_url', '')
        opp.description = opp_dict.get('description', '')
        opp.location = opp_dict.get('location', '')
        opp.reference_number = opp_dict.get('reference_number', '')
        opp.keywords_found = opp_dict.get('keywords_found', [])
        opp.raw_data = opp_dict.get('raw_data', {})
        return opp

    def _get_fallback_opportunities(self) -> List[OpportunityData]:
        fallback = {
            'title': 'UNDP - Development Communication Services',
            'organization': self.organization,
            'location': 'Global',
            'description': 'Communication and multimedia services opportunity from UNDP. Fallback opportunity.',
            'source_url': self.opportunities_url,
            'reference_number': 'UNDP-FALLBACK-001',
            'keywords_found': ['communication', 'multimedia'],
        }
        return [self._convert_dict_to_opportunity_data(fallback)]
"""
UNDP-specific scraper for Proposaland opportunity monitoring system.
Handles UNDP procurement notices and business opportunities.
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional
from bs4 import BeautifulSoup
from loguru import logger
import urllib.parse

from .base_scraper import BaseScraper, OpportunityData


class UNDPScraper(BaseScraper):
    """Scraper for UNDP procurement opportunities."""
    
    def __init__(self, config, website_config):
        super().__init__(config, website_config)
        self.base_url = "https://procurement-notices.undp.org"
        self.search_url = f"{self.base_url}/search.cfm"
        
    def scrape_opportunities(self) -> List[OpportunityData]:
        """Scrape opportunities from UNDP procurement notices."""
        opportunities = []
        
        try:
            # Search for opportunities with multimedia keywords
            for keyword in self.keywords[:5]:  # Limit to first 5 keywords to avoid too many requests
                keyword_opportunities = self._search_by_keyword(keyword)
                opportunities.extend(keyword_opportunities)
            
            # Also get recent opportunities without keyword filter
            recent_opportunities = self._get_recent_opportunities()
            opportunities.extend(recent_opportunities)
            
        except Exception as e:
            logger.error(f"Error scraping UNDP: {e}")
        
        # Remove duplicates based on reference number
        unique_opportunities = self._remove_duplicates(opportunities)
        
        # Filter relevant opportunities
        relevant_opportunities = [opp for opp in unique_opportunities if self.is_relevant_opportunity(opp)]
        logger.info(f"Found {len(relevant_opportunities)} relevant opportunities from UNDP")
        
        return relevant_opportunities
    
    def _search_by_keyword(self, keyword: str) -> List[OpportunityData]:
        """Search for opportunities by keyword."""
        opportunities = []
        
        try:
            # Prepare search parameters
            params = {
                'title': keyword,
                'from_date': (datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y'),
                'to_date': (datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y')
            }
            
            # Build search URL
            search_url = f"{self.search_url}?" + urllib.parse.urlencode(params)
            
            soup = self.get_page(search_url)
            if not soup:
                logger.warning(f"Failed to search UNDP for keyword: {keyword}")
                return opportunities
            
            # Extract opportunities from search results
            opportunities = self._extract_opportunities_from_page(soup)
            logger.info(f"Found {len(opportunities)} opportunities for keyword '{keyword}'")
            
        except Exception as e:
            logger.warning(f"Error searching UNDP for keyword '{keyword}': {e}")
        
        return opportunities
    
    def _get_recent_opportunities(self) -> List[OpportunityData]:
        """Get recent opportunities without keyword filter."""
        opportunities = []
        
        try:
            # Get opportunities from the last 30 days
            params = {
                'from_date': (datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y'),
                'to_date': (datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y')
            }
            
            search_url = f"{self.search_url}?" + urllib.parse.urlencode(params)
            
            soup = self.get_page(search_url)
            if not soup:
                logger.warning("Failed to get recent UNDP opportunities")
                return opportunities
            
            opportunities = self._extract_opportunities_from_page(soup)
            logger.info(f"Found {len(opportunities)} recent opportunities from UNDP")
            
        except Exception as e:
            logger.warning(f"Error getting recent UNDP opportunities: {e}")
        
        return opportunities
    
    def _extract_opportunities_from_page(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Extract opportunities from a search results page."""
        opportunities = []
        
        # Look for opportunity containers in the search results
        # UNDP uses table-like structure or div containers for opportunities
        opportunity_containers = soup.find_all(['div', 'tr'], class_=re.compile(r'(opportunity|notice|procurement)', re.I))
        
        # If no specific containers found, look for links with opportunity patterns
        if not opportunity_containers:
            opportunity_containers = soup.find_all('a', href=re.compile(r'view\.cfm', re.I))
        
        # Also look for any containers with titles that match our patterns
        if not opportunity_containers:
            opportunity_containers = soup.find_all(['div', 'p'], string=re.compile(r'(title|ref|deadline)', re.I))
        
        for container in opportunity_containers:
            try:
                opportunity = self._parse_opportunity_container(container)
                if opportunity:
                    opportunities.append(opportunity)
            except Exception as e:
                logger.warning(f"Error parsing UNDP opportunity container: {e}")
                continue
        
        # If we still don't have opportunities, try to parse the entire page content
        if not opportunities:
            opportunities = self._parse_page_content(soup)
        
        return opportunities
    
    def _parse_opportunity_container(self, container) -> Optional[OpportunityData]:
        """Parse an individual opportunity container."""
        opportunity = OpportunityData()
        opportunity.organization = "UNDP"
        opportunity.source_url = self.search_url
        
        # Extract text content from container
        container_text = container.get_text(strip=True) if hasattr(container, 'get_text') else str(container)
        
        # Look for title
        title_match = re.search(r'Title\s*(.+?)(?:UNDP Office|Deadline|Process|$)', container_text, re.IGNORECASE | re.DOTALL)
        if title_match:
            opportunity.title = title_match.group(1).strip()
        
        # Look for reference number
        ref_match = re.search(r'(UNDP-[A-Z]{2,4}-\d+)', container_text, re.IGNORECASE)
        if ref_match:
            opportunity.reference_number = ref_match.group(1)
            opportunity.reference_confidence = 0.9
        
        # Look for country/office
        office_match = re.search(r'UNDP Office/Country\s*(.+?)(?:Deadline|Process|$)', container_text, re.IGNORECASE | re.DOTALL)
        if office_match:
            opportunity.location = office_match.group(1).strip()
        
        # Look for deadline
        deadline_match = re.search(r'Deadline\s*(\d{1,2}-[A-Za-z]{3}-\d{2,4})', container_text, re.IGNORECASE)
        if deadline_match:
            try:
                deadline_str = deadline_match.group(1)
                opportunity.deadline = datetime.strptime(deadline_str, '%d-%b-%y')
            except ValueError:
                try:
                    opportunity.deadline = datetime.strptime(deadline_str, '%d-%b-%Y')
                except ValueError:
                    pass
        
        # Look for process type
        process_match = re.search(r'Process\s*(.+?)(?:$|\n)', container_text, re.IGNORECASE)
        if process_match:
            process_type = process_match.group(1).strip()
            opportunity.description = f"Process: {process_type}"
        
        # Extract keywords
        all_text = f"{opportunity.title} {opportunity.description}"
        opportunity.keywords_found = self.extract_keywords(all_text)
        
        # Look for detailed link
        if hasattr(container, 'find'):
            link_elem = container.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    href = self.base_url + href
                opportunity.source_url = href
        
        # Only return if we have meaningful content
        if opportunity.title and (opportunity.reference_number or opportunity.keywords_found):
            return opportunity
        
        return None
    
    def _parse_page_content(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Parse opportunities from the entire page content."""
        opportunities = []
        
        # Get all text content and split into potential opportunity blocks
        page_text = soup.get_text()
        
        # Split by common delimiters that separate opportunities
        opportunity_blocks = re.split(r'(?=Title\s)', page_text, flags=re.IGNORECASE)
        
        for block in opportunity_blocks:
            if len(block.strip()) < 50:  # Skip very short blocks
                continue
                
            try:
                opportunity = OpportunityData()
                opportunity.organization = "UNDP"
                opportunity.source_url = self.search_url
                
                # Extract title
                title_match = re.search(r'Title\s*(.+?)(?:\n|UNDP Office)', block, re.IGNORECASE)
                if title_match:
                    opportunity.title = title_match.group(1).strip()
                
                # Extract reference number
                ref_match = re.search(r'(UNDP-[A-Z]{2,4}-\d+)', block, re.IGNORECASE)
                if ref_match:
                    opportunity.reference_number = ref_match.group(1)
                    opportunity.reference_confidence = 0.9
                
                # Extract location
                location_match = re.search(r'UNDP Office/Country\s*(.+?)(?:\n|Deadline)', block, re.IGNORECASE)
                if location_match:
                    opportunity.location = location_match.group(1).strip()
                
                # Extract deadline
                deadline_match = re.search(r'Deadline\s*(\d{1,2}-[A-Za-z]{3}-\d{2,4})', block, re.IGNORECASE)
                if deadline_match:
                    try:
                        deadline_str = deadline_match.group(1)
                        opportunity.deadline = datetime.strptime(deadline_str, '%d-%b-%y')
                    except ValueError:
                        try:
                            opportunity.deadline = datetime.strptime(deadline_str, '%d-%b-%Y')
                        except ValueError:
                            pass
                
                # Extract keywords
                opportunity.keywords_found = self.extract_keywords(block)
                
                # Only add if we have meaningful content
                if opportunity.title and (opportunity.reference_number or opportunity.keywords_found):
                    opportunities.append(opportunity)
                    
            except Exception as e:
                logger.warning(f"Error parsing UNDP opportunity block: {e}")
                continue
        
        return opportunities
    
    def _remove_duplicates(self, opportunities: List[OpportunityData]) -> List[OpportunityData]:
        """Remove duplicate opportunities based on reference number or title."""
        seen_refs = set()
        seen_titles = set()
        unique_opportunities = []
        
        for opp in opportunities:
            # Use reference number as primary deduplication key
            if opp.reference_number:
                if opp.reference_number not in seen_refs:
                    seen_refs.add(opp.reference_number)
                    unique_opportunities.append(opp)
            # Fall back to title if no reference number
            elif opp.title:
                title_key = opp.title.lower().strip()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_opportunities.append(opp)
        
        return unique_opportunities

