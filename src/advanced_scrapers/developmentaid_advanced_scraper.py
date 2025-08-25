"""
Advanced Playwright-based scraper for DevelopmentAid tenders with test automation structure
"""

import asyncio
import pytest
from playwright.async_api import async_playwright
import datetime
import json
import logging

# Dynamically set postedFrom to 3 days ago
three_days_ago = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d')
SEARCH_URL = f"https://www.developmentaid.org/tenders/search?hiddenAdvancedFilters=0&sort=relevance.desc&locations=181,171,170,165,172,173,168,174,161,160,158,157,155,153,152,151,150,149,147,148,146,145,143,140,139,138,137,6,8,4,9,7,3,178,184&statuses=10,2,3&eligibilityAlias=organisation&postedFrom={three_days_ago}&languages=92,101,253&searchedText=video%20or%20photo%20or%20film%20or%20multimedia%20or%20visual%20or%20documentary%20or%20podcasts%20or%20virtual%20event%20or%20media%20or%20animation%20or%20promotion%20or%20communication%20or%20audiovisual%20&searchedFields=title"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("developmentaid_scraper")

async def extract_tender_details(page, tender_title):
    logger.info(f"Extracting details for: {tender_title}")
    await page.click(f'text={tender_title}')
    await page.wait_for_selector('h1', timeout=10000)
    details = {
        "title": await page.text_content('h1'),
        "location": await page.text_content('text=Location: >> xpath=../following-sibling::*[1]'),
        "category": await page.text_content('text=Category: >> xpath=../following-sibling::*[1]'),
        "status": await page.text_content('text=Status: >> xpath=../following-sibling::*[1]'),
        "contracting_authority": await page.text_content('text=Contracting authority: >> xpath=../following-sibling::*[1]'),
        "funding_agency": await page.text_content('text=Funding Agency: >> xpath=../following-sibling::*[1]'),
        "budget": await page.text_content('text=Budget: >> xpath=../following-sibling::*[1]'),
        "date_posted": await page.text_content('text=Date posted: >> xpath=../following-sibling::*[1]'),
        "description": await page.text_content('text=Description >> xpath=../following-sibling::*[1]')
    }
    await page.go_back()
    await page.wait_for_selector('h1', timeout=10000)
    logger.info(f"Extracted: {details}")
    return details

@pytest.mark.asyncio
async def test_extraction_and_output():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(SEARCH_URL)
        await page.wait_for_selector('h1', timeout=10000)
        # Extract all tender titles on the first page
        titles = await page.locator('h1, h2, h3').all_text_contents()
        assert titles, "No tender titles found on the page."
        results = []
        # Extract details for each tender and validate
        for tender_title in titles:
            # Skip UNDP and UNGM tenders to avoid duplicates
            if any(skip in tender_title.lower() for skip in ["undp", "ungm"]):
                logger.info(f"Skipping duplicate tender: {tender_title}")
                continue
            details = await extract_tender_details(page, tender_title)
            assert details["title"], "Tender title missing."
            assert details["location"], "Location missing."
            assert details["category"], "Category missing."
            assert details["funding_agency"], "Funder missing."
            assert details["description"], "Description missing."
            # Format for Devex
            devex_item = {
                "Devex Project": details["title"],
                "funder": details["funding_agency"],
                "location": details["location"],
                "category": details["category"],
                "timeline": {
                    "deadline": details["date_posted"],
                    "posted": details["date_posted"]
                },
                "description": details["description"],
                "resources": [details["contracting_authority"], details["budget"]] # Add more links if available
            }
            results.append(devex_item)
        # Save results to JSON file
        with open("developmentaid_devex_format.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(results)} tenders to developmentaid_devex_format.json")
        await browser.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_extraction_and_output())
