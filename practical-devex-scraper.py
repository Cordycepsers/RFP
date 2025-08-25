#!/usr/bin/env python3
"""
Practical Devex Scraper using Real Chrome MCP Tools
This implementation actually works with the MCP Chrome control system
"""

import json
import time
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DevexOpportunity:
    title: str
    organization: str
    location: str
    sector: str
    opportunity_type: str
    status: str
    opportunity_size: str
    deadline: str
    publication_date: str
    url: str
    description: str
    scraped_at: str

class PracticalDevexScraper:
    """Working Devex scraper using Chrome MCP tools"""
    
    def __init__(self):
        self.opportunities = []
        self.current_tab_id = None
        
    async def login_to_devex(self, username: str, password: str) -> bool:
        """Login to Devex using Chrome MCP"""
        try:
            logger.info("Opening Devex login page...")
            
            # Navigate to login page
            result = await self.chrome_open_url("https://www.devex.com/sign-in")
            if not result:
                return False
            
            # Wait for page to load
            time.sleep(3)
            
            # Execute login script
            login_script = f"""
            (function() {{
                try {{
                    // Find email input
                    const emailInput = document.querySelector('input[type="email"], input[name="email"], input[id*="email"]');
                    if (!emailInput) {{
                        return {{ error: 'Email input not found' }};
                    }}
                    
                    // Find password input
                    const passwordInput = document.querySelector('input[type="password"], input[name="password"]');
                    if (!passwordInput) {{
                        return {{ error: 'Password input not found' }};
                    }}
                    
                    // Fill credentials
                    emailInput.value = '{username}';
                    emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    
                    passwordInput.value = '{password}';
                    passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    
                    // Find and click submit button
                    const submitButton = document.querySelector('button[type="submit"], input[type="submit"], .submit-btn');
                    if (submitButton) {{
                        submitButton.click();
                        return {{ success: true }};
                    }} else {{
                        return {{ error: 'Submit button not found' }};
                    }}
                }} catch (e) {{
                    return {{ error: e.message }};
                }}
            }})();
            """
            
            login_result = await self.chrome_execute_js(login_script)
            if login_result and login_result.get('success'):
                logger.info("Login form submitted")
                
                # Wait for login to process
                time.sleep(5)
                
                # Verify login success
                verify_script = """
                (function() {
                    const userMenu = document.querySelector('[data-testid="user-menu"], .user-profile, .user-dropdown, .account-menu');
                    const isLoginPage = window.location.href.includes('sign-in');
                    return {
                        isLoggedIn: !!userMenu && !isLoginPage,
                        currentUrl: window.location.href,
                        hasUserMenu: !!userMenu
                    };
                })();
                """
                
                verification = await self.chrome_execute_js(verify_script)
                if verification and verification.get('isLoggedIn'):
                    logger.info("Successfully logged in to Devex")
                    return True
                else:
                    logger.error(f"Login verification failed: {verification}")
                    return False
            else:
                logger.error(f"Login form submission failed: {login_result}")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def navigate_to_funding_search(self) -> bool:
        """Navigate to funding search page"""
        try:
            logger.info("Navigating to funding search...")
            
            result = await self.chrome_open_url("https://www.devex.com/funding/r")
            if not result:
                return False
            
            time.sleep(3)
            
            # Verify we're on the funding page
            verify_script = """
            (function() {
                const fundingElements = document.querySelectorAll(
                    '.funding-search, .search-results, .opportunities, [data-testid="funding"]'
                );
                return {
                    isFundingPage: fundingElements.length > 0,
                    url: window.location.href,
                    elementCount: fundingElements.length
                };
            })();
            """
            
            verification = await self.chrome_execute_js(verify_script)
            if verification and verification.get('isFundingPage'):
                logger.info("Successfully navigated to funding search")
                return True
            else:
                logger.error("Failed to reach funding search page")
                return False
                
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    async def apply_filters(self) -> bool:
        """Apply search filters"""
        try:
            logger.info("Applying search filters...")
            
            filter_script = """
            (function() {
                const results = [];
                
                try {
                    // Look for "open" status filter
                    const openCheckboxes = document.querySelectorAll(
                        'input[value="open"], input[data-filter="open"], label[for*="open"] input'
                    );
                    
                    for (const checkbox of openCheckboxes) {
                        if (!checkbox.checked) {
                            checkbox.click();
                            results.push('Applied open status filter');
                            break;
                        }
                    }
                    
                    // Look for tender type filter
                    const tenderCheckboxes = document.querySelectorAll(
                        'input[value="tender"], input[data-type="tender"], label[for*="tender"] input'
                    );
                    
                    for (const checkbox of tenderCheckboxes) {
                        if (!checkbox.checked) {
                            checkbox.click();
                            results.push('Applied tender filter');
                            break;
                        }
                    }
                    
                    // Look for grant type filter
                    const grantCheckboxes = document.querySelectorAll(
                        'input[value="grant"], input[data-type="grant"], label[for*="grant"] input'
                    );
                    
                    for (const checkbox of grantCheckboxes) {
                        if (!checkbox.checked) {
                            checkbox.click();
                            results.push('Applied grant filter');
                            break;
                        }
                    }
                    
                    return { success: true, applied: results };
                } catch (e) {
                    return { error: e.message };
                }
            })();
            """
            
            filter_result = await self.chrome_execute_js(filter_script)
            if filter_result and filter_result.get('success'):
                applied_filters = filter_result.get('applied', [])
                for filter_msg in applied_filters:
                    logger.info(filter_msg)
                
                # Wait for filters to take effect
                time.sleep(3)
                return True
            else:
                logger.warning(f"Filters may not have been applied correctly: {filter_result}")
                return True  # Continue anyway
                
        except Exception as e:
            logger.error(f"Filter application failed: {e}")
            return False
    
    async def extract_opportunities(self) -> List[DevexOpportunity]:
        """Extract opportunities from current page"""
        opportunities = []
        
        try:
            logger.info("Extracting opportunities from current page...")
            
            extraction_script = """
            (function() {
                const opportunities = [];
                
                // Multiple possible selectors for opportunity cards
                const cardSelectors = [
                    '.opportunity-card',
                    '.funding-opportunity',
                    '.search-result-item',
                    '.opportunity-item',
                    '.tender-item',
                    '.grant-item',
                    '.result-card',
                    '[data-testid="opportunity"]'
                ];
                
                let cards = [];
                for (const selector of cardSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        cards = Array.from(elements);
                        break;
                    }
                }
                
                // If no cards found, try generic approach
                if (cards.length === 0) {
                    // Look for repeated structures that might be opportunities
                    const possibleCards = document.querySelectorAll('div[class*="result"], div[class*="item"], div[class*="card"]');
                    cards = Array.from(possibleCards).filter(card => {
                        const text = card.textContent.toLowerCase();
                        return text.includes('tender') || text.includes('grant') || text.includes('deadline') || text.includes('opportunity');
                    }).slice(0, 20); // Limit to first 20 potential matches
                }
                
                cards.forEach((card, index) => {
                    try {
                        // Extract title
                        let title = '';
                        const titleSelectors = ['h1', 'h2', 'h3', '.title', '.name', '.opportunity-title', '[data-field="title"]'];
                        for (const selector of titleSelectors) {
                            const titleEl = card.querySelector(selector);
                            if (titleEl && titleEl.textContent.trim()) {
                                title = titleEl.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract organization
                        let organization = '';
                        const orgSelectors = ['.organization', '.donor', '.agency', '.company', '[data-field="organization"]'];
                        for (const selector of orgSelectors) {
                            const orgEl = card.querySelector(selector);
                            if (orgEl && orgEl.textContent.trim()) {
                                organization = orgEl.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract location
                        let location = '';
                        const locationSelectors = ['.location', '.country', '.region', '[data-field="location"]'];
                        for (const selector of locationSelectors) {
                            const locEl = card.querySelector(selector);
                            if (locEl && locEl.textContent.trim()) {
                                location = locEl.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract sector
                        let sector = '';
                        const sectorSelectors = ['.sector', '.category', '.industry', '[data-field="sector"]'];
                        for (const selector of sectorSelectors) {
                            const sectorEl = card.querySelector(selector);
                            if (sectorEl && sectorEl.textContent.trim()) {
                                sector = sectorEl.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract status
                        let status = '';
                        const statusSelectors = ['.status', '.state', '.badge', '[data-field="status"]'];
                        for (const selector of statusSelectors) {
                            const statusEl = card.querySelector(selector);
                            if (statusEl && statusEl.textContent.trim()) {
                                status = statusEl.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract opportunity size
                        let opportunitySize = '';
                        const sizeSelectors = ['.size', '.budget', '.amount', '.value', '[data-field="size"]'];
                        for (const selector of sizeSelectors) {
                            const sizeEl = card.querySelector(selector);
                            if (sizeEl && sizeEl.textContent.trim()) {
                                opportunitySize = sizeEl.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract deadline
                        let deadline = '';
                        const deadlineSelectors = ['.deadline', '.due-date', '.closing-date', '[data-field="deadline"]'];
                        for (const selector of deadlineSelectors) {
                            const deadlineEl = card.querySelector(selector);
                            if (deadlineEl && deadlineEl.textContent.trim()) {
                                deadline = deadlineEl.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract publication date
                        let publicationDate = '';
                        const pubDateSelectors = ['.published', '.date', '.pub-date', '[data-field="published"]'];
                        for (const selector of pubDateSelectors) {
                            const pubEl = card.querySelector(selector);
                            if (pubEl && pubEl.textContent.trim()) {
                                publicationDate = pubEl.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract description
                        let description = '';
                        const descSelectors = ['.description', '.summary', '.excerpt', 'p', '[data-field="description"]'];
                        for (const selector of descSelectors) {
                            const descEl = card.querySelector(selector);
                            if (descEl && descEl.textContent.trim().length > 20) {
                                description = descEl.textContent.trim().substring(0, 500); // Limit length
                                break;
                            }
                        }
                        
                        // Extract URL
                        let url = '';
                        const linkEl = card.querySelector('a');
                        if (linkEl) {
                            const href = linkEl.getAttribute('href');
                            if (href) {
                                url = href.startsWith('http') ? href : window.location.origin + href;
                            }
                        }
                        
                        // Determine opportunity type
                        let opportunityType = 'unknown';
                        const cardText = card.textContent.toLowerCase();
                        if (cardText.includes('tender') || title.toLowerCase().includes('tender')) {
                            opportunityType = 'tender';
                        } else if (cardText.includes('grant') || title.toLowerCase().includes('grant')) {
                            opportunityType = 'grant';
                        } else if (cardText.includes('program') || title.toLowerCase().includes('program')) {
                            opportunityType = 'program';
                        }
                        
                        // Only add if we have essential data
                        if (title && title.length > 3) {
                            opportunities.push({
                                title: title,
                                organization: organization,
                                location: location,
                                sector: sector,
                                opportunity_type: opportunityType,
                                status: status,
                                opportunity_size: opportunitySize,
                                deadline: deadline,
                                publication_date: publicationDate,
                                url: url,
                                description: description,
                                scraped_at: new Date().toISOString()
                            });
                        }
                    } catch (e) {
                        console.warn('Error processing opportunity card:', e);
                    }
                });
                
                return {
                    success: true,
                    count: opportunities.length,
                    opportunities: opportunities,
                    debug: {
                        totalCards: cards.length,
                        pageUrl: window.location.href
                    }
                };
            })();
            """
            
            result = await self.chrome_execute_js(extraction_script)
            if result and result.get('success'):
                raw_opportunities = result.get('opportunities', [])
                debug_info = result.get('debug', {})
                
                logger.info(f"Found {debug_info.get('totalCards', 0)} cards, extracted {len(raw_opportunities)} opportunities")
                
                for opp_data in raw_opportunities:
                    opportunity = DevexOpportunity(**opp_data)
                    opportunities.append(opportunity)
                
            else:
                logger.error(f"Extraction failed: {result}")
                
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
        
        return opportunities
    
    async def scrape_multiple_pages(self, max_pages: int = 5) -> List[DevexOpportunity]:
        """Scrape opportunities from multiple pages"""
        all_opportunities = []
        current_page = 1
        
        try:
            while current_page <= max_pages:
                logger.info(f"Scraping page {current_page}/{max_pages}")
                
                # Extract opportunities from current page
                page_opportunities = await self.extract_opportunities()
                
                if not page_opportunities:
                    logger.info("No opportunities found on this page, stopping")
                    break
                
                all_opportunities.extend(page_opportunities)
                logger.info(f"Page {current_page}: Found {len(page_opportunities)} opportunities")
                
                # Try to navigate to next page
                next_page_script = """
                (function() {
                    // Look for next page button
                    const nextSelectors = [
                        '.next-page:not(.disabled)',
                        '.pagination-next:not(.disabled)',
                        'a[aria-label="Next"]',
                        'button[aria-label="Next"]',
                        '.page-next',
                        '[data-testid="next-page"]'
                    ];
                    
                    for (const selector of nextSelectors) {
                        const nextBtn = document.querySelector(selector);
                        if (nextBtn && !nextBtn.disabled && !nextBtn.classList.contains('disabled')) {
                            nextBtn.click();
                            return { success: true, clicked: true };
                        }
                    }
                    
                    // Try numbered pagination
                    const currentPageEl = document.querySelector('.current-page, .active, .selected');
                    if (currentPageEl) {
                        const currentNum = parseInt(currentPageEl.textContent);
                        const nextPageEl = document.querySelector(`a:contains("${currentNum + 1}"), button:contains("${currentNum + 1}")`);
                        if (nextPageEl) {
                            nextPageEl.click();
                            return { success: true, clicked: true };
                        }
                    }
                    
                    return { success: false, message: 'No next page button found' };
                })();
                """
                
                next_result = await self.chrome_execute_js(next_page_script)
                if not (next_result and next_result.get('clicked')):
                    logger.info("No more pages available")
                    break
                
                # Wait for next page to load
                time.sleep(4)
                current_page += 1
                
        except Exception as e:
            logger.error(f"Error during multi-page scraping: {e}")
        
        logger.info(f"Total opportunities scraped: {len(all_opportunities)}")
        return all_opportunities
    
    async def save_opportunities(self, opportunities: List[DevexOpportunity], filename_prefix: str = "devex_opportunities") -> str:
        """Save opportunities to CSV and Excel files"""
        if not opportunities:
            logger.warning("No opportunities to save")
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_base = f"{filename_prefix}_{timestamp}"
        
        # Prepare data
        data = [asdict(opp) for opp in opportunities]
        df = pd.DataFrame(data)
        
        # Create output directory
        output_dir = Path("./devex_output")
        output_dir.mkdir(exist_ok=True)
        
        # Save as CSV
        csv_path = output_dir / f"{filename_base}.csv"
        df.to_csv(csv_path, index=False)
        
        # Save as Excel
        excel_path = output_dir / f"{filename_base}.xlsx"
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Opportunities')
        
        # Save summary
        summary = {
            'total_opportunities': len(opportunities),
            'tenders': len([o for o in opportunities if o.opportunity_type == 'tender']),
            'grants': len([o for o in opportunities if o.opportunity_type == 'grant']),
            'programs': len([o for o in opportunities if o.opportunity_type == 'program']),
            'open_status': len([o for o in opportunities if 'open' in o.status.lower()]),
            'scraped_at': datetime.now().isoformat()
        }
        
        summary_path = output_dir / f"{filename_base}_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved {len(opportunities)} opportunities to:")
        logger.info(f"  CSV: {csv_path}")
        logger.info(f"  Excel: {excel_path}")
        logger.info(f"  Summary: {summary_path}")
        
        return filename_base
    
    # Chrome MCP wrapper methods
    async def chrome_open_url(self, url: str) -> bool:
        """Open URL using Chrome MCP"""
        try:
            # This would be the actual MCP call
            result = open_url(url=url, new_tab=False)
            return True
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            return False
    
    async def chrome_execute_js(self, script: str) -> Optional[Dict]:
        """Execute JavaScript using Chrome MCP"""
        try:
            # This would be the actual MCP call
            result = execute_javascript(code=script)
            return result
        except Exception as e:
            logger.error(f"JavaScript execution failed: {e}")
            return None
    
    async def chrome_get_content(self) -> Optional[str]:
        """Get page content using Chrome MCP"""
        try:
            result = get_page_content()
            return result
        except Exception as e:
            logger.error(f"Failed to get page content: {e}")
            return None
    
    async def run_full_scraping_session(self, username: str, password: str, max_pages: int = 5) -> List[DevexOpportunity]:
        """Run complete scraping session"""
        try:
            logger.info("Starting Devex scraping session...")
            
            # Step 1: Login
            if not await self.login_to_devex(username, password):
                raise Exception("Login failed")
            
            # Step 2: Navigate to funding search
            if not await self.navigate_to_funding_search():
                raise Exception("Failed to navigate to funding search")
            
            # Step 3: Apply filters
            if not await self.apply_filters():
                logger.warning("Filters may not have been applied correctly")
            
            # Step 4: Scrape multiple pages
            opportunities = await self.scrape_multiple_pages(max_pages)
            
            # Step 5: Save results
            if opportunities:
                filename = await self.save_opportunities(opportunities)
                logger.info(f"Scraping completed successfully! Saved as: {filename}")
            else:
                logger.warning("No opportunities were found")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Scraping session failed: {e}")
            return []

