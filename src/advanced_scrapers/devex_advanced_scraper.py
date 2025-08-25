"""
Advanced Devex scraper for hard-to-scrape funding opportunities.
Uses Playwright with MCP integration patterns for comprehensive data extraction.
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from loguru import logger

from .playwright_base_scraper import PlaywrightBaseScraper
from ..scrapers.base_scraper import OpportunityData


class DevexAdvancedScraper(PlaywrightBaseScraper):
    """
    Advanced Devex scraper using Playwright for comprehensive opportunity discovery.
    Handles all multimedia and communication keywords with advanced filtering.
    """
    
    def __init__(self, config, website_config):
        super().__init__(config, website_config)
        self.base_url = "https://www.devex.com"
        self.funding_search_url = "https://www.devex.com/funding/r"
        
        # Keywords from configuration
        self.keywords = config.get('keywords', {}).get('primary', [
            "video", "photo", "film", "multimedia", "design", "visual",
            "campaign", "podcasts", "virtual event", "media", "animation", 
            "animated video", "promotion", "communication", "audiovisual"
        ])
        
        # Geographic filters
        geographic_filters = config.get('geographic_filters', {})
        self.excluded_countries = geographic_filters.get('excluded_countries', [])
        self.included_countries = geographic_filters.get('included_countries', [])
        
        # Search configuration
        self.max_results_per_keyword = 25
        self.search_time_filter = "last_week"
    
    def search_keywords(self, keywords: List[str]) -> List[OpportunityData]:
        """Search for opportunities using all specified keywords."""
        all_opportunities = []
        
        for keyword in self.keywords:
            logger.info(f"Searching Devex for keyword: {keyword}")
            
            try:
                opportunities = self._search_single_keyword(keyword)
                logger.info(f"Found {len(opportunities)} opportunities for '{keyword}'")
                all_opportunities.extend(opportunities)
                
                # Human-like delay between keyword searches
                self._human_like_delay(3, 6)
                
            except Exception as e:
                logger.error(f"Error searching keyword '{keyword}': {e}")
                self._notify_error(f"Keyword search failed for '{keyword}': {str(e)}")
                continue
        
        # Deduplicate opportunities
        unique_opportunities = self._deduplicate_opportunities(all_opportunities)
        logger.info(f"Total unique opportunities found: {len(unique_opportunities)}")
        
        return unique_opportunities
    
    def _search_single_keyword(self, keyword: str) -> List[OpportunityData]:
        """Search for opportunities with a single keyword."""
        opportunities = []
        
        # Navigate to funding search page
        if not self.navigate_with_retry(self.funding_search_url):
            logger.error(f"Failed to navigate to Devex funding page for keyword: {keyword}")
            return opportunities
        
        # Enter keyword in search box
        if not self._enter_search_keyword(keyword):
            logger.error(f"Failed to enter keyword: {keyword}")
            return opportunities
        
        # Apply filters
        if not self._apply_search_filters():
            logger.warning("Failed to apply some search filters")
        
        # Execute search
        if not self._execute_search():
            logger.error(f"Failed to execute search for keyword: {keyword}")
            return opportunities
        
        # Extract opportunities from results
        opportunities = self._extract_search_results(keyword)
        
        return opportunities
    
    def _enter_search_keyword(self, keyword: str) -> bool:
        """Enter keyword in the search box."""
        search_selectors = [
            'input[placeholder*="keywords"]',
            'input[placeholder*="agriculture"]',
            'textbox[name*="query"]',
            'input[name*="search"]'
        ]
        
        for selector in search_selectors:
            if self._safe_fill(selector, keyword):
                logger.debug(f"Successfully entered keyword '{keyword}' using selector: {selector}")
                return True
        
        logger.error(f"Could not find search box to enter keyword: {keyword}")
        return False
    
    def _apply_search_filters(self) -> bool:
        """Apply search filters based on configuration."""
        success = True
        
        # Apply Tenders & Grants filter
        if not self._apply_opportunity_type_filter():
            success = False
        
        # Apply status filters (Open, Forecast)
        if not self._apply_status_filters():
            success = False
        
        # Apply time filter (Last week)
        if not self._apply_time_filter():
            success = False
        
        return success
    
    def _apply_opportunity_type_filter(self) -> bool:
        """Apply Tenders & Grants filter."""
        try:
            # Look for Tenders & Grants checkbox
            tenders_selectors = [
                'input[type="checkbox"]:near(:text("Tenders & Grants"))',
                'checkbox[value*="tender"]',
                'input[name*="type"][value*="tender"]'
            ]
            
            for selector in tenders_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible() and not element.is_checked():
                        element.check()
                        self._human_like_delay(0.5, 1.0)
                        logger.debug("Applied Tenders & Grants filter")
                        return True
                except:
                    continue
            
            logger.warning("Could not find or apply Tenders & Grants filter")
            return False
            
        except Exception as e:
            logger.error(f"Error applying opportunity type filter: {e}")
            return False
    
    def _apply_status_filters(self) -> bool:
        """Apply Open and Forecast status filters."""
        try:
            # Open Filters panel if needed
            filters_button = self.page.locator('button:has-text("Filters")').first
            if filters_button.is_visible():
                filters_button.click()
                self._human_like_delay(1, 2)
            
            # Apply Open status
            open_selectors = [
                'input[type="checkbox"]:near(:text("Open"))',
                'checkbox[value*="open"]'
            ]
            
            for selector in open_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible() and not element.is_checked():
                        element.check()
                        self._human_like_delay(0.3, 0.7)
                        break
                except:
                    continue
            
            # Apply Forecast status  
            forecast_selectors = [
                'input[type="checkbox"]:near(:text("Forecast"))',
                'checkbox[value*="forecast"]'
            ]
            
            for selector in forecast_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible() and not element.is_checked():
                        element.check()
                        self._human_like_delay(0.3, 0.7)
                        break
                except:
                    continue
            
            logger.debug("Applied status filters (Open, Forecast)")
            return True
            
        except Exception as e:
            logger.error(f"Error applying status filters: {e}")
            return False
    
    def _apply_time_filter(self) -> bool:
        """Apply time filter for last week."""
        try:
            time_selectors = [
                ':text("Last week")',
                ':text("7 days")',
                'select[name*="time"] option[value*="week"]'
            ]
            
            for selector in time_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        element.click()
                        self._human_like_delay(0.5, 1.0)
                        logger.debug("Applied last week time filter")
                        return True
                except:
                    continue
            
            logger.warning("Could not apply time filter")
            return False
            
        except Exception as e:
            logger.error(f"Error applying time filter: {e}")
            return False
    
    def _execute_search(self) -> bool:
        """Execute the search."""
        search_button_selectors = [
            'button:has-text("Search")',
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has(:text("Go"))'
        ]
        
        for selector in search_button_selectors:
            if self._safe_click(selector):
                # Wait for search results to load
                self._wait_for_network_idle(15000)
                self._human_like_delay(3, 5)
                logger.debug("Search executed successfully")
                return True
        
        logger.error("Could not find or click search button")
        return False
    
    def _extract_search_results(self, keyword: str) -> List[OpportunityData]:
        """Extract opportunities from search results."""
        opportunities = []
        
        try:
            # Wait for results to load
            self.page.wait_for_selector('li, div[class*="opportunity"], article', timeout=15000)
            
            # Extract opportunities from current page
            page_opportunities = self._extract_page_opportunities(keyword)
            opportunities.extend(page_opportunities)
            
            # Handle pagination if needed
            if len(opportunities) < self.max_results_per_keyword:
                paginated_opportunities = self._handle_pagination(keyword)
                opportunities.extend(paginated_opportunities)
            
        except Exception as e:
            logger.error(f"Error extracting search results: {e}")
        
        return opportunities[:self.max_results_per_keyword]
    
    def _extract_page_opportunities(self, keyword: str) -> List[OpportunityData]:
        """Extract opportunities from current page."""
        opportunities = []
        
        # Find opportunity containers based on manual exploration patterns
        opportunity_selectors = [
            'li:has(heading[level="4"])',
            'listitem:has(h4)',
            'div:has(h3):has(:text("Tender"))',
            'article:has(:text("Grant"))'
        ]
        
        opportunity_elements = []
        for selector in opportunity_selectors:
            try:
                elements = self.page.locator(selector).all()
                opportunity_elements.extend(elements)
                if elements:
                    break  # Use first successful selector
            except:
                continue
        
        logger.info(f"Found {len(opportunity_elements)} opportunity elements on page")
        
        for element in opportunity_elements:
            try:
                opportunity = self._parse_opportunity_element(element, keyword)
                if opportunity and self._is_geographically_relevant(opportunity):
                    opportunities.append(opportunity)
            except Exception as e:
                logger.warning(f"Error parsing opportunity element: {e}")
                continue
        
        return opportunities
    
    def _parse_opportunity_element(self, element, keyword: str) -> Optional[OpportunityData]:
        """Parse individual opportunity element."""
        opportunity = OpportunityData()
        opportunity.organization = "Devex"
        opportunity.source_keyword = keyword
        opportunity.date_found = datetime.now()
        
        try:
            # Extract title
            title_selectors = ['heading[level="4"]', 'h4', 'h3', 'h2']
            for selector in title_selectors:
                title_elem = element.locator(selector).first
                if title_elem.is_visible():
                    opportunity.title = title_elem.text_content().strip()
                    break
            
            if not opportunity.title:
                return None
            
            # Extract funding organization
            org_patterns = [
                ':text("United Nations")', ':text("UNDP")', ':text("World Bank")',
                ':text("USAID")', ':text("EU")', ':text("ADB")', 'generic:has-text("UN")'
            ]
            
            for pattern in org_patterns:
                org_elem = element.locator(pattern).first
                if org_elem.is_visible():
                    opportunity.funding_organization = org_elem.text_content().strip()
                    break
            
            # Extract location
            location_elem = element.locator('generic:near(:text("Location")), :text("Chad"), :text("Ethiopia"), :text("Iraq")').first
            if location_elem.is_visible():
                opportunity.location = location_elem.text_content().strip()
            
            # Extract deadline
            deadline_elem = element.locator(':text("2025"), :text("Sep"), :text("Aug"), :text("Oct")').first
            if deadline_elem.is_visible():
                deadline_text = deadline_elem.text_content().strip()
                opportunity.deadline = self._parse_deadline(deadline_text)
            
            # Extract opportunity type
            type_elem = element.locator(':text("Tender"), :text("Grant"), :text("RFP")').first
            if type_elem.is_visible():
                opportunity.opportunity_type = type_elem.text_content().strip()
            
            # Get detail page URL
            link_elem = element.locator('a[href*="/funding/"]').first
            if link_elem.is_visible():
                href = link_elem.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        href = self.base_url + href
                    opportunity.source_url = href
                    
                    # Extract detailed information
                    self._extract_detailed_information(opportunity, href)
            
            # Extract keywords found
            all_text = f"{opportunity.title} {opportunity.description}"
            opportunity.keywords_found = self.extract_keywords(all_text)
            
            # Extract budget
            opportunity.budget = self.extract_budget(all_text)
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error parsing opportunity element: {e}")
            return None
    
    def _extract_detailed_information(self, opportunity: OpportunityData, detail_url: str):
        """Extract detailed information from opportunity detail page."""
        try:
            # Open detail page in new tab to preserve search results
            detail_page = self.context.new_page()
            
            try:
                detail_page.goto(detail_url, timeout=20000, wait_until='domcontentloaded')
                detail_page.wait_for_timeout(2000)
                
                # Extract detailed description
                desc_selectors = [
                    'paragraph:has-text("Contexte")',
                    'paragraph:has-text("Project")',
                    'div:has-text("Description")',
                    'generic:has-text("Objectif")'
                ]
                
                for selector in desc_selectors:
                    desc_elem = detail_page.locator(selector).first
                    if desc_elem.is_visible():
                        description = desc_elem.text_content().strip()
                        opportunity.description = description[:800]  # Limit length
                        break
                
                # Extract contact information
                contact_elem = detail_page.locator(':text("@"), generic:has-text(".org")').first
                if contact_elem.is_visible():
                    contact_text = contact_elem.text_content()
                    opportunity.contact_email = self._extract_email(contact_text)
                
                # Extract reference numbers
                ref_elem = detail_page.locator(':text("Reference"), :text("UNDP-"), :text("PRC")').first
                if ref_elem.is_visible():
                    opportunity.reference_number = ref_elem.text_content().strip()
                
                # Extract document links
                doc_links = detail_page.locator('link:has-text("Terms"), link:has-text("RFP"), link:has-text("Document")').all()
                if doc_links:
                    opportunity.documents_available = True
                    opportunity.document_urls = []
                    for link in doc_links:
                        href = link.get_attribute('href')
                        if href:
                            if href.startswith('/'):
                                href = self.base_url + href
                            opportunity.document_urls.append(href)
                
                # Extract submission portal links
                portal_links = detail_page.locator('link:has-text("Portal"), link:has-text("Submit"), link:has-text("Quantum")').all()
                if portal_links:
                    opportunity.submission_portals = []
                    for link in portal_links:
                        href = link.get_attribute('href')
                        if href:
                            opportunity.submission_portals.append(href)
                
            finally:
                detail_page.close()
                
        except Exception as e:
            logger.warning(f"Error extracting detailed info for {detail_url}: {e}")
    
    def _handle_pagination(self, keyword: str) -> List[OpportunityData]:
        """Handle pagination to get more results."""
        opportunities = []
        
        try:
            # Look for next button
            next_selectors = [
                ':text("next")',
                'button:has-text("Next")',
                'a:has-text(">")',
                'button:has(:text("2"))'
            ]
            
            for selector in next_selectors:
                next_btn = self.page.locator(selector).first
                if next_btn.is_visible():
                    next_btn.click()
                    self._wait_for_network_idle()
                    self._human_like_delay(2, 4)
                    
                    # Extract opportunities from next page
                    page_opportunities = self._extract_page_opportunities(keyword)
                    opportunities.extend(page_opportunities)
                    break
                    
        except Exception as e:
            logger.debug(f"Pagination handling error: {e}")
        
        return opportunities
    
    def _is_geographically_relevant(self, opportunity: OpportunityData) -> bool:
        """Check if opportunity is geographically relevant based on filters."""
        if not opportunity.location:
            return True  # Include if location unknown
        
        location_lower = opportunity.location.lower()
        
        # Check excluded countries
        for excluded in self.excluded_countries:
            if excluded.lower() in location_lower:
                logger.debug(f"Excluding opportunity in {opportunity.location} (excluded country)")
                return False
        
        # Check included countries (if specified)
        if self.included_countries:
            for included in self.included_countries:
                if included.lower() in location_lower:
                    return True
            logger.debug(f"Excluding opportunity in {opportunity.location} (not in included countries)")
            return False
        
        return True
    
    def _parse_deadline(self, deadline_text: str) -> Optional[datetime]:
        """Parse deadline from various text formats."""
        try:
            patterns = [
                r'(\d{1,2})\s+(Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',
                r'(\d{4})-(\d{2})-(\d{2})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, deadline_text, re.IGNORECASE)
                if match:
                    if any(month in deadline_text for month in ['Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                        day, month_name, year = match.groups()
                        month_map = {'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                        month = month_map.get(month_name, 1)
                        return datetime(int(year), month, int(day))
                    else:
                        parts = match.groups()
                        if len(parts) == 3:
                            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        except:
            pass
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group() if match else None
    
    def _deduplicate_opportunities(self, opportunities: List[OpportunityData]) -> List[OpportunityData]:
        """Remove duplicate opportunities."""
        seen = set()
        unique_opportunities = []
        
        for opp in opportunities:
            # Create unique key based on title, organization, and location
            key = f"{opp.title}_{opp.funding_organization}_{opp.location}"
            if key not in seen:
                seen.add(key)
                unique_opportunities.append(opp)
        
        return unique_opportunities
    
    def _parse_basic_opportunities(self, soup) -> List[OpportunityData]:
        """Fallback parsing for basic scraping."""
        opportunities = []
        
        try:
            # Basic HTML parsing as fallback
            opportunity_containers = soup.find_all(['div', 'article'], class_=re.compile(r'(opportunity|funding)', re.I))
            
            for container in opportunity_containers[:10]:
                opportunity = OpportunityData()
                opportunity.organization = "Devex"
                opportunity.date_found = datetime.now()
                
                # Extract title
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                if title_elem:
                    opportunity.title = title_elem.get_text(strip=True)
                
                # Extract description
                desc_elem = container.find(['p', 'div'])
                if desc_elem:
                    opportunity.description = desc_elem.get_text(strip=True)[:300]
                
                # Extract link
                link_elem = container.find('a', href=True)
                if link_elem:
                    href = link_elem['href']
                    if href.startswith('/'):
                        href = self.base_url + href
                    opportunity.source_url = href
                
                if opportunity.title:
                    opportunities.append(opportunity)
                    
        except Exception as e:
            logger.error(f"Error in fallback parsing: {e}")
        
        return opportunities
