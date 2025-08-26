"""
UNGM advanced scraper using Playwright MCP integration.
Automates procurement opportunity extraction for media-related keywords.
"""

import sys
import os
from datetime import datetime
from loguru import logger
from .base_advanced_scraper import BaseAdvancedScraper

class UNGMAdvancedScraper(BaseAdvancedScraper):
    """
    Scraper for UNGM procurement opportunities using Playwright MCP.
    """
    def _scrape_with_mcp(self):
        from playwright.sync_api import sync_playwright
        opportunities = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.playwright_config['headless'])
                context = browser.new_context(
                    viewport=self.playwright_config['viewport'],
                    user_agent=self.playwright_config['user_agent']
                )
                page = context.new_page()
                page.goto(self.website_config['url'], wait_until=self.playwright_config['wait_for_load_state'])
                page.wait_for_timeout(2000)

                    # Set Published between: 3 days before today, only if input visible

                try:
                    from datetime import datetime, timedelta
                    published_date = (datetime.now() - timedelta(days=3)).strftime('%d-%b-%Y')
                    published_input = page.locator('input[name*="Published"], input[placeholder*="Published"], input[aria-label*="Published"], input[id*="Published"]').first
                    if published_input.is_visible():
                        published_input.fill(published_date)
                except Exception as e:
                    logger.warning(f"Published date input not found or invisible: {e}")

                try:
                    deadline_date = (datetime.now() + timedelta(days=3)).strftime('%d-%b-%Y')
                    deadline_input = page.locator('input[name*="Deadline"], input[placeholder*="Deadline"], input[aria-label*="Deadline"], input[id*="Deadline"]').first
                    if deadline_input.is_visible():
                        deadline_input.fill(deadline_date)
                except Exception as e:
                    logger.warning(f"Deadline date input not found or invisible: {e}")

                    # Check opportunity type boxes
                types = [
                    'Req for Proposal', 'Req for Quotation', 'Invitation to Bid',
                    'Grant Support', 'Pre Bid Notice'
                ]
                for t in types:
                    try:
                        cb = page.locator(f'input[type="checkbox"]:near(text("{t}"))').first
                        if cb.is_visible() and not cb.is_checked():
                            cb.check()
                    except Exception as e:
                        logger.warning(f"Checkbox {t} not found: {e}")

                # Click Search button
                try:
                    search_btn = page.locator('button:has-text("Search")').first
                    if search_btn.is_visible():
                        search_btn.click()
                        page.wait_for_timeout(3000)
                except Exception as e:
                    logger.warning(f"Search button not found: {e}")

                # Extract results matching keywords
                keyword_pattern = '|'.join(self.keywords)
                items = page.locator('tr, li, div[class*="opportunity"], article').all()
                for item in items:
                    try:
                        title_elem = item.locator('a, h2, h3, h4').first
                        if title_elem.is_visible():
                            title = title_elem.text_content().strip()
                            if any(k.lower() in title.lower() for k in self.keywords):
                                # Click to open details
                                title_elem.click()
                                page.wait_for_timeout(2000)
                                detail_url = page.url
                                details = self._extract_detailed_info(page, detail_url)
                                details['title'] = title
                                details['organization'] = self.website_config.get('name', 'UNGM')
                                details['detail_url'] = detail_url
                                details['extraction_date'] = datetime.now().isoformat()

                                # Extract beneficiary country if available
                                details['beneficiary_country'] = details.get('location', '')

                                # Extract published_on and deadline_on
                                details['published_on'] = details.get('published_date', '')
                                details['deadline_on'] = details.get('deadline', '')

                                # Extract reference
                                details['reference'] = details.get('reference_number', '')

                                # Export all tab data into detailed_description
                                tab_names = ['Documents', 'Contacts', 'Sustainability', 'Links', 'UNSPSC codes']
                                tab_data = []
                                for tab in tab_names:
                                    try:
                                        tab_elem = page.locator(f'button:has-text("{tab}")').first
                                        if tab_elem.is_visible():
                                            tab_elem.click()
                                            page.wait_for_timeout(1000)
                                            tab_content = page.locator('div[role="tabpanel"], section').first
                                            if tab_content.is_visible():
                                                tab_data.append(f"{tab}: {tab_content.text_content().strip()}")
                                    except Exception as e:
                                        logger.warning(f"Tab {tab} not found: {e}")
                                details['detailed_description'] = details.get('detailed_description', '') + '\n' + '\n'.join(tab_data)

                                # Download project documentation if document links are present
                                doc_links = details.get('document_links', [])
                                reference = details.get('reference', 'ungm_opportunity')
                                doc_folder = os.path.join('output', 'ungm_docs', reference)
                                if doc_links:
                                    os.makedirs(doc_folder, exist_ok=True)
                                    for doc_url in doc_links:
                                        try:
                                            import requests
                                            file_name = doc_url.split('/')[-1].split('?')[0]
                                            file_path = os.path.join(doc_folder, file_name)
                                            response = requests.get(doc_url, timeout=30)
                                            if response.status_code == 200:
                                                with open(file_path, 'wb') as f:
                                                    f.write(response.content)
                                                logger.info(f"Downloaded document: {file_name}")
                                            else:
                                                logger.warning(f"Failed to download {doc_url}: {response.status_code}")
                                        except Exception as e:
                                            logger.warning(f"Error downloading document {doc_url}: {e}")
                                details['document_links'] = [doc_folder]

                                # Ensure contact_email and submission_portal are present
                                details['contact_email'] = details.get('contact_email', '')
                                details['submission_portal'] = details.get('submission_portal', '')

                                # Only include if keyword found in title
                                if any(k.lower() in title.lower() for k in self.keywords):
                                    opportunities.append(details)
                                # Click through tabs: Documents, Contacts, Sustainability, Links, UNSPSC codes
                                tab_names = ['Documents', 'Contacts', 'Sustainability', 'Links', 'UNSPSC codes']
                                for tab in tab_names:
                                    try:
                                        tab_elem = page.locator(f'button:has-text("{tab}")').first
                                        if tab_elem.is_visible():
                                            tab_elem.click()
                                            page.wait_for_timeout(1000)
                                            # Extract tab info (simple text)
                                            tab_content = page.locator('div[role="tabpanel"], section').first
                                            if tab_content.is_visible():
                                                details[tab.lower().replace(' ', '_')] = tab_content.text_content().strip()
                                    except Exception as e:
                                        logger.warning(f"Tab {tab} not found: {e}")
                                # Go back to main list
                                page.go_back()
                                page.wait_for_timeout(1000)
                    except Exception as e:
                        logger.warning(f"Error processing item: {e}")
                        continue
                browser.close()
        except Exception as e:
            logger.error(f"UNGM Playwright scraping failed: {e}")
        return opportunities
