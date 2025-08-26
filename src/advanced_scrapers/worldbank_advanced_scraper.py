"""
World Bank advanced scraper using Playwright MCP integration.
Automates procurement opportunity extraction for unified export.
"""

import sys
import os
from datetime import datetime
from loguru import logger
from .base_advanced_scraper import BaseAdvancedScraper

class WorldBankAdvancedScraper(BaseAdvancedScraper):
    """
    Scraper for World Bank procurement opportunities using Playwright MCP.
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
                page.goto('https://projects.worldbank.org/en/projects-operations/procurement?srce=both', wait_until=self.playwright_config['wait_for_load_state'])
                page.wait_for_timeout(2000)

                # Use keywords from config, fallback to default
                keywords = getattr(self, 'keywords', [
                    "video", "photo", "film", "multimedia", "design", "visual",
                    "campaign", "podcasts", "virtual event", "media", "animation", 
                    "animated video", "promotion", "communication", "audiovisual"
                ])
                rows = page.locator('table tr, .procurement-listing tr, .project-listing tr, li, article').all()
                for row in rows:
                    try:
                        title_elem = row.locator('a, h2, h3, h4').first
                        if title_elem.is_visible():
                            title = title_elem.text_content().strip()
                            # Check for open status in row (exclude Contract Award)
                            status_elem = row.locator('td, span, div').first
                            status_text = status_elem.text_content().strip() if status_elem and status_elem.is_visible() else ""
                            open_statuses = ["Invitation for Bids", "Open", "Forecast", "Request for Proposal", "Request for Quotation"]
                            is_open = any(s in status_text for s in open_statuses) and "Contract Award" not in status_text
                            if any(k.lower() in title.lower() for k in keywords) and is_open:
                                title_elem.click()
                                page.wait_for_timeout(2000)
                                detail_url = page.url
                                details = self._extract_detailed_info(page, detail_url)
                                details['title'] = title
                                details['organization'] = 'World Bank'
                                details['detail_url'] = detail_url
                                details['extraction_date'] = datetime.now().isoformat()
                                details['beneficiary_country'] = details.get('location', '')
                                details['published_on'] = details.get('published_date', '')
                                details['deadline_on'] = details.get('deadline', '')
                                details['reference'] = details.get('reference_number', '')
                                details['contact_email'] = details.get('contact_email', '')
                                details['submission_portal'] = details.get('submission_portal', '')
                                details['document_links'] = details.get('document_links', [])
                                details['detailed_description'] = details.get('detailed_description', '')
                                opportunities.append(details)
                                page.go_back()
                                page.wait_for_timeout(1000)
                    except Exception as e:
                        logger.warning(f"Error processing row: {e}")
                        continue
                browser.close()
        except Exception as e:
            logger.error(f"World Bank Playwright scraping failed: {e}")
        return opportunities
