"""
Playwright-based test script for DevelopmentAid tenders extraction
"""

import asyncio
from playwright.async_api import async_playwright

SEARCH_URL = "https://www.developmentaid.org/tenders/search?hiddenAdvancedFilters=0&sort=relevance.desc&statuses=2,3,5&eligibilityAlias=organisation&postedFrom=2025-08-18&languages=92,101,253&searchedText=multimedia"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(SEARCH_URL)
        await page.wait_for_selector('text=Organisation of Corporate events', timeout=10000)
        # Click on the first tender
        await page.click('text=Organisation of Corporate events')
        await page.wait_for_selector('h1', timeout=10000)
        # Extract details
        title = await page.text_content('h1')
        location = await page.text_content('text=Location: >> xpath=../following-sibling::*[1]')
        category = await page.text_content('text=Category: >> xpath=../following-sibling::*[1]')
        status = await page.text_content('text=Status: >> xpath=../following-sibling::*[1]')
        sectors = await page.text_content('text=Sectors: >> xpath=../following-sibling::*[1]')
        languages = await page.text_content('text=Languages: >> xpath=../following-sibling::*[1]')
        contracting_authority = await page.text_content('text=Contracting authority: >> xpath=../following-sibling::*[1]')
        funding_agency = await page.text_content('text=Funding Agency: >> xpath=../following-sibling::*[1]')
        eligibility = await page.text_content('text=Eligibility: >> xpath=../following-sibling::*[1]')
        budget = await page.text_content('text=Budget: >> xpath=../following-sibling::*[1]')
        date_posted = await page.text_content('text=Date posted: >> xpath=../following-sibling::*[1]')
        description = await page.text_content('text=Description >> xpath=../following-sibling::*[1]')
        print({
            "title": title,
            "location": location,
            "category": category,
            "status": status,
            "sectors": sectors,
            "languages": languages,
            "contracting_authority": contracting_authority,
            "funding_agency": funding_agency,
            "eligibility": eligibility,
            "budget": budget,
            "date_posted": date_posted,
            "description": description
        })
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
