"""
Devex-specific scraper for Proposaland opportunity monitoring system.
Handles Devex funding opportunities and business announcements.
"""

import re
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from loguru import logger

from .base_scraper import BaseScraper, OpportunityData


class DevexScraper(BaseScraper):
    """Scraper for Devex funding opportunities."""
    
    def __init__(self, config, website_config):
        super().__init__(config, website_config)
        self.base_url = "https://www.devex.com"
        self.funding_url = "https://www.devex.com/funding-overview"
        
    def scrape_opportunities(self) -> List[OpportunityData]:
        """Scrape opportunities from Devex."""
        opportunities = []
        
        try:
            # Try to access the funding overview page
            soup = self.get_page(self.funding_url)
            if not soup:
                logger.error("Failed to access Devex funding page")
                return opportunities
            
            # Look for funding opportunities in the page
            opportunities.extend(self._extract_funding_opportunities(soup))
            
            # Try to access news section for additional opportunities
            news_opportunities = self._scrape_news_section()
            opportunities.extend(news_opportunities)
            
        except Exception as e:
            logger.error(f"Error scraping Devex: {e}")
        
        # Filter relevant opportunities
        relevant_opportunities = [opp for opp in opportunities if self.is_relevant_opportunity(opp)]
        logger.info(f"Found {len(relevant_opportunities)} relevant opportunities from Devex")
        
        return relevant_opportunities
    
    def _extract_funding_opportunities(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Extract funding opportunities from the main funding page."""
        opportunities = []
        
        # Look for opportunity containers
        opportunity_containers = soup.find_all(['div', 'article'], class_=re.compile(r'(opportunity|funding|tender|grant)', re.I))
        
        for container in opportunity_containers:
            try:
                opportunity = self._parse_opportunity_container(container)
                if opportunity:
                    opportunities.append(opportunity)
            except Exception as e:
                logger.warning(f"Error parsing opportunity container: {e}")
                continue
        
        return opportunities
    
    def _parse_opportunity_container(self, container) -> Optional[OpportunityData]:
        """Parse an individual opportunity container."""
        opportunity = OpportunityData()
        opportunity.organization = "Devex"
        opportunity.source_url = self.funding_url
        
        # Extract title
        title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'(title|heading)', re.I))
        if not title_elem:
            title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
        
        if title_elem:
            opportunity.title = title_elem.get_text(strip=True)
        
        # Extract description
        desc_elem = container.find(['p', 'div'], class_=re.compile(r'(description|summary|content)', re.I))
        if desc_elem:
            opportunity.description = desc_elem.get_text(strip=True)
        
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
        
        # Extract budget if mentioned
        opportunity.budget = self.extract_budget(all_text)
        
        # Extract deadline if mentioned
        opportunity.deadline = self.extract_deadline(all_text)
        
        # Extract reference number
        opportunity.reference_number = self._extract_reference_number(all_text)
        if opportunity.reference_number:
            opportunity.reference_confidence = 0.8
        
        # Only return if we have meaningful content
        if opportunity.title or opportunity.description:
            return opportunity
        
        return None
    
    def _scrape_news_section(self) -> List[OpportunityData]:
        """Scrape news section for funding announcements."""
        opportunities = []
        
        try:
            news_url = f"{self.base_url}/news"
            soup = self.get_page(news_url)
            if not soup:
                return opportunities
            
            # Look for news articles that might contain funding opportunities
            articles = soup.find_all(['article', 'div'], class_=re.compile(r'(article|news|post)', re.I))
            
            for article in articles[:10]:  # Limit to first 10 articles
                try:
                    opportunity = self._parse_news_article(article)
                    if opportunity and opportunity.keywords_found:
                        opportunities.append(opportunity)
                except Exception as e:
                    logger.warning(f"Error parsing news article: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error scraping Devex news section: {e}")
        
        return opportunities
    
    def _parse_news_article(self, article) -> Optional[OpportunityData]:
        """Parse a news article for funding opportunities."""
        opportunity = OpportunityData()
        opportunity.organization = "Devex (News)"
        
        # Extract title
        title_elem = article.find(['h1', 'h2', 'h3'], class_=re.compile(r'(title|heading)', re.I))
        if not title_elem:
            title_elem = article.find(['h1', 'h2', 'h3'])
        
        if title_elem:
            opportunity.title = title_elem.get_text(strip=True)
        
        # Extract description/summary
        desc_elem = article.find(['p', 'div'], class_=re.compile(r'(summary|excerpt|description)', re.I))
        if desc_elem:
            opportunity.description = desc_elem.get_text(strip=True)
        
        # Extract link
        link_elem = article.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if href.startswith('/'):
                href = self.base_url + href
            opportunity.source_url = href
        
        # Extract keywords
        all_text = f"{opportunity.title} {opportunity.description}"
        opportunity.keywords_found = self.extract_keywords(all_text)
        
        # Only return if relevant keywords found
        if opportunity.keywords_found and (opportunity.title or opportunity.description):
            return opportunity
        
        return None
    
    def _extract_reference_number(self, text: str) -> str:
        """Extract reference number from text using Devex-specific patterns."""
        if not text:
            return ""
        
        # Devex-specific patterns
        patterns = [
            r'(?:RFP|RFQ|ITB|EOI)[:\s]*([A-Z0-9/-]+)',
            r'Reference[:\s]*([A-Z0-9/-]+)',
            r'Ref[:\s]*([A-Z0-9/-]+)',
            r'ID[:\s]*([A-Z0-9/-]+)',
            r'([A-Z]{2,4}/\d{4}/\d{3,4})',
            r'([A-Z]{2,4}-\d{4}-\d{3,4})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return ""

