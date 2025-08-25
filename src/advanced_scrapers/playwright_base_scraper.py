"""
Advanced Playwright-based scraper for hard-to-scrape websites.
Handles JavaScript-heavy sites, anti-bot protection, and complex interactions.
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from loguru import logger
import sys

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scrapers.base_scraper import BaseScraper, OpportunityData


class PlaywrightBaseScraper(BaseScraper):
    """
    Base class for advanced scrapers using Playwright for hard-to-scrape websites.
    """
    
    def __init__(self, config, website_config):
        super().__init__(config, website_config)
        self.playwright_available = False
        self.browser = None
        self.context = None
        self.page = None
        
        # Advanced scraping configuration
        self.stealth_mode = True
        self.human_like_delays = True
        self.retry_attempts = 3
        self.page_timeout = 30000
        
        # Initialize Playwright if available
        self._init_playwright()
    
    def _init_playwright(self):
        """Initialize Playwright browser automation."""
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
            self.playwright_available = True
            logger.info("Playwright initialized successfully")
        except ImportError:
            logger.warning("Playwright not available, falling back to requests")
            self.playwright_available = False
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            self.playwright_available = False
    
    def _setup_browser(self, headless: bool = True):
        """Setup browser with stealth configuration."""
        if not self.playwright_available:
            return False
        
        try:
            # Launch browser with stealth settings
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Faster loading
                    '--disable-javascript-harmony-shipping'
                ]
            )
            
            # Create context with realistic viewport and user agent
            self.context = self.browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Set additional headers
            self.context.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            })
            
            self.page = self.context.new_page()
            
            # Block unnecessary resources for faster loading
            self.page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            return False
    
    def _human_like_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add human-like delay between actions."""
        if self.human_like_delays:
            import random
            delay = random.uniform(min_seconds, max_seconds)
            time.sleep(delay)
    
    def _safe_click(self, selector: str, timeout: int = 10000) -> bool:
        """Safely click an element with retry logic."""
        if not self.page:
            return False
        
        for attempt in range(self.retry_attempts):
            try:
                element = self.page.wait_for_selector(selector, timeout=timeout)
                if element:
                    element.click()
                    self._human_like_delay(0.5, 1.5)
                    return True
            except Exception as e:
                logger.warning(f"Click attempt {attempt + 1} failed for {selector}: {e}")
                if attempt < self.retry_attempts - 1:
                    self._human_like_delay(2, 4)
        
        return False
    
    def _safe_fill(self, selector: str, text: str, timeout: int = 10000) -> bool:
        """Safely fill a text field with retry logic."""
        if not self.page:
            return False
        
        for attempt in range(self.retry_attempts):
            try:
                element = self.page.wait_for_selector(selector, timeout=timeout)
                if element:
                    element.clear()
                    self._human_like_delay(0.3, 0.8)
                    element.fill(text)
                    self._human_like_delay(0.5, 1.0)
                    return True
            except Exception as e:
                logger.warning(f"Fill attempt {attempt + 1} failed for {selector}: {e}")
                if attempt < self.retry_attempts - 1:
                    self._human_like_delay(2, 4)
        
        return False
    
    def _wait_for_network_idle(self, timeout: int = 10000):
        """Wait for network to be idle (no requests for 500ms)."""
        if self.page:
            try:
                self.page.wait_for_load_state('networkidle', timeout=timeout)
            except Exception as e:
                logger.warning(f"Network idle wait failed: {e}")
    
    def _extract_text_safely(self, selector: str, default: str = "") -> str:
        """Safely extract text from an element."""
        if not self.page:
            return default
        
        try:
            element = self.page.locator(selector).first
            if element.is_visible():
                return element.text_content().strip()
        except Exception as e:
            logger.debug(f"Text extraction failed for {selector}: {e}")
        
        return default
    
    def _extract_attribute_safely(self, selector: str, attribute: str, default: str = "") -> str:
        """Safely extract an attribute from an element."""
        if not self.page:
            return default
        
        try:
            element = self.page.locator(selector).first
            if element.is_visible():
                attr_value = element.get_attribute(attribute)
                return attr_value.strip() if attr_value else default
        except Exception as e:
            logger.debug(f"Attribute extraction failed for {selector}.{attribute}: {e}")
        
        return default
    
    def navigate_with_retry(self, url: str) -> bool:
        """Navigate to URL with retry logic."""
        if not self.page:
            if not self._setup_browser():
                return False
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Navigating to {url} (attempt {attempt + 1})")
                response = self.page.goto(url, timeout=self.page_timeout, wait_until='domcontentloaded')
                
                if response and response.status < 400:
                    self._wait_for_network_idle()
                    self._human_like_delay(2, 4)
                    return True
                else:
                    logger.warning(f"Navigation failed with status: {response.status if response else 'No response'}")
                    
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    self._human_like_delay(5, 10)
        
        return False
    
    def handle_pagination(self, next_button_selector: str, max_pages: int = 5) -> List[Any]:
        """Handle pagination with next button clicking."""
        all_items = []
        current_page = 1
        
        while current_page <= max_pages:
            logger.info(f"Processing page {current_page}")
            
            # Extract items from current page
            page_items = self._extract_page_items()
            all_items.extend(page_items)
            
            # Try to go to next page
            if current_page < max_pages:
                if not self._safe_click(next_button_selector):
                    logger.info("No more pages or next button not found")
                    break
                
                self._wait_for_network_idle()
                self._human_like_delay(2, 4)
            
            current_page += 1
        
        return all_items
    
    def _extract_page_items(self) -> List[Any]:
        """Override this method in subclasses to extract items from current page."""
        return []
    
    def apply_filters(self, filters: Dict[str, Any]) -> bool:
        """Apply search filters. Override in subclasses."""
        return True
    
    def search_keywords(self, keywords: List[str]) -> List[OpportunityData]:
        """Search for opportunities using keywords. Override in subclasses."""
        return []
    
    def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
    
    def scrape_opportunities(self) -> List[OpportunityData]:
        """
        Main scraping method. Override in subclasses.
        This base implementation provides error handling and notification.
        """
        opportunities = []
        
        try:
            if not self.playwright_available:
                logger.error("Playwright not available for advanced scraping")
                self._notify_error("Playwright initialization failed")
                return self._fallback_scraping()
            
            if not self._setup_browser():
                logger.error("Browser setup failed")
                self._notify_error("Browser setup failed")
                return self._fallback_scraping()
            
            # Get keywords from config
            keywords = self.config.get('keywords', {}).get('primary', [])
            
            # Search for opportunities
            opportunities = self.search_keywords(keywords)
            
            logger.info(f"Successfully scraped {len(opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            self._notify_error(f"Scraping error: {str(e)}")
            opportunities = self._fallback_scraping()
        
        finally:
            self.cleanup()
        
        return opportunities
    
    def _notify_error(self, error_message: str):
        """Notify about scraping errors."""
        try:
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "scraper": self.__class__.__name__,
                "website": self.website_config.get('name', 'Unknown'),
                "error": error_message
            }
            
            # Log to file
            error_log_path = "logs/scraper_errors.json"
            os.makedirs(os.path.dirname(error_log_path), exist_ok=True)
            
            errors = []
            if os.path.exists(error_log_path):
                try:
                    with open(error_log_path, 'r') as f:
                        errors = json.load(f)
                except:
                    pass
            
            errors.append(error_data)
            
            # Keep only last 100 errors
            errors = errors[-100:]
            
            with open(error_log_path, 'w') as f:
                json.dump(errors, f, indent=2)
            
            logger.error(f"Error notification saved: {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to save error notification: {e}")
    
    def _fallback_scraping(self) -> List[OpportunityData]:
        """Fallback to basic requests-based scraping."""
        logger.info("Using fallback scraping method")
        
        try:
            # Basic requests fallback
            soup = self.get_page(self.website_config.get('url', ''))
            if soup:
                return self._parse_basic_opportunities(soup)
        except Exception as e:
            logger.error(f"Fallback scraping also failed: {e}")
            self._notify_error(f"Both advanced and fallback scraping failed: {str(e)}")
        
        return []
    
    def _parse_basic_opportunities(self, soup) -> List[OpportunityData]:
        """Basic opportunity parsing for fallback. Override in subclasses."""
        return []
