"""
IUCN Scraper for Proposaland
Scrapes opportunities from https://iucn.org/procurement/currently-ru            # Find the open tenders section
            open_section = None
            for h2 in soup.find_all('h2'):
                if h2.get_text() and 'open tenders' in h2.get_text().lower():
                    open_section = h2
                    breaking-tenders
"""

import requests
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import re
from .base_scraper import OpportunityData, BaseScraper

class IUCNScraper(BaseScraper):
    def __init__(self, config, website_config=None):
        # Create default website config if not provided
        if website_config is None:
            website_config = {
                'name': 'IUCN',
                'url': 'https://iucn.org/procurement/currently-running-tenders',
                'type': 'iucn',
                'priority': 1.0
            }
        
        super().__init__(config, website_config)
        self.base_url = "https://iucn.org"
        self.tenders_url = "https://iucn.org/procurement/currently-running-tenders"
        self.name = "IUCN"
        
        # IUCN specific configuration
        scraper_config = config.get('scraper_configs', {}).get('iucn', {})
        self.max_opportunities = scraper_config.get('max_opportunities', 50)
        self.request_delay = scraper_config.get('request_delay', 2.0)
        
        # Reference number patterns for IUCN
        self.reference_patterns = [
            r'(IUCN[-/]\d{2}[-/]\d{2}[-/]P\d{5}[-/]\d{1,2})',  # IUCN-25-07-P03812-1
            r'(IUCN[-/]\d{2}[-/]\d{2}[-/]P\d{4,6})',  # IUCN-25-07-P05011
            r'(PACO\s+IUCN\s+\d{2}[-/]\d{2}[-/]P\d{4,6}[-/]\d{2})',  # PACO IUCN 25-06-P04799-02
            r'(RfP\s+Reference:\s*([A-Z0-9-]+))',  # RfP Reference: IUCN-25-07-P03812-1
            r'([A-Z]{2,6}[-/]\d{2,4}[-/]\d{2}[-/]P\d{4,6}[-/]\d{2})',  # General IUCN pattern
        ]
        
        # Setup logging
        self.logger = logging.getLogger(f"proposaland.{self.name}")
        
    def scrape_opportunities(self) -> List[Dict[str, Any]]:
        """
        Main method to scrape opportunities from IUCN
        """
        opportunities = []
        
        try:
            self.logger.info(f"Starting IUCN scraping from {self.tenders_url}")
            
            # Get the main tenders page
            soup = self.get_page(self.tenders_url)
            if not soup:
                return opportunities
            
            # Parse open tenders
            open_tenders = self._parse_open_tenders(soup)
            opportunities.extend(open_tenders)
            
            # Parse tenders under evaluation (if relevant)
            evaluation_tenders = self._parse_evaluation_tenders(soup)
            opportunities.extend(evaluation_tenders)
            
            self.logger.info(f"Found {len(opportunities)} opportunities from IUCN")
            
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
            self.logger.error(f"Error scraping IUCN: {str(e)}")
            return []
    
    def _parse_open_tenders(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse open tenders from the main table"""
        opportunities = []
        
        try:
            # Find the "Open tenders" section
            open_section = soup.find('h2', string=lambda text: text and 'open tenders' in text.lower())
            if not open_section:
                self.logger.warning("Could not find open tenders section")
                return opportunities
            
            # Find the table after the open tenders heading
            table = open_section.find_next('table')
            if not table:
                self.logger.warning("Could not find tenders table")
                return opportunities
            
            # Parse table rows
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                try:
                    opportunity = self._parse_tender_row(row, status='Open')
                    if opportunity:
                        opportunities.append(opportunity)
                except Exception as e:
                    self.logger.warning(f"Error parsing tender row: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing open tenders: {str(e)}")
        
        return opportunities
    
    def _parse_evaluation_tenders(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse tenders under evaluation (if they contain relevant opportunities)"""
        opportunities = []
        
        try:
            # Find the "Tenders under evaluation" section
            eval_section = soup.find('h2', string=lambda text: text and 'under evaluation' in text.lower())
            if not eval_section:
                return opportunities
            
            # Find the table after the evaluation heading
            table = eval_section.find_next('table')
            if not table:
                return opportunities
            
            # Parse table rows (only if they might be relevant for future reference)
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                try:
                    opportunity = self._parse_tender_row(row, status='Under Evaluation')
                    if opportunity and self._is_relevant_opportunity(opportunity):
                        # Only include evaluation tenders if they're highly relevant
                        opportunities.append(opportunity)
                except Exception as e:
                    continue
            
        except Exception as e:
            self.logger.warning(f"Error parsing evaluation tenders: {str(e)}")
        
        return opportunities
    
    def _parse_tender_row(self, row: BeautifulSoup, status: str = 'Open') -> Optional[Dict[str, Any]]:
        """Parse individual tender row from table"""
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 5:  # Need at least 5 columns
                return None
            
            opportunity = {}
            
            # Column structure: Deadline | Title | Office | Country | Duration | Value
            deadline_cell = cells[0]
            title_cell = cells[1]
            office_cell = cells[2]
            country_cell = cells[3]
            duration_cell = cells[4]
            value_cell = cells[5] if len(cells) > 5 else None
            
            # Extract deadline
            deadline_text = deadline_cell.get_text(strip=True)
            opportunity['deadline_text'] = deadline_text
            opportunity['deadline'] = self._parse_deadline(deadline_text)
            
            # Extract title and URL
            title_link = title_cell.find('a', href=True)
            if title_link:
                opportunity['title'] = title_link.get_text(strip=True)
                opportunity['url'] = urljoin(self.base_url, title_link['href'])
            else:
                opportunity['title'] = title_cell.get_text(strip=True)
                opportunity['url'] = self.tenders_url
            
            # Extract office/organization
            opportunity['organization'] = f"IUCN {office_cell.get_text(strip=True)}"
            
            # Extract country/location
            opportunity['location'] = country_cell.get_text(strip=True)
            
            # Extract duration
            opportunity['duration'] = duration_cell.get_text(strip=True)
            
            # Extract contract value
            if value_cell:
                value_text = value_cell.get_text(strip=True)
                opportunity['budget_text'] = value_text
                opportunity['budget'] = self._parse_budget(value_text)
            
            # Extract reference number from title or content
            ref_number, confidence = self._extract_reference_number(opportunity['title'])
            opportunity['reference_number'] = ref_number
            opportunity['reference_confidence'] = confidence
            
            # Set status
            opportunity['status'] = status
            
            # Extract description (use title for now, can be enhanced with detail page)
            opportunity['description'] = opportunity['title']
            
            # Extract keywords found
            all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}"
            opportunity['keywords_found'] = self.extract_keywords(all_text)
            
            # Set source information
            opportunity['source'] = self.name
            opportunity['source_url'] = self.tenders_url
            opportunity['extracted_date'] = datetime.now().isoformat()
            
            return opportunity
            
        except Exception as e:
            self.logger.warning(f"Error parsing tender row: {str(e)}")
            return None
    
    def _parse_deadline(self, deadline_text: str) -> Optional[datetime]:
        """Parse deadline text to datetime"""
        if not deadline_text:
            return None
        
        # Clean the text
        deadline_text = deadline_text.strip()
        
        # Handle "EXTENDED TO" cases
        if 'extended to' in deadline_text.lower():
            # Extract the new date
            parts = deadline_text.lower().split('extended to')
            if len(parts) > 1:
                deadline_text = parts[1].strip()
        
        # Common date formats used by IUCN
        formats = [
            '%d %B %Y',      # 08 September 2025
            '%d %b %Y',      # 08 Sep 2025
            '%B %d %Y',      # September 08 2025
            '%b %d %Y',      # Sep 08 2025
            '%d/%m/%Y',      # 08/09/2025
            '%m/%d/%Y',      # 09/08/2025
            '%Y-%m-%d',      # 2025-09-08
            '%d %B, %Y',     # 08 September, 2025
            '%d %b, %Y',     # 08 Sep, 2025
        ]
        
        # Try to parse with different formats
        for fmt in formats:
            try:
                return datetime.strptime(deadline_text, fmt)
            except ValueError:
                continue
        
        # Try to extract date with regex
        date_patterns = [
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, deadline_text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
        
        self.logger.warning(f"Could not parse deadline: {deadline_text}")
        return None
    
    def _parse_budget(self, budget_text: str) -> Optional[float]:
        """Parse budget text to float"""
        if not budget_text:
            return None
        
        # Extract numeric value and currency
        # Common IUCN budget formats: "USD 25,000", "EUR 25,000", "CHF 150,000", "between USD 200,000 and 250,000"
        
        # Handle range values (take the maximum)
        if 'between' in budget_text.lower() and 'and' in budget_text.lower():
            numbers = re.findall(r'[\d,]+(?:\.\d{2})?', budget_text.replace(',', ''))
            if len(numbers) >= 2:
                try:
                    return float(numbers[-1])  # Take the higher value
                except ValueError:
                    pass
        
        # Extract single value
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
        
        # Try IUCN-specific patterns first
        for pattern in self.reference_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # Handle patterns with groups
                    ref = matches[0][1] if len(matches[0]) > 1 else matches[0][0]
                else:
                    ref = matches[0]
                return ref.strip(), 0.95
        
        # Fall back to base class method
        return self.extract_reference_number_advanced(text)
    
    def _is_relevant_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Check if opportunity is relevant for multimedia/creative services"""
        # Check for keywords
        all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower()
        
        # High-priority keywords for IUCN (they often have communication needs)
        relevant_keywords = [
            'communication', 'graphic', 'design', 'website', 'photography', 'videography',
            'multimedia', 'video', 'visual', 'campaign', 'media', 'animation',
            'documentation', 'report', 'publication', 'magazine', 'layout', 'production',
            'outreach', 'awareness', 'training', 'capacity building', 'materials'
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
        
        # IUCN often has relevant opportunities, so be more inclusive
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
        
        # Add currency information
        budget_text = opportunity.get('budget_text', '')
        if budget_text:
            if 'USD' in budget_text:
                opportunity['currency'] = 'USD'
            elif 'EUR' in budget_text:
                opportunity['currency'] = 'EUR'
            elif 'CHF' in budget_text:
                opportunity['currency'] = 'CHF'
            elif 'THB' in budget_text:
                opportunity['currency'] = 'THB'
            else:
                opportunity['currency'] = 'USD'  # Default
        
        return opportunity
    
    def _calculate_relevance_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate relevance score for opportunity"""
        score = 0.0
        
        all_text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower()
        
        # High-value keywords (IUCN specific)
        high_value_keywords = [
            'communication', 'graphic design', 'website design', 'photography', 'videography',
            'multimedia', 'visual', 'campaign', 'magazine', 'publication'
        ]
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 0.25
        
        # Medium-value keywords
        medium_value_keywords = [
            'design', 'video', 'media', 'documentation', 'report', 'layout',
            'outreach', 'awareness', 'training materials'
        ]
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 0.15
        
        # Reference number confidence
        score += opportunity.get('reference_confidence', 0.0) * 0.2
        
        # Budget consideration
        budget = opportunity.get('budget')
        if budget:
            if 5000 <= budget <= 500000:  # Target range
                score += 0.2
            elif budget > 500000:  # High value but outside range
                score += 0.1
        
        # Deadline consideration (prefer opportunities with reasonable deadlines)
        days_until = opportunity.get('days_until_deadline')
        if days_until:
            if 7 <= days_until <= 60:  # Good timeframe
                score += 0.1
            elif days_until > 60:  # Long timeframe
                score += 0.05
        
        # IUCN is generally a good source, so add base score
        score += 0.1
        
        return min(score, 1.0)
    
    def _determine_priority(self, opportunity: Dict[str, Any]) -> str:
        """Determine priority level"""
        score = opportunity.get('relevance_score', 0.0)
        
        # IUCN opportunities are generally high quality
        if score >= 0.7:
            return 'Critical'
        elif score >= 0.5:
            return 'High'
        elif score >= 0.3:
            return 'Medium'
        else:
            return 'Low'
    
    def test_connection(self):
        """Test connection to IUCN website"""
        try:
            soup = self.get_page(self.tenders_url)
            return soup is not None
        except Exception as e:
            self.logger.error(f"IUCN connection test failed: {str(e)}")
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
            if not opportunity_url or opportunity_url == self.tenders_url:
                return None
                
            soup = self.get_page(opportunity_url)
            if not soup:
                return None
            
            # Extract detailed information
            details = {
                'full_description': '',
                'requirements': '',
                'contact_info': '',
                'documents': [],
                'submission_details': ''
            }
            
            # Extract full description
            content_div = soup.find(['div', 'section'], class_=lambda x: x and 'content' in x.lower())
            if content_div:
                details['full_description'] = content_div.get_text(strip=True)
            
            # Extract requirements
            req_section = soup.find(text=lambda text: text and 'requirement' in text.lower())
            if req_section:
                req_parent = req_section.find_parent()
                if req_parent:
                    details['requirements'] = req_parent.get_text(strip=True)
            
            # Extract contact information
            contact_section = soup.find(text=lambda text: text and 'contact' in text.lower())
            if contact_section:
                contact_parent = contact_section.find_parent()
                if contact_parent:
                    details['contact_info'] = contact_parent.get_text(strip=True)
            
            # Extract document links
            doc_links = soup.find_all('a', href=lambda x: x and any(
                ext in x.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
            ))
            
            for link in doc_links:
                details['documents'].append({
                    'title': link.get_text(strip=True),
                    'url': urljoin(self.base_url, link['href'])
                })
            
            # Extract submission details
            submission_section = soup.find(text=lambda text: text and 'submission' in text.lower())
            if submission_section:
                submission_parent = submission_section.find_parent()
                if submission_parent:
                    details['submission_details'] = submission_parent.get_text(strip=True)
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting IUCN opportunity details: {str(e)}")
            return None

