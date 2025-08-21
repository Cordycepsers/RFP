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
    def _login_with_browser(self, driver, username: str, password: str, timeout: int = 30) -> bool:
        """Automate login to Devex using Selenium."""
        try:
            driver.get("https://www.devex.com/account/login")
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.NAME, "email")))
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            email_input.clear()
            email_input.send_keys(username)
            password_input.clear()
            password_input.send_keys(password)
            submit_btn = driver.find_element(By.XPATH, '//button[@type="submit"]')
            submit_btn.click()
            # Wait for login to complete (profile icon or redirect)
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/profile']")))
            return True
        except Exception as e:
            logger.error(f"Devex login automation failed: {e}")
            return False
    """Scraper for Devex funding opportunities."""
    
    def __init__(self, config, website_config):
        super().__init__(config, website_config)
        self.base_url = "https://www.devex.com"
        self.funding_url = "https://www.devex.com/funding/r"
        
    def scrape_opportunities(self) -> List[OpportunityData]:
        """Scrape opportunities from Devex, using browser automation if needed."""
        opportunities = []
        try:
            # Try to access the funding overview page (requests first)
            soup = self.get_page(self.funding_url)
            if not soup or not soup.find('body'):
                logger.warning("Devex funding page not accessible or empty, trying Selenium browser automation.")
                soup = self._get_page_with_browser(self.funding_url)
                if not soup:
                    logger.warning("Selenium failed, trying Playwright browser automation.")
                    try:
                        import asyncio
                        soup = asyncio.run(self._get_page_with_playwright(self.funding_url))
                    except Exception as e:
                        logger.error(f"Playwright fallback failed: {e}")
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

    def _get_page_with_browser(self, url: str, timeout: int = 30) -> Optional[BeautifulSoup]:
        """Fetch a page using Selenium browser automation with login if credentials are provided."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            chrome_options = Options()
            # chrome_options.add_argument('--headless')  # Run in visible mode for anti-bot bypass
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--window-size=1920,1080')
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
            driver.set_page_load_timeout(timeout)
            # Check for credentials in config
            creds = self.config.get('devex_credentials', {})
            username = creds.get('username')
            password = creds.get('password')
            if username and password:
                logger.info("Attempting Devex login automation...")
                logged_in = self._login_with_browser(driver, username, password, timeout)
                if not logged_in:
                    driver.quit()
                    return None
            driver.get(url)
            WebDriverWait(driver, min(timeout, 20)).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            html = driver.page_source
            driver.quit()
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"Selenium browser automation failed for Devex: {e}")
            return None
    
    async def _get_page_with_playwright(self, url: str, timeout: int = 30) -> Optional[BeautifulSoup]:
        """Fetch a page using Playwright with stealth and login if credentials are provided."""
        try:
            from playwright.async_api import async_playwright
            import playwright_stealth
            creds = self.config.get('devex_credentials', {})
            username = creds.get('username')
            password = creds.get('password')
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                await playwright_stealth.stealth_async(context)
                page = await context.new_page()
                if username and password:
                    await page.goto("https://www.devex.com/account/login", timeout=timeout*1000)
                    await page.fill('input[name="email"]', username)
                    await page.fill('input[name="password"]', password)
                    await page.click('button[type="submit"]')
                    await page.wait_for_selector("a[href*='/profile']", timeout=timeout*1000)
                await page.goto(url, timeout=timeout*1000)
                await page.wait_for_selector('body', timeout=timeout*1000)
                html = await page.content()
                await browser.close()
                return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"Playwright browser automation failed for Devex: {e}")
            return None
    
    def _extract_funding_opportunities(self, soup: BeautifulSoup) -> List[OpportunityData]:
        """Extract funding opportunities from the main funding page."""
        opportunities = []
        opportunity_containers = soup.find_all(['div', 'article'], class_=re.compile(r'(opportunity|funding|tender|grant)', re.I))
        logger.debug(f"Devex: Found {len(opportunity_containers)} opportunity containers on funding page.")
        if opportunity_containers:
            logger.debug(f"Devex: First container HTML: {opportunity_containers[0].prettify()[:1000]}")
        else:
            logger.debug("Devex: No opportunity containers found. Dumping funding page HTML.")
            logger.debug(soup.prettify()[:2000])
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