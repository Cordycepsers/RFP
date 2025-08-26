"""
Enhanced Devex scraper using Playwright MCP patterns for comprehensive keyword-based opportunity discovery.
Based on successful manual exploration patterns from August 2025.
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from loguru import logger

from .base_scraper import BaseScraper, OpportunityData


class DevexPlaywrightScraper(BaseScraper):
    """
    Enhanced Devex scraper using Playwright MCP automation patterns.
    Systematically searches through multimedia and communication keywords.
    """
    
    def __init__(self, config, website_config):
        super().__init__(config, website_config)
        self.base_url = "https://www.devex.com"
        self.funding_search_url = "https://www.devex.com/funding/r"
        
        # Keywords from user specification
        self.keywords = [
            "video", "photo", "film", "multimedia", "design", "visual",
            "campaign", "podcasts", "virtual event", "media", "animation", 
            "animated video", "promotion", "communication", "audiovisual"
        ]
        
        # Search configuration based on successful manual patterns
        self.search_config = {
            "filters": {
                "type": ["tender", "grant"],  # Tenders & Grants
                "statuses": ["forecast", "open"],  # Forecast, Open
                "time_filter": "last_week"  # Last week filter
            },
            "max_results_per_keyword": 50,
            "document_download": True
        }
        
    def scrape_opportunities(self) -> List[OpportunityData]:
        """
        Scrape opportunities using systematic keyword search approach.
        """
        all_opportunities = []
        
        try:
            # Import MCP tools if available
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                # Process each keyword systematically
                for keyword in self.keywords:
                    logger.info(f"Searching Devex for keyword: {keyword}")
                    opportunities = self._search_keyword_opportunities(page, keyword)
                    all_opportunities.extend(opportunities)
                    
                browser.close()
                
        except ImportError:
            logger.warning("Playwright not available, falling back to requests-based scraping")
            all_opportunities = self._fallback_scraping()
        except Exception as e:
            logger.error(f"Error in Playwright scraping: {e}")
            all_opportunities = self._fallback_scraping()
        
        # Deduplicate and filter
        unique_opportunities = self._deduplicate_opportunities(all_opportunities)
        relevant_opportunities = [opp for opp in unique_opportunities if self.is_relevant_opportunity(opp)]
        
        logger.info(f"Found {len(relevant_opportunities)} relevant opportunities from Devex")
        return relevant_opportunities
    
    def _search_keyword_opportunities(self, page, keyword: str) -> List[OpportunityData]:
        """
        Search for opportunities using a specific keyword.
        Based on successful manual exploration patterns.
        """
        opportunities = []
        
        try:
            # Navigate to funding search page
            page.goto(self.funding_search_url, wait_until='domcontentloaded')
            page.wait_for_timeout(2000)  # Allow page to fully load
            
            # Enter keyword in search box
            search_box = page.locator('input[placeholder*="keywords"], input[placeholder*="agriculture"], textbox[placeholder*="keywords"]').first
            if search_box.is_visible():
                search_box.clear()
                search_box.fill(keyword)
            
            # Apply filters - Tenders & Grants
            try:
                tenders_grants_checkbox = page.locator('input[type="checkbox"]:near(text("Tenders & Grants"))').first
                if not tenders_grants_checkbox.is_checked():
                    tenders_grants_checkbox.check()
            except:
                pass
            
            # Apply additional filters via Filters button
            try:
                filters_button = page.locator('button:has-text("Filters")').first
                if filters_button.is_visible():
                    filters_button.click()
                    page.wait_for_timeout(1000)
                    
                    # Select Forecast and Open statuses
                    for status in ["Forecast", "Open"]:
                        status_checkbox = page.locator(f'input[type="checkbox"]:near(text("{status}"))').first
                        if status_checkbox.is_visible() and not status_checkbox.is_checked():
                            status_checkbox.check()
                    
                    # Apply time filter - Last week
                    last_week_option = page.locator('text("Last week"), text("7 days")').first
                    if last_week_option.is_visible():
                        last_week_option.click()
            except:
                pass
            
            # Execute search
            search_button = page.locator('button:has-text("Search"), button[type="submit"]').first
            if search_button.is_visible():
                search_button.click()
                page.wait_for_timeout(3000)  # Wait for results
            
            # Extract opportunities from results
            opportunities = self._extract_search_results(page, keyword)
            
        except Exception as e:
            logger.error(f"Error searching for keyword '{keyword}': {e}")
        
        return opportunities
    
    def _extract_search_results(self, page, keyword: str) -> List[OpportunityData]:
        """
        Extract opportunity data from search results page.
        """
        opportunities = []
        
        try:
            # Wait for results to load
            page.wait_for_selector('li[class*="listitem"], div[class*="opportunity"], article', timeout=10000)
            
            # Get all opportunity items (based on manual exploration patterns)
            opportunity_items = page.locator('li:has(heading), div:has(heading[level="4"])').all()
            
            for item in opportunity_items[:self.search_config["max_results_per_keyword"]]:
                try:
                    opportunity = self._parse_opportunity_item(page, item, keyword)
                    if opportunity:
                        opportunities.append(opportunity)
                except Exception as e:
                    logger.warning(f"Error parsing opportunity item: {e}")
                    continue
            
            # Handle pagination if available
            next_button = page.locator('text("next"), button:has-text("Next")').first
            if next_button.is_visible() and len(opportunities) < self.search_config["max_results_per_keyword"]:
                next_button.click()
                page.wait_for_timeout(2000)
                additional_opportunities = self._extract_search_results(page, keyword)
                opportunities.extend(additional_opportunities)
                
        except Exception as e:
            logger.error(f"Error extracting search results: {e}")
        
        return opportunities
    
    def _parse_opportunity_item(self, page, item, keyword: str) -> Optional[OpportunityData]:
        """
        Parse individual opportunity item with comprehensive data extraction.
        Extracts: title, funder, location, timeline, deadline, reference, description, contact, resources
        """
        try:
            opportunity = OpportunityData()
            opportunity.organization = "Devex"
            opportunity.source_keyword = keyword
            opportunity.date_found = datetime.now()
            
            # Extract Project Title (heading level 4 based on manual patterns)
            title_elem = item.locator('heading[level="4"], h4, h3, h2').first
            if title_elem.is_visible():
                opportunity.title = title_elem.text_content().strip()
            
            # Extract Funder (funding organization)
            funder_selectors = [
                'text("United Nations"), text("World Bank"), text("UNDP")',
                'generic:has-text("UN"), generic:has-text("UNICEF")',
                'generic:has-text("USAID"), generic:has-text("EU")'
            ]
            for selector in funder_selectors:
                funder_elem = item.locator(selector).first
                if funder_elem.is_visible():
                    opportunity.funding_organization = funder_elem.text_content().strip()
                    break
            
            # Extract Location
            location_elem = item.locator('generic:near(text("Location")), generic:has-text("Chad"), generic:has-text("Ethiopia")').first
            if location_elem.is_visible():
                location_text = location_elem.text_content().strip()
                # Apply geographic filters
                if self._is_location_allowed(location_text):
                    opportunity.location = location_text
                else:
                    return None  # Skip excluded locations
            
            # Extract Timeline - Published date and Deadline
            timeline_elem = item.locator('generic:has-text("days ago"), generic:has-text("hours ago")').first
            if timeline_elem.is_visible():
                opportunity.published_date = self._parse_published_date(timeline_elem.text_content())
            
            deadline_elem = item.locator('generic:has-text("2025"), text("Sep"), text("Aug")').first
            if deadline_elem.is_visible():
                deadline_text = deadline_elem.text_content().strip()
                opportunity.deadline = self._parse_deadline(deadline_text)
            
            # Extract Opportunity Type (Tender/Grant)
            type_elem = item.locator('text("Tender"), text("Grant")').first
            if type_elem.is_visible():
                opportunity.opportunity_type = type_elem.text_content().strip()
            
            # Get detail page URL and extract comprehensive information
            detail_link = item.locator('a[href*="/funding/"]').first
            if detail_link.is_visible():
                href = detail_link.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        href = self.base_url + href
                    opportunity.source_url = href
                    
                    # Extract comprehensive detailed information
                    self._extract_comprehensive_details(page, opportunity, href)
            
            # Extract keywords found
            all_text = f"{opportunity.title} {opportunity.description}"
            opportunity.keywords_found = self.extract_keywords(all_text)
            
            # Extract budget if mentioned
            opportunity.budget = self.extract_budget(all_text)
            
            return opportunity if opportunity.title else None
            
        except Exception as e:
            logger.error(f"Error parsing opportunity item: {e}")
            return None
    
    def _is_location_allowed(self, location: str) -> bool:
        """Check if location is allowed based on geographic filters."""
        location_lower = location.lower()
        
        # Check excluded countries
        excluded = ["india", "pakistan", "china", "bangladesh", "sri lanka", 
                   "myanmar", "thailand", "vietnam", "cambodia", "laos", 
                   "malaysia", "indonesia", "philippines", "singapore"]
        
        for excluded_country in excluded:
            if excluded_country in location_lower:
                return False
        
        # Allow Nepal specifically
        if "nepal" in location_lower:
            return True
            
        # Allow other non-Asian countries
        return True
    
    def _parse_published_date(self, text: str) -> Optional[datetime]:
        """Parse published date from 'X days ago' format."""
        try:
            import re
            match = re.search(r'(\d+)\s+(hours?|days?)\s+ago', text, re.IGNORECASE)
            if match:
                value, unit = match.groups()
                value = int(value)
                if 'hour' in unit.lower():
                    return datetime.now() - timedelta(hours=value)
                elif 'day' in unit.lower():
                    return datetime.now() - timedelta(days=value)
        except:
            pass
        return None
    
    def _extract_comprehensive_details(self, page, opportunity: OpportunityData, detail_url: str):
        """
        Extract comprehensive details: reference number, detailed description, 
        contact information, and resource links.
        """
        try:
            # Navigate to detail page
            page.goto(detail_url, wait_until='domcontentloaded')
            page.wait_for_timeout(2000)
            
            # Extract Reference Number
            ref_selectors = [
                'text("Reference Number"), text("Reference")',
                'text("UNDP-"), text("PRC"), text("Tender No")',
                'generic:has-text("REF:"), generic:has-text("ID:")'
            ]
            for selector in ref_selectors:
                ref_elem = page.locator(selector).first
                if ref_elem.is_visible():
                    ref_text = ref_elem.text_content()
                    opportunity.reference_number = self._extract_reference_number(ref_text)
                    break
            
            # Extract Detailed Description with Requirements
            desc_selectors = [
                'paragraph:has-text("Contexte"), paragraph:has-text("Project")',
                'paragraph:has-text("Description"), paragraph:has-text("Overview")',
                'generic:has-text("Objectif"), generic:has-text("Objective")',
                'paragraph:has-text("Requirements"), paragraph:has-text("Scope")'
            ]
            
            full_description = ""
            for selector in desc_selectors:
                desc_elems = page.locator(selector).all()
                for elem in desc_elems:
                    if elem.is_visible():
                        full_description += elem.text_content().strip() + "\n\n"
            
            if full_description:
                opportunity.description = full_description.strip()[:2000]  # Limit but keep comprehensive
            
            # Extract Contact Information
            contact_selectors = [
                'text("@"), link[href*="mailto:"]',
                'text("Contact"), text("Email")',
                'generic:has-text(".org"), generic:has-text(".com")'
            ]
            
            contacts = []
            for selector in contact_selectors:
                contact_elems = page.locator(selector).all()
                for elem in contact_elems:
                    if elem.is_visible():
                        contact_text = elem.text_content()
                        email = self._extract_email(contact_text)
                        if email and email not in contacts:
                            contacts.append(email)
                        # Also check href for mailto links
                        if elem.get_attribute('href'):
                            href = elem.get_attribute('href')
                            if href.startswith('mailto:'):
                                email = href.replace('mailto:', '')
                                if email not in contacts:
                                    contacts.append(email)
            
            opportunity.contact_email = "; ".join(contacts) if contacts else None
            
            # Extract Resource Links (submission portals & download files)
            resource_links = []
            link_selectors = [
                'link:has-text("Terms"), link:has-text("RFP")',
                'link:has-text("Document"), link:has-text("Download")',
                'link:has-text("Portal"), link:has-text("Submit")',
                'link:has-text("Quantum"), link:has-text("UNGM")'
            ]
            
            for selector in link_selectors:
                link_elems = page.locator(selector).all()
                for link in link_elems:
                    if link.is_visible():
                        href = link.get_attribute('href')
                        text = link.text_content().strip()
                        if href:
                            resource_links.append({
                                "title": text,
                                "url": href if href.startswith('http') else self.base_url + href,
                                "type": self._categorize_link(text, href)
                            })
            
            if resource_links:
                opportunity.documents_available = True
                opportunity.document_urls = [link["url"] for link in resource_links]
                opportunity.resource_links = resource_links
            
        except Exception as e:
            logger.error(f"Error extracting comprehensive details for {detail_url}: {e}")
    
    def _extract_reference_number(self, text: str) -> Optional[str]:
        """Extract reference number from text."""
        import re
        patterns = [
            r'(UNDP-[A-Z]+-\d+)',
            r'(PRC\d+)',
            r'(\d{6,})',
            r'(REF:\s*[A-Z0-9-]+)',
            r'(ID:\s*[A-Z0-9-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _categorize_link(self, text: str, url: str) -> str:
        """Categorize resource links."""
        text_lower = text.lower()
        url_lower = url.lower()
        
        if any(word in text_lower for word in ['terms', 'rfp', 'document']):
            return "document"
        elif any(word in text_lower for word in ['portal', 'submit', 'quantum', 'ungm']):
            return "submission_portal"
        elif any(ext in url_lower for ext in ['.pdf', '.doc', '.docx']):
            return "document"
        else:
            return "resource"
    
    def _extract_detailed_info(self, page, opportunity: OpportunityData, detail_url: str):
        """
        Extract detailed information from opportunity detail page.
        """
        try:
            # Navigate to detail page
            page.goto(detail_url, wait_until='domcontentloaded')
            page.wait_for_timeout(2000)
            
            # Extract description from detail page
            desc_selectors = [
                'paragraph:has-text("Contexte"), paragraph:has-text("Project")',
                'div:has-text("Description"), div:has-text("Overview")',
                'generic:has-text("Objectif"), generic:has-text("Objective")'
            ]
            
            for selector in desc_selectors:
                desc_elem = page.locator(selector).first
                if desc_elem.is_visible():
                    opportunity.description = desc_elem.text_content().strip()[:500]  # Limit description length
                    break
            
            # Extract contact information
            contact_elem = page.locator('text("@"), text("email"), generic:has-text(".org")').first
            if contact_elem.is_visible():
                opportunity.contact_email = self._extract_email(contact_elem.text_content())
            
            # Extract reference numbers
            ref_elem = page.locator('text("Reference"), text("UNDP-"), text("PRC")').first
            if ref_elem.is_visible():
                opportunity.reference_number = ref_elem.text_content().strip()
            
            # Check for downloadable documents
            doc_links = page.locator('link:has-text("Terms"), link:has-text("RFP"), link:has-text("Document")').all()
            if doc_links:
                opportunity.documents_available = True
                opportunity.document_urls = [link.get_attribute('href') for link in doc_links if link.get_attribute('href')]
            
        except Exception as e:
            logger.warning(f"Error extracting detailed info for {detail_url}: {e}")
    
    def _parse_deadline(self, deadline_text: str) -> Optional[datetime]:
        """Parse deadline from various text formats."""
        try:
            # Common patterns from manual exploration
            patterns = [
                r'(\d{1,2})\s+(Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',
                r'(\d{4})-(\d{2})-(\d{2})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, deadline_text, re.IGNORECASE)
                if match:
                    if 'Aug' in deadline_text or 'Sep' in deadline_text:
                        # Handle month name format
                        day, month_name, year = match.groups()
                        month_map = {'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                        month = month_map.get(month_name, 1)
                        return datetime(int(year), month, int(day))
                    else:
                        # Handle numeric formats
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
        """Remove duplicate opportunities based on title and organization."""
        seen = set()
        unique_opportunities = []
        
        for opp in opportunities:
            key = f"{opp.title}_{opp.funding_organization}_{opp.location}"
            if key not in seen:
                seen.add(key)
                unique_opportunities.append(opp)
        
        return unique_opportunities
    
    def _fallback_scraping(self) -> List[OpportunityData]:
        """Fallback to requests-based scraping if Playwright fails."""
        logger.info("Using fallback scraping method")
        opportunities = []
        
        try:
            # Basic requests-based scraping as fallback
            soup = self.get_page(self.funding_search_url)
            if soup:
                # Extract what we can from the static page
                opportunity_containers = soup.find_all(['div', 'article'], class_=re.compile(r'(opportunity|funding|tender)', re.I))
                
                for container in opportunity_containers[:20]:  # Limit to prevent overload
                    try:
                        opportunity = self._parse_static_container(container)
                        if opportunity:
                            opportunities.append(opportunity)
                    except Exception as e:
                        logger.warning(f"Error in fallback parsing: {e}")
                        continue
        except Exception as e:
            logger.error(f"Fallback scraping failed: {e}")
        
        return opportunities
    
    def _parse_static_container(self, container) -> Optional[OpportunityData]:
        """Parse opportunity from static HTML container."""
        opportunity = OpportunityData()
        opportunity.organization = "Devex"
        opportunity.source_url = self.funding_search_url
        opportunity.date_found = datetime.now()
        
        # Extract title
        title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
        if title_elem:
            opportunity.title = title_elem.get_text(strip=True)
        
        # Extract description
        desc_elem = container.find(['p', 'div'], class_=re.compile(r'(description|summary)', re.I))
        if desc_elem:
            opportunity.description = desc_elem.get_text(strip=True)[:300]
        
        # Extract link
        link_elem = container.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if href.startswith('/'):
                href = self.base_url + href
            opportunity.source_url = href
        
        # Extract keywords
        all_text = f"{opportunity.title} {opportunity.description}"
        opportunity.keywords_found = self.extract_keywords(all_text)
        
        return opportunity if opportunity.title else None
