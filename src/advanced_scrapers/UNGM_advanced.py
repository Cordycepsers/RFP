"""
UNGM Advanced Scraper using Playwright MCP Server
"""

from playwright.sync_api import sync_playwright
import json

# Constants
UNGM_URL = "https://www.ungm.org/Public/Notice"
OUTPUT_FILE = "output/ungm_opportunities.json"


def scrape_ungm():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(UNGM_URL)
        page.wait_for_selector("#notice-list")
        notices = page.query_selector_all(".notice-list-item")
        results = []
        for notice in notices:
            title = notice.query_selector(".notice-title").inner_text() if notice.query_selector(".notice-title") else ""
            ref = notice.query_selector(".notice-reference").inner_text() if notice.query_selector(".notice-reference") else ""
            deadline = notice.query_selector(".notice-deadline").inner_text() if notice.query_selector(".notice-deadline") else ""
            link = notice.query_selector("a").get_attribute("href") if notice.query_selector("a") else ""
            results.append({
                "title": title,
                "reference": ref,
                "deadline": deadline,
                "link": link
            })
        browser.close()
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Scraped {len(results)} opportunities from UNGM.")

if __name__ == "__main__":
    scrape_ungm()
