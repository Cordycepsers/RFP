"""
Development Aid Scraper for Proposaland
Scrapes opportunities from https://www.developmentaid.org/tenders/search
"""

import requests
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import logging
from .base_scraper import OpportunityData, BaseScraper

class DevelopmentAidScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'Development Aid',
                'url': 'https://www.developmentaid.org/tenders/search',
                'type': 'developmentaid',
                'priority': 1.0
            }
        
        super().__init__(config, website_config)
        self.base_url = "https://www.developmentaid.org"
        self.search_url = "https://www.developmentaid.org/tenders/search"
        self.name = "Development Aid"
        
        # Development Aid specific configuration
        scraper_config = config.get('scraper_configs', {}).get('developmentaid', {})
        self.max_pages = scraper_config.get('max_pages', 5)
        self.results_per_page = 20  # Development Aid shows ~20 results per page
        self.max_opportunities = scraper_config.get('max_opportunities', 100)
        self.request_delay = scraper_config.get('request_delay', 2.0)
        
        # Reference number patterns for Development Aid
        self.reference_patterns = [
            r'([A-Z]{2,4}[-/]\d{4}[-/][A-Z0-9]{2,6}[-/]\d{2,6})',  # NPO-2025-MEX-047
            r'([A-Z]{3,5}[-/][A-Z]{2,3}[-/]\d{4,6})',  # UNDP-FJI-00666
            r'([A-Z]{2,4}[-/]\d{4}[-/]\d{3,6})',  # RFP-2025-003
            r'(RFP[/-]\d{4}[/-][A-Z0-9]{2,8}[/-]\d{2,6})',  # RFP/2025/ACNUR/MEX/047
            r'(RFQ[/-][A-Z]{2,6}[/-]\d{4}[/-]\d{2,6})',  # RFQ/CRPC/2025/003
            r'([A-Z]{2,6}[-/]\d{4}[-/]\d{6,8})',  # LRPS-2025-9198844
            r'([A-Z]{2,4}[-/]\d{2}[-/]\d{2,4})',  # TGF-25-46
            r'(P\d{6})',  # P158522 (World Bank style)
            r'([A-Z]{2,6}[-/]\d{2,4}[-/][A-Z0-9]{2,6})',  # General pattern
        ]
        
        # Setup logging
        self.logger = logging.getLogger(f"proposaland.{self.name}")
        
    def scrape_opportunities(self) -> List[Dict[str, Any]]:
        """
        Main method to scrape opportunities from Development Aid
        """
        opportunities = []
        
        try:
            self.logger.info(f"Starting Development Aid scraping from {self.search_url}")
            
            # Build search URL with multimedia/creative keywords
            search_params = self._build_search_params()
            
            # Scrape multiple pages
            for page in range(self.max_pages):
                self.logger.info(f"Scraping Development Aid page {page + 1}/{self.max_pages}")
                
                # Add pagination parameters
                page_url = self._build_page_url(search_params, page)
                
                soup = self.get_page(page_url)
                if not soup:
                    break
                
                # Parse opportunities from this page
                page_opportunities = self._parse_opportunities_page(soup)
                
                if not page_opportunities:
                    self.logger.info(f"No opportunities found on page {page + 1}, stopping")
                    break
                
                opportunities.extend(page_opportunities)
                
                # Check if we've reached our limit
                if len(opportunities) >= self.max_opportunities:
                    opportunities = opportunities[:self.max_opportunities]
                    break
                
                # Respectful delay between requests
                time.sleep(self.request_delay)
            
            self.logger.info(f"Found {len(opportunities)} opportunities from Development Aid")
            
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
        
        return opportunity_objects
            
        except Exception as e:
            self.logger.error(f"Error scraping Development Aid: {str(e)}")
            return []
    
    def _build_search_params(self) -> Dict[str, str]:
        """Build search parameters for multimedia/creative opportunities"""
        # Keywords for multimedia/creative services
        keywords = [
            "multimedia", "video", "photo", "film", "design", "visual", 
            "campaign", "communication", "media", "animation", "graphic",
            "documentation", "training", "capacity building", "outreach"
        ]
        
        return {
            'q': ' OR '.join(keywords),  # Search query
            'sort': 'modified_date',  # Sort by most recent
            'order': 'desc'  # Descending order
        }
    
    def _build_page_url(self, search_params: Dict[str, str], page: int) -> str:
        """Build URL for specific page"""
        base_url = self.search_url
        
        # Add search parameters
        params = []
        for key, value in search_params.items():
            params.append(f"{key}={value}")
        
        # Add pagination
        if page > 0:
            params.append(f"page={page + 1}")
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        else:
            return base_url
    
    def _parse_opportunities_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse opportunities from a search results page"""
        opportunities = []
        
        try:
            # Look for opportunity containers in the grid
            # Development Aid uses a grid layout with opportunity cards
            opportunity_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                term in x.lower() for term in ['tender', 'opportunity', 'result', 'item', 'card']
            ))
            
            if not opportunity_cards:
                # Try alternative selectors
                opportunity_cards = soup.find_all('tr')  # Table rows
                if not opportunity_cards:
                    opportunity_cards = soup.find_all('div', class_=lambda x: x and 'row' in x.lower())
            
            for card in opportunity_cards:
                try:
                    opportunity = self._parse_opportunity_card(card)
                    if opportunity and opportunity.get('title'):
                        opportunities.append(opportunity)
                except Exception as e:
                    self.logger.warning(f"Error parsing opportunity card: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing opportunities page: {str(e)}")
        
        return opportunities
    
    def _parse_opportunity_card(self, card: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Parse individual opportunity card"""
        try:
            opportunity = {}
            
            # Extract title and URL
            title_link = card.find('a', href=True)
            if title_link:
                opportunity['title'] = title_link.get_text(strip=True)
                opportunity['url'] = urljoin(self.base_url, title_link['href'])
            else:
                # Try alternative title extraction
                title_elem = card.find(['h1', 'h2', 'h3', 'h4', 'strong'])
                if title_elem:
                    opportunity['title'] = title_elem.get_text(strip=True)
                else:
                    return None
            
            # Extract organization
            org_elem = card.find(text=lambda text: text and any(
                term in text.lower() for term in ['funding agency', 'organization', 'client']
            ))
            if org_elem:
                opportunity['organization'] = org_elem.strip()
            else:
                # Try to extract from title or other elements
                opportunity['organization'] = self._extract_organization_from_title(opportunity.get('title', ''))
            
            # Extract location
            location_elem = card.find(text=lambda text: text and any(
                term in text.lower() for term in ['location', 'country', 'region']
            ))
            if location_elem:
                opportunity['location'] = location_elem.strip()
            else:
                opportunity['location'] = self._extract_location_from_card(card)
            
            # Extract deadline
            deadline_text = self._extract_deadline_from_card(card)
            if deadline_text:
                opportunity['deadline'] = self._parse_deadline(deadline_text)
                opportunity['deadline_text'] = deadline_text
            
            # Extract budget/value
            budget_text = self._extract_budget_from_card(card)
            if budget_text:
                opportunity['budget'] = self._parse_budget(budget_text)
                opportunity['budget_text'] = budget_text
            
            # Extract reference number
            ref_number, confidence = self._extract_reference_number(opportunity.get('title', ''))
            opportunity['reference_number'] = ref_number
            opportunity['reference_confidence'] = confidence
            
            # Extract description
            desc_elem = card.find(['p', 'div'], class_=lambda x: x and 'description' in x.lower())
            if desc_elem:
                opportunity['description'] = desc_elem.get_text(strip=True)
            else:
                opportunity['description'] = opportunity.get('title', '')
            
            # Extract keywords found
            all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}"
            opportunity['keywords_found'] = self.extract_keywords(all_text)
            
            # Set source information
            opportunity['source'] = self.name
            opportunity['source_url'] = self.search_url
            opportunity['extracted_date'] = datetime.now().isoformat()
            
            return opportunity
            
        except Exception as e:
            self.logger.warning(f"Error parsing opportunity card: {str(e)}")
            return None
    
    def _extract_organization_from_title(self, title: str) -> str:
        """Extract organization from title"""
        # Common organization patterns in titles
        org_patterns = [
            r'([A-Z]{2,6})\s*[-–—]\s*',  # NPO - Title
            r'^([A-Z]{2,6})\s+',  # NPO Title
            r'\(([A-Z]{2,6})\)',  # Title (NPO)
        ]
        
        for pattern in org_patterns:
            import re
            match = re.search(pattern, title)
            if match:
                return match.group(1)
        
        return "Development Aid"
    
    def _extract_location_from_card(self, card: BeautifulSoup) -> str:
        """Extract location from opportunity card"""
        # Look for location indicators
        location_indicators = ['location:', 'country:', 'region:', 'place:']
        
        for indicator in location_indicators:
            elem = card.find(text=lambda text: text and indicator in text.lower())
            if elem:
                # Extract text after the indicator
                text = elem.strip()
                parts = text.split(':')
                if len(parts) > 1:
                    return parts[1].strip()
        
        # Try to find country names in the text
        countries = [
            'Afghanistan', 'Angola', 'Bangladesh', 'Cambodia', 'Ethiopia', 
            'Kenya', 'Nepal', 'Rwanda', 'Tanzania', 'Uganda', 'Vietnam',
            'Dominican Republic', 'Guatemala', 'Haiti', 'Honduras', 'Nicaragua',
            'Global', 'Regional', 'Multi-country'
        ]
        
        card_text = card.get_text().lower()
        for country in countries:
            if country.lower() in card_text:
                return country
        
        return "Not specified"
    
    def _extract_deadline_from_card(self, card: BeautifulSoup) -> Optional[str]:
        """Extract deadline from opportunity card"""
        deadline_indicators = ['deadline:', 'due:', 'closing:', 'submission:', 'expires:']
        
        for indicator in deadline_indicators:
            elem = card.find(text=lambda text: text and indicator in text.lower())
            if elem:
                # Extract text after the indicator
                text = elem.strip()
                parts = text.split(':')
                if len(parts) > 1:
                    return parts[1].strip()
        
        # Look for date patterns
        import re
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',
            r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b',
        ]
        
        card_text = card.get_text()
        for pattern in date_patterns:
            matches = re.findall(pattern, card_text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_budget_from_card(self, card: BeautifulSoup) -> Optional[str]:
        """Extract budget from opportunity card"""
        budget_indicators = ['budget:', 'value:', 'amount:', 'contract value:', 'estimated:']
        
        for indicator in budget_indicators:
            elem = card.find(text=lambda text: text and indicator in text.lower())
            if elem:
                # Extract text after the indicator
                text = elem.strip()
                parts = text.split(':')
                if len(parts) > 1:
                    return parts[1].strip()
        
        # Look for currency patterns
        import re
        currency_patterns = [
            r'(USD?\s*[\d,]+(?:\.\d{2})?)',
            r'(EUR?\s*[\d,]+(?:\.\d{2})?)',
            r'(\$\s*[\d,]+(?:\.\d{2})?)',
            r'(€\s*[\d,]+(?:\.\d{2})?)',
        ]
        
        card_text = card.get_text()
        for pattern in currency_patterns:
            matches = re.findall(pattern, card_text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
    
    def _parse_deadline(self, deadline_text: str) -> Optional[datetime]:
        """Parse deadline text to datetime"""
        if not deadline_text:
            return None
        
        # Common date formats
        formats = [
            '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%Y/%m/%d',
            '%d %b %Y', '%d %B %Y', '%b %d, %Y', '%B %d, %Y'
        ]
        
        # Clean the text
        import re
        date_text = re.sub(r'[^\w\s/,-]', '', deadline_text).strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
        
        return None
    
    def _parse_budget(self, budget_text: str) -> Optional[float]:
        """Parse budget text to float"""
        if not budget_text:
            return None
        
        # Extract numeric value
        import re
        numbers = re.findall(r'[\d,]+(?:\.\d{2})?', budget_text.replace(',', ''))
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        
        return None
    
    def _extract_reference_number(self, text: str) -> tuple[str, float]:
        """Extract reference number from text"""
        if not text:
            return "", 0.0
        
        # Use the advanced reference extractor from base class
        return self.extract_reference_number_advanced(text)
    
    def _is_relevant_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Check if opportunity is relevant for multimedia/creative services"""
        # Check for keywords
        all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower()
        
        # Must have relevant keywords
        relevant_keywords = [
            'multimedia', 'video', 'photo', 'film', 'design', 'visual', 
            'campaign', 'communication', 'media', 'animation', 'graphic',
            'documentation', 'training', 'capacity', 'outreach', 'awareness'
        ]
        
        has_keywords = any(keyword in all_text for keyword in relevant_keywords)
        if not has_keywords:
            return False
        
        # Check geographic exclusions
        location = opportunity.get('location', '').lower()
        excluded_locations = ['india', 'pakistan', 'china']
        
        for excluded in excluded_locations:
            if excluded in location:
                return False
        
        # Check for local company exclusions
        if 'local company' in all_text or 'local firm' in all_text:
            return False
        
        return True
    
    def _enhance_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance opportunity with additional information"""
        # Add scoring
        opportunity['relevance_score'] = self._calculate_relevance_score(opportunity)
        
        # Add priority level
        opportunity['priority'] = self._determine_priority(opportunity)
        
        # Add days until deadline
        if opportunity.get('deadline'):
            try:
                deadline = opportunity['deadline']
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline)
                days_until = (deadline - datetime.now()).days
                opportunity['days_until_deadline'] = days_until
            except:
                opportunity['days_until_deadline'] = None
        
        return opportunity
    
    def _calculate_relevance_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0
        
        all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower()
        
        # High-value keywords
        high_value_keywords = ['multimedia', 'video', 'design', 'communication', 'campaign']
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.2
        
        # Medium-value keywords
        medium_value_keywords = ['photo', 'film', 'visual', 'media', 'animation', 'graphic']
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.1
        
        # Reference number confidence
        score += opportunity.get('reference_confidence', 0.0) * 0.3
        
        # Budget consideration
        budget = opportunity.get('budget')
        if budget:
            if 5000 <= budget <= 500000:  # Target range
                score += 0.2
        
        return min(score, 1.0)
    
    def _determine_priority(self, opportunity: Dict[str, Any]) -> str:
        """Determine priority level"""
        score = opportunity.get('relevance_score', 0.0)
        
        if score >= 0.8:
            return 'Critical'
        elif score >= 0.6:
            return 'High'
        elif score >= 0.4:
            return 'Medium'
        else:
            return 'Low'
    
    def test_connection(self):
        """Test connection to Development Aid website"""
        try:
            soup = self.get_page(self.search_url)
            return soup is not None
        except Exception as e:
            self.logger.error(f"Development Aid connection test failed: {str(e)}")
            return False
    

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

    def get_opportunity_details(self, opportunity_url):
        """Get detailed information for a specific opportunity"""
        try:
            if not opportunity_url:
                return None
                
            soup = self.get_page(opportunity_url)
            if not soup:
                return None
            
            # Extract detailed information
            details = {
                'full_description': '',
                'requirements': '',
                'contact_info': '',
                'documents': []
            }
            
            # Extract full description
            desc_elem = soup.find(['div', 'section'], class_=lambda x: x and 'description' in x.lower())
            if desc_elem:
                details['full_description'] = desc_elem.get_text(strip=True)
            
            # Extract requirements
            req_elem = soup.find(['div', 'section'], class_=lambda x: x and 'requirement' in x.lower())
            if req_elem:
                details['requirements'] = req_elem.get_text(strip=True)
            
            # Extract contact information
            contact_elem = soup.find(['div', 'section'], class_=lambda x: x and 'contact' in x.lower())
            if contact_elem:
                details['contact_info'] = contact_elem.get_text(strip=True)
            
            # Extract document links
            doc_links = soup.find_all('a', href=lambda x: x and any(
                ext in x.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
            ))
            
            for link in doc_links:
                details['documents'].append({
                    'title': link.get_text(strip=True),
                    'url': urljoin(self.base_url, link['href'])
                })
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting opportunity details: {str(e)}")
            return None