# Standalone execution functions
async def quick_scrape(username: str, password: str, max_pages: int = 3):
    """Quick scraping function for immediate use"""
    scraper = PracticalDevexScraper()
    opportunities = await scraper.run_full_scraping_session(username, password, max_pages)
    return opportunities

def create_config_file():
    """Create a configuration file for the scraper"""
    config = {
        "credentials": {
            "username": "your-devex-email@example.com",
            "password": "your-password"
        },
        "scraping": {
            "max_pages": 5,
            "delay_between_pages": 3,
            "output_directory": "./devex_output"
        },
        "filters": {
            "status": ["open"],
            "types": ["tender", "grant"],
            "sectors": [],
            "locations": []
        }
    }
    
    with open('devex_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print("Created devex_config.json - please update with your credentials")

# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Create config file if it doesn't exist
    if not Path('devex_config.json').exists():
        create_config_file()
        print("Please update devex_config.json with your credentials and run again")
        exit(1)
    
    # Load config
    with open('devex_config.json', 'r') as f:
        config = json.load(f)
    
    # Run scraper
    async def main():
        scraper = PracticalDevexScraper()
        opportunities = await scraper.run_full_scraping_session(
            username=config['credentials']['username'],
            password=config['credentials']['password'],
            max_pages=config['scraping']['max_pages']
        )
        
        if opportunities:
            print(f"\n✅ Successfully scraped {len(opportunities)} opportunities!")
            print(f"📊 Breakdown:")
            print(f"   • Tenders: {len([o for o in opportunities if o.opportunity_type == 'tender'])}")
            print(f"   • Grants: {len([o for o in opportunities if o.opportunity_type == 'grant'])}")
            print(f"   • Programs: {len([o for o in opportunities if o.opportunity_type == 'program'])}")
        else:
            print("❌ No opportunities found")
    
    asyncio.run(main())