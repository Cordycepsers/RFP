"""
Devex-specific scraper for Proposaland opportunity monitoring system.
Handles Devex funding opportunities and business announcements.
"""

import os
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
        # Use a simpler endpoint and keep alternatives to try if blocked
        self.funding_url = "https://www.devex.com/funding"
        self.alt_urls = [
            "https://www.devex.com/funding/r",
            "https://www.devex.com/news",
        ]
        # Harden headers to avoid 406
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': self.base_url,
            'Connection': 'keep-alive',
        })
        # Optional Selenium usage
        self.use_browser = bool(int(os.environ.get("DEVEX_USE_BROWSER", str(config.get('scraper_configs', {}).get('devex', {}).get('use_headless', 0)))))
        self.force_browser = bool(int(os.environ.get("DEVEX_FORCE_BROWSER", "0")))
        self.cookies_cache_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".cache", "devex_cookies.json")
        os.makedirs(os.path.dirname(self.cookies_cache_path), exist_ok=True)
        # Session/auth cookie configuration
        self.session_cookie_name = os.environ.get("DEVEX_SESSION_COOKIE_NAME", "devex_session")
        self.extra_cookies_env = os.environ.get("DEVEX_EXTRA_COOKIES", "")
        
    def _warmup(self) -> None:
        try:
            # Hit the home page to establish cookies/session
            _ = self.session.get(self.base_url, timeout=self.timeout, allow_redirects=True)
        except Exception:
            pass

    def _devex_login(self) -> bool:
        """Attempt to login to Devex if env credentials are provided. Returns True on likely success."""
        # If a session cookie is provided, set it directly
        sess_cookie = os.environ.get("DEVEX_SESSION_COOKIE")
        if sess_cookie:
            try:
                # Set primary session cookie (supports custom name via DEVEX_SESSION_COOKIE_NAME)
                for domain in ["www.devex.com", ".devex.com"]:
                    try:
                        self.session.cookies.set(self.session_cookie_name, sess_cookie, domain=domain)
                    except Exception:
                        continue
                # Load extra cookies if provided as JSON (e.g., datadome, ua_session_id, dxvisa)
                try:
                    import json as _json
                    extras = _json.loads(self.extra_cookies_env) if self.extra_cookies_env else {}
                    if isinstance(extras, dict):
                        for k, v in extras.items():
                            for domain in ["www.devex.com", ".devex.com"]:
                                try:
                                    self.session.cookies.set(str(k), str(v), domain=domain)
                                except Exception:
                                    continue
                except Exception:
                    pass
                check = self.session.get(self.funding_url, timeout=self.timeout, allow_redirects=True)
                if check.ok:
                    return True
            except Exception:
                pass
        user = os.environ.get("DEVEX_USERNAME")
        pw = os.environ.get("DEVEX_PASSWORD")
        if not user or not pw:
            return False
        try:
            # 1) Get login page to establish cookies and extract CSRF token if present
            login_page_url = f"{self.base_url}/account/login"
            resp = self.session.get(login_page_url, timeout=self.timeout, allow_redirects=True)
            token = None
            try:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Common hidden token names
                for name in [
                    'authenticity_token', 'csrfmiddlewaretoken', 'csrf-token', 'csrf_token'
                ]:
                    hidden = soup.find('input', attrs={'name': name})
                    if hidden and hidden.get('value'):
                        token = hidden.get('value')
                        break
            except Exception:
                token = None

            # 2) Submit login form (endpoint/fields may vary; we try a common pattern)
            post_url_candidates = [
                f"{self.base_url}/session",
                f"{self.base_url}/account/login",
            ]
            form = {
                'username': user,
                'email': user,  # some forms accept email field
                'login': user,  # fallback field name
                'password': pw,
            }
            if token:
                # include token under common keys
                for k in ['authenticity_token', 'csrfmiddlewaretoken', 'csrf-token', 'csrf_token']:
                    form[k] = token

            headers = {
                'Referer': login_page_url,
                'Origin': self.base_url,
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            ok = False
            for post_url in post_url_candidates:
                try:
                    r = self.session.post(post_url, data=form, headers=headers, timeout=self.timeout, allow_redirects=True)
                    if r.ok:
                        ok = True
                        break
                except Exception:
                    continue

            if not ok:
                return False

            # 3) Verify by fetching funding page
            check = self.session.get(self.funding_url, timeout=self.timeout, allow_redirects=True)
            return check.ok
        except Exception as e:
            logger.warning(f"Devex login attempt failed: {e}")
            return False
        
    def scrape_opportunities(self) -> List[OpportunityData]:
        """Scrape opportunities from Devex."""
        opportunities = []
        
        try:
            # Try login if credentials provided; otherwise warm up session
            logged_in = self._devex_login()
            if not logged_in:
                self._warmup()
            
            # Prepare URLs to try
            urls_to_try = [self.funding_url] + self.alt_urls
            soup = None
            # If forced, try Selenium first
            if self.force_browser and self.use_browser:
                for url in urls_to_try:
                    soup = self._browser_get_soup(url)
                    if soup:
                        break
            # Otherwise, try HTTP first
            if not soup:
                for url in urls_to_try:
                    soup = self.get_page(url, timeout=self.timeout)
                    if soup:
                        break
            # If still blocked, try Selenium fallback (cookie cache aware)
            if not soup and self.use_browser:
                for url in urls_to_try:
                    soup = self._browser_get_soup(url)
                    if soup:
                        break
            if not soup and not logged_in:
                # If still blocked, try logging in once and retry
                if self._devex_login():
                    for url in urls_to_try:
                        soup = self.get_page(url, timeout=self.timeout)
                        if soup:
                            break
                    if not soup and self.use_browser:
                        for url in urls_to_try:
                            soup = self._browser_get_soup(url)
                            if soup:
                                break
            if not soup:
                logger.error("Failed to access any Devex endpoint (funding/news)")
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

    # ---------------- Selenium helpers ----------------
    def _browser_get_soup(self, url: str) -> Optional[BeautifulSoup]:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            import json
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(f"--user-agent={self.session.headers.get('User-Agent')}")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(self.timeout)
            # Load cached cookies if present and apply env cookies
            try:
                driver.get(self.base_url)
                # Apply cached cookies first
                try:
                    if os.path.exists(self.cookies_cache_path):
                        with open(self.cookies_cache_path, 'r') as f:
                            cookies = json.load(f)
                        for c in cookies:
                            # selenium requires domain without leading dot
                            if isinstance(c, dict):
                                c = c.copy()
                                if c.get('domain', '').startswith('.'):
                                    c['domain'] = c['domain'][1:]
                                try:
                                    driver.add_cookie(c)
                                except Exception:
                                    continue
                except Exception:
                    pass
                # Apply env-provided cookies (session and extras)
                try:
                    # Primary session cookie
                    sess_cookie = os.environ.get("DEVEX_SESSION_COOKIE")
                    if sess_cookie:
                        try:
                            driver.add_cookie({
                                'name': self.session_cookie_name,
                                'value': sess_cookie,
                                'domain': 'www.devex.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
                    # Extra cookies JSON
                    try:
                        extras = json.loads(self.extra_cookies_env) if self.extra_cookies_env else {}
                        if isinstance(extras, dict):
                            for k, v in extras.items():
                                try:
                                    driver.add_cookie({
                                        'name': str(k),
                                        'value': str(v),
                                        'domain': 'www.devex.com',
                                        'path': '/'
                                    })
                                except Exception:
                                    continue
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                pass
            # Navigate to target URL
            driver.get(url)
            
            # Wait for DOM ready and attempt to wait for likely results to render
            try:
                import time as _time
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                # Wait for document ready
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                # Try to accept cookie banners if present (best-effort)
                for sel in [
                    '#onetrust-accept-btn-handler',
                    'button[aria-label*="Accept"]',
                    'button[aria-label*="accept"]',
                    'button:contains("Accept")',
                ]:
                    try:
                        elems = driver.find_elements(By.CSS_SELECTOR, sel)
                        if elems:
                            elems[0].click()
                            _time.sleep(0.5)
                            break
                    except Exception:
                        continue
                # Scroll to trigger lazy load
                for y in [500, 1500, 3000]:
                    try:
                        driver.execute_script("window.scrollTo(0, arguments[0]);", y)
                        _time.sleep(0.8)
                    except Exception:
                        break
                # Wait for presence of likely result containers
                likely_selectors = [
                    'div[class*="result"]',
                    'div[class*="fund"]',
                    'article',
                    'a[href*="/funding/"]',
                ]
                for sel in likely_selectors:
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                        )
                        break
                    except Exception:
                        continue
            except Exception:
                pass
            
            html = driver.page_source
            # Save cookies back to cache
            try:
                cookies = driver.get_cookies()
                with open(self.cookies_cache_path, 'w') as f:
                    json.dump(cookies, f)
            except Exception:
                pass
            driver.quit()
            return BeautifulSoup(html, 'html.parser') if html else None
        except Exception as e:
            logger.warning(f"Selenium fallback failed for Devex: {e}")
            try:
                driver.quit()
            except Exception:
                pass
            return None


class DevexScraperFixed(DevexScraper):
    """Backward-compatible adapter expected by proposaland_monitor.py."""
    pass

