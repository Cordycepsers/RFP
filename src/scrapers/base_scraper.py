"""
Base scraper class for Proposaland opportunity monitoring system.
Provides common functionality for all website-specific scrapers.
"""

import requests
import time
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from loguru import logger
import re
import sys
import os

# Add parent directory to path to import reference extractor
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from reference_number_extractor import ReferenceNumberExtractor


class OpportunityData:
    """Data structure for storing opportunity information."""
    
    def __init__(self):
        self.title: str = ""
        self.description: str = ""
        self.organization: str = ""
        self.source_url: str = ""
        self.deadline: Optional[datetime] = None
        self.budget: Optional[float] = None
        self.currency: str = "USD"
        self.location: str = ""
        self.reference_number: str = ""
        self.reference_confidence: float = 0.0
        self.keywords_found: List[str] = []
        self.raw_data: Dict[str, Any] = {}
        self.extracted_date: datetime = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert opportunity data to dictionary format."""
        return {
            "title": self.title,
            "description": self.description,
            "organization": self.organization,
            "source_url": self.source_url,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "budget": self.budget,
            "currency": self.currency,
            "location": self.location,
            "reference_number": self.reference_number,
            "reference_confidence": self.reference_confidence,
            "keywords_found": self.keywords_found,
            "extracted_date": self.extracted_date.isoformat(),
            "raw_data": self.raw_data
        }


class BaseScraper(ABC):
    """Abstract base class for all website scrapers."""
    
    def __init__(self, config: Dict[str, Any], website_config: Dict[str, Any]):
        self.config = config
        self.website_config = website_config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.keywords = config.get('keywords', {}).get('primary', [])
        self.exclusion_keywords = config.get('keywords', {}).get('exclusions', [])
        self.max_retries = 3
        self.retry_delay = 2
        self.reference_extractor = ReferenceNumberExtractor()
        
    def get_page(self, url: str, timeout: int = 30) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page with retry logic."""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                
                # Check if content is HTML
                content_type = response.headers.get('content-type', '').lower()
                if 'html' not in content_type:
                    logger.warning(f"Non-HTML content received from {url}")
                    return None
                
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
        
        return None
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract matching keywords from text."""
        if not text:
            return []
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def has_exclusion_keywords(self, text: str) -> bool:
        """Check if text contains exclusion keywords."""
        if not text:
            return False
        
        text_lower = text.lower()
        for exclusion in self.exclusion_keywords:
            if exclusion.lower() in text_lower:
                return True
        
        return False
    
    def extract_budget(self, text: str) -> Optional[float]:
        """Extract budget amount from text."""
        if not text:
            return None
        
        # Common budget patterns
        patterns = [
            r'(?:USD|US\$|\$)\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'([0-9,]+(?:\.[0-9]{2})?)\s*(?:USD|US\$|\$)',
            r'budget[:\s]*(?:USD|US\$|\$)?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'value[:\s]*(?:USD|US\$|\$)?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'amount[:\s]*(?:USD|US\$|\$)?\s*([0-9,]+(?:\.[0-9]{2})?)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Remove commas and convert to float
                    amount_str = matches[0].replace(',', '')
                    amount = float(amount_str)
                    return amount
                except ValueError:
                    continue
        
        return None
    
    def extract_reference_number_advanced(self, text: str, context: str = "") -> tuple[str, float]:
        """Extract reference number using advanced pattern recognition."""
        if not text:
            return "", 0.0
        
        # Use the advanced reference extractor
        best_match = self.reference_extractor.get_best_reference(text, context)
        
        if best_match:
            return best_match.reference_number, best_match.confidence
        else:
            return "", 0.0
    
    def extract_all_reference_numbers(self, text: str, context: str = "") -> List[Dict[str, Any]]:
        """Extract all potential reference numbers with confidence scores."""
        if not text:
            return []
        
        matches = self.reference_extractor.extract_reference_numbers(text, context)
        
        return [
            {
                'reference_number': match.reference_number,
                'confidence': match.confidence,
                'pattern_type': match.pattern_type,
                'organization_type': match.organization_type,
                'context': match.context
            }
            for match in matches
        ]
    
    def extract_deadline(self, text: str) -> Optional[datetime]:
        if not text:
            return None
        
        # Common date patterns
        patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                try:
                    # Try different date formats
                    for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%Y-%m-%d', 
                               '%d %b %Y', '%b %d, %Y', '%B %d, %Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except ValueError:
                    continue
        
        return None
    
    def is_relevant_opportunity(self, opportunity: OpportunityData) -> bool:
        """Check if opportunity meets basic relevance criteria."""
        # Check for keywords
        all_text = f"{opportunity.title} {opportunity.description}".lower()
        has_keywords = any(keyword.lower() in all_text for keyword in self.keywords)
        
        if not has_keywords:
            return False
        
        # Check for exclusions
        if self.has_exclusion_keywords(all_text):
            return False
        
        # Check geographic exclusions
        excluded_countries = self.config.get('geographic_filters', {}).get('excluded_countries', [])
        for country in excluded_countries:
            if country.lower() in opportunity.location.lower():
                return False
        
        # Check budget range
        if opportunity.budget:
            min_budget = self.config.get('budget_filters', {}).get('min_budget', 0)
            max_budget = self.config.get('budget_filters', {}).get('max_budget', float('inf'))
            if not (min_budget <= opportunity.budget <= max_budget):
                return False
        
        # Check deadline
        if opportunity.deadline:
            min_days = self.config.get('deadline_filters', {}).get('minimum_days', 0)
            days_until_deadline = (opportunity.deadline - datetime.now()).days
            if days_until_deadline < min_days:
                return False
        
        return True
    
    @abstractmethod
    def scrape_opportunities(self) -> List[OpportunityData]:
        """Scrape opportunities from the target website."""
        pass
    
    def get_website_name(self) -> str:
        """Get the name of the website being scraped."""
        return self.website_config.get('name', 'Unknown')
    
    def get_website_url(self) -> str:
        """Get the URL of the website being scraped."""
        return self.website_config.get('url', '')
    
    def get_priority(self) -> float:
        """Get the priority score for this website."""
        return self.website_config.get('priority', 0.5)

    def test_connection(self) -> bool:
        """Default lightweight connectivity check for scrapers.

        Performs a HEAD request to the website URL if available, falling back to
        a page fetch using get_page when necessary. Returns True when the site
        appears reachable (HTTP < 400 or valid parsed page).
        """
        url = self.get_website_url() or self.website_config.get('url', '')
        try:
            if url:
                # Prefer HEAD to minimize payload
                resp = self.session.head(url, timeout=8, allow_redirects=True)
                if resp.status_code < 400:
                    return True
            # Fallback: try a parsed GET
            page = self.get_page(url, timeout=15)
            return page is not None
        except Exception:
            return False

